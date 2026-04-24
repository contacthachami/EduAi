"""Smoke test du LLM Ollama : ping + 1 chat court chronométré."""
import asyncio
import time

from backend.services.llm_client import get_client


async def main():
    c = get_client()
    print("→ Health check…")
    t0 = time.time()
    ok = await c.is_available(force=True)
    print(f"  available={ok}  ({time.time()-t0:.2f}s)")
    if not ok:
        return

    print("→ Mini-chat (≤ 50 tokens)…")
    t0 = time.time()
    out = await c.chat(
        system="Tu es un assistant pédagogique français concis.",
        user="En une phrase, qu'est-ce qu'un réseau de neurones convolutif ?",
        temperature=0.2,
        max_tokens=80,
    )
    dt = time.time() - t0
    print(f"  ⏱ {dt:.1f}s  →  {out!r}")

    print("→ Mini-JSON…")
    t0 = time.time()
    data = await c.chat_json(
        system="Tu réponds en JSON strict.",
        user='Donne {"capital":"...","pays":"France"}.',
        temperature=0.0,
    )
    print(f"  ⏱ {time.time()-t0:.1f}s  →  {data}")


if __name__ == "__main__":
    asyncio.run(main())
