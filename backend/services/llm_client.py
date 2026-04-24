"""Client asynchrone pour Ollama (LLM local).

Fournit:
- Health check (cache court pour ne pas spammer)
- Génération texte (chat) avec retries
- Génération JSON stricte (utilise format='json' d'Ollama)
- Streaming token par token (SSE)
- Détection automatique d'indisponibilité → permet le fallback extractif

Le client est volontairement minimaliste : pas d'agent, pas de tools, juste
un wrapper robuste autour de l'API HTTP Ollama.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncIterator, Optional

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)


class LLMUnavailable(RuntimeError):
    """Levée quand Ollama est injoignable ou que le modèle n'est pas chargé."""


class OllamaClient:
    """Client singleton pour Ollama. Thread/async-safe."""

    _instance: Optional["OllamaClient"] = None

    def __init__(self) -> None:
        s = get_settings()
        self.host = s.ollama_host.rstrip("/")
        self.model = s.ollama_model
        self.timeout = s.ollama_timeout_seconds
        self.num_ctx = s.ollama_num_ctx
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self._health_cache: tuple[float, bool] = (0.0, False)
        self._health_ttl = 30.0  # secondes

    @classmethod
    def get(cls) -> "OllamaClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def aclose(self) -> None:
        await self._client.aclose()

    # ── Health ──────────────────────────────────────────────────────

    async def is_available(self, force: bool = False) -> bool:
        """Vérifie qu'Ollama tourne ET que le modèle est dispo. Cache 30s."""
        ts, ok = self._health_cache
        if not force and (time.monotonic() - ts) < self._health_ttl:
            return ok
        ok = await self._check()
        self._health_cache = (time.monotonic(), ok)
        return ok

    async def _check(self) -> bool:
        try:
            r = await self._client.get(f"{self.host}/api/tags", timeout=5.0)
            r.raise_for_status()
            tags = r.json().get("models", []) or []
            names = {m.get("name", "").split(":")[0] for m in tags} | {m.get("name", "") for m in tags}
            base = self.model.split(":")[0]
            available = self.model in names or base in names
            if not available:
                logger.warning(
                    "Ollama joignable mais modèle '%s' absent (modèles présents: %s).",
                    self.model, [m.get("name") for m in tags],
                )
            return available
        except Exception as exc:
            logger.warning("Ollama indisponible: %s", exc)
            return False

    # ── Génération texte simple ─────────────────────────────────────

    async def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        retries: int = 1,
    ) -> str:
        """Appelle /api/chat et retourne le contenu textuel.

        Lève LLMUnavailable si Ollama est down ou que toutes les tentatives échouent.
        """
        if not await self.is_available():
            raise LLMUnavailable("Ollama non disponible (health check échoué).")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": self.num_ctx,
            },
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens
        if json_mode:
            payload["format"] = "json"

        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                t0 = time.monotonic()
                r = await self._client.post(f"{self.host}/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
                msg = (data.get("message") or {}).get("content", "")
                logger.info(
                    "Ollama chat OK: %.1fs done=%s eval=%s prompt_eval=%s len_out=%d",
                    time.monotonic() - t0,
                    data.get("done_reason"),
                    data.get("eval_count"),
                    data.get("prompt_eval_count"),
                    len(msg),
                )
                if not msg:
                    raise LLMUnavailable("Réponse Ollama vide.")
                return msg.strip()
            except (httpx.HTTPError, LLMUnavailable) as exc:
                last_exc = exc
                logger.warning("Ollama chat tentative %d/%d échouée: %s", attempt + 1, retries + 1, exc)
                if attempt < retries:
                    await asyncio.sleep(1.5 * (attempt + 1))
        # Ne marque indisponible que pour les vraies erreurs réseau / connexion,
        # pas pour les timeouts (le service tourne, juste lent).
        if isinstance(last_exc, (httpx.ConnectError, httpx.NetworkError)):
            self._health_cache = (time.monotonic(), False)
        raise LLMUnavailable(f"Ollama chat: toutes les tentatives ont échoué ({last_exc}).")

    async def chat_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        retries: int = 2,
    ) -> dict | list:
        """Comme chat() mais force JSON et parse la réponse. Tolère les blocs ```json."""
        raw = await self.chat(
            system=system,
            user=user,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
            retries=retries,
        )
        return _parse_json_loose(raw)

    # ── Streaming (pour le chat utilisateur) ────────────────────────

    async def chat_stream(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
    ) -> AsyncIterator[str]:
        """Stream token-by-token. Yield les fragments texte au fur et à mesure."""
        if not await self.is_available():
            raise LLMUnavailable("Ollama non disponible.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_ctx": self.num_ctx,
            },
        }
        try:
            async with self._client.stream("POST", f"{self.host}/api/chat", json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        evt = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    chunk = (evt.get("message") or {}).get("content", "")
                    if chunk:
                        yield chunk
                    if evt.get("done"):
                        break
        except httpx.HTTPError as exc:
            self._health_cache = (time.monotonic(), False)
            raise LLMUnavailable(f"Ollama stream: {exc}")


# ── Helpers ─────────────────────────────────────────────────────────

def _parse_json_loose(raw: str) -> dict | list:
    """Extrait le premier objet/tableau JSON d'une chaîne, tolère ```json …``` etc."""
    s = raw.strip()
    # Retire les fences ```json ou ```
    if s.startswith("```"):
        s = s.split("```", 2)[-1] if s.count("```") >= 2 else s.lstrip("`")
        # 'json\n{...}' éventuel
        if s.lstrip().lower().startswith("json"):
            s = s.lstrip()[4:]
        s = s.strip().rstrip("`").strip()
    # Tente parse direct
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # Fallback: trouve le premier { ou [ et le dernier matching
    for opener, closer in (("{", "}"), ("[", "]")):
        i = s.find(opener)
        j = s.rfind(closer)
        if i != -1 and j > i:
            try:
                return json.loads(s[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise LLMUnavailable(f"Impossible de parser le JSON Ollama: {raw[:200]!r}")


# ── Façade simple pour le code synchrone ───────────────────────────

class GroqClient:
    """Client Groq Cloud (API OpenAI-compatible).

    Expose la même surface que OllamaClient : is_available, chat, chat_json, chat_stream.
    Très rapide (~250-800 tok/s sur llama-3.3-70b-versatile), gratuit avec rate limits.
    """

    _instance: Optional["GroqClient"] = None

    def __init__(self) -> None:
        s = get_settings()
        self.api_key = s.groq_api_key.strip()
        self.model = s.groq_model
        self.base_url = s.groq_base_url.rstrip("/")
        self.timeout = s.groq_timeout_seconds
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            } if self.api_key else {"Content-Type": "application/json"},
        )
        self._health_cache: tuple[float, bool] = (0.0, False)
        self._health_ttl = 60.0

    @classmethod
    def get(cls) -> "GroqClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def aclose(self) -> None:
        await self._client.aclose()

    async def is_available(self, force: bool = False) -> bool:
        ts, ok = self._health_cache
        if not force and (time.monotonic() - ts) < self._health_ttl:
            return ok
        ok = bool(self.api_key)
        if not ok:
            logger.warning("Groq: GROQ_API_KEY absente dans la configuration.")
        self._health_cache = (time.monotonic(), ok)
        return ok

    async def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        retries: int = 1,
    ) -> str:
        if not await self.is_available():
            raise LLMUnavailable("Groq indisponible (clé API manquante).")

        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                t0 = time.monotonic()
                r = await self._client.post(f"{self.base_url}/chat/completions", json=payload)
                if r.status_code == 401:
                    raise LLMUnavailable("Groq: clé API invalide (401).")
                if r.status_code == 429:
                    # Rate limit : attendre un peu plus
                    logger.warning("Groq: rate limit (429), attente avant retry…")
                    await asyncio.sleep(3.0 * (attempt + 1))
                    raise httpx.HTTPError("rate limited")
                r.raise_for_status()
                data = r.json()
                choice = (data.get("choices") or [{}])[0]
                msg = (choice.get("message") or {}).get("content", "") or ""
                usage = data.get("usage") or {}
                logger.info(
                    "Groq chat OK: %.2fs model=%s in=%s out=%s len=%d",
                    time.monotonic() - t0,
                    data.get("model"),
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    len(msg),
                )
                if not msg:
                    raise LLMUnavailable("Réponse Groq vide.")
                return msg.strip()
            except (httpx.HTTPError, LLMUnavailable) as exc:
                last_exc = exc
                logger.warning("Groq chat tentative %d/%d échouée: %s", attempt + 1, retries + 1, exc)
                if attempt < retries:
                    await asyncio.sleep(1.5 * (attempt + 1))
        raise LLMUnavailable(f"Groq chat: toutes les tentatives ont échoué ({last_exc}).")

    async def chat_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        retries: int = 2,
    ) -> dict | list:
        raw = await self.chat(
            system=system,
            user=user,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
            retries=retries,
        )
        return _parse_json_loose(raw)

    async def chat_stream(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
    ) -> AsyncIterator[str]:
        if not await self.is_available():
            raise LLMUnavailable("Groq indisponible.")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "stream": True,
        }
        try:
            async with self._client.stream("POST", f"{self.base_url}/chat/completions", json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        evt = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    delta = ((evt.get("choices") or [{}])[0].get("delta") or {})
                    chunk = delta.get("content", "")
                    if chunk:
                        yield chunk
        except httpx.HTTPError as exc:
            raise LLMUnavailable(f"Groq stream: {exc}")


def get_client():
    """Retourne l'instance LLM active selon la configuration (groq | ollama)."""
    backend = (get_settings().llm_backend or "ollama").lower()
    if backend == "groq":
        return GroqClient.get()
    return OllamaClient.get()
