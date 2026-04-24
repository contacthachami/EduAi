"""Test rapide quiz + Q&A (le résumé a déjà été validé)."""
import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from backend.database.mongodb import connect_db, get_chunks_by_course, close_db
from backend.services.llm_quiz import generate_quiz_llm
from backend.services.llm_qa import answer_with_llm

COURSE_ID = "69e8ddf9850f24f14a5895d5"  # CNN


async def main():
    await connect_db()
    chunks = await get_chunks_by_course(COURSE_ID)
    print(f"Cours chargé : {len(chunks)} chunks")

    # ── 1. Quiz LLM (3 questions, un seul appel) ──
    print("\n" + "═" * 70)
    print(" QUIZ — 3 QCM via LLM (un seul appel)")
    print("═" * 70)
    t0 = time.time()
    quiz = await generate_quiz_llm(chunks, num_questions=3)
    dt = time.time() - t0
    if quiz:
        print(f"  ✓ {len(quiz)} questions générées en {dt:.1f}s\n")
        for q in quiz:
            print(f"  Q{q['id']}. {q['question']}")
            for i, opt in enumerate(q['options']):
                marker = "✓" if i == q['correct_index'] else " "
                print(f"      {marker} [{chr(65+i)}] {opt}")
            print(f"      💡 {q['explanation']}\n")
    else:
        print(f"  ✗ Quiz LLM échoué ({dt:.1f}s)")

    # ── 2. Q&A RAG ──
    print("\n" + "═" * 70)
    print(" Q&A — RAG via LLM")
    print("═" * 70)
    question = "Qu'est-ce qu'une couche de convolution ?"
    print(f"  ❓ {question}")
    contexts = sorted(chunks, key=lambda c: len(c.get("text", "")), reverse=True)[:5]
    contexts = [{"text": c["text"], "page": c["page"], "chapter": c.get("chapter", ""), "score": 0.8} for c in contexts]
    t0 = time.time()
    answer = await answer_with_llm(question, contexts)
    dt = time.time() - t0
    if answer:
        print(f"\n  ✓ Réponse en {dt:.1f}s :\n")
        print("  " + answer.replace("\n", "\n  "))
    else:
        print(f"  ✗ Q&A LLM échoué ({dt:.1f}s)")

    await close_db()
    print("\n✓ TESTS TERMINÉS")


if __name__ == "__main__":
    asyncio.run(main())
