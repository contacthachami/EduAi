"""Test V3 — résumé narratif avec qwen2.5:7b sur 2 chapitres NLP."""
import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from backend.database.mongodb import connect_db, get_db, close_db
from backend.services.llm_summarizer import refine_chapter

COURSE_ID = "69ea7b701ef3690bb30a5191"  # NLP (cache v2 actuel)


async def main():
    await connect_db()
    db = get_db()
    # Lecture brute du cache (ignore version) pour récupérer les bullets extraits
    summary = await db.summaries.find_one({"course_id": COURSE_ID})
    if not summary:
        print("Aucun résumé trouvé pour ce cours.")
        return
    chapters = summary.get("chapters", [])
    print(f"Cours NLP : {len(chapters)} chapitres en cache")

    # On teste les chapitres 1 et 6 (ceux que l'utilisateur a montrés en screenshot)
    indices_to_test = [0, 5]

    for idx in indices_to_test:
        if idx >= len(chapters):
            continue
        ch = chapters[idx]
        title = ch.get("title", "")
        bullets = ch.get("summary", [])
        keys = ch.get("key_concepts", [])

        print("\n" + "═" * 78)
        print(f" CHAPITRE {idx+1} — Titre brut : {title!r}")
        print(f" Pages : {ch.get('pages')}")
        print(f" Nb bullets extraits : {len(bullets)}")
        print("═" * 78)

        t0 = time.time()
        # bullets peut être une liste (cache) ou une str ; refine_chapter attend un str
        bullets_str = "\n".join(bullets) if isinstance(bullets, list) else str(bullets)
        refined = await refine_chapter(title=title, bullets=bullets_str, key_concepts=keys, lang_hint="fr")
        dt = time.time() - t0

        if not refined:
            print(f"  ✗ refine_chapter retourné None en {dt:.1f}s")
            continue

        print(f"\n  ✓ Généré en {dt:.1f}s\n")
        print(f"  TITRE RAFFINÉ : {refined['title']!r}")
        print(f"  CONCEPTS-CLÉS : {refined['key_concepts']}\n")
        print("  --- CORPS ---")
        body = refined["body"]
        for line in body.split("\n"):
            print(f"  {line}")
        print("  --- FIN CORPS ---")

    await close_db()
    print("\n✓ TEST V3 TERMINÉ")


if __name__ == "__main__":
    asyncio.run(main())
