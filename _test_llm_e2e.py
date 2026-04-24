"""Test end-to-end des 3 services LLM sur un cours réel (CNN — le plus court)."""
import asyncio
import time
import json

from backend.database.mongodb import connect_db, get_chunks_by_course, close_db
from backend.services.summarizer import summarize_course
from backend.services.llm_summarizer import refine_chapter
from backend.services.llm_quiz import generate_quiz_llm
from backend.services.llm_qa import answer_with_llm

COURSE_ID = "69e8c235e3271cd53f38e76a"  # CNN


async def main():
    await connect_db()
    chunks = await get_chunks_by_course(COURSE_ID)
    print(f"Cours chargé : {len(chunks)} chunks")

    # ────────────────────────────────────────────────────────────
    # 1. Résumé extractif → raffinement LLM (1 seul chapitre)
    # ────────────────────────────────────────────────────────────
    print("\n" + "═" * 70)
    print(" 1. RÉSUMÉ — extractif puis raffinement LLM (1 chapitre)")
    print("═" * 70)
    summaries = summarize_course(chunks)
    print(f"  {len(summaries)} chapitres extractifs générés")
    target = summaries[0]
    print(f"\n  → Raffinement chapitre : '{target['title']}'")
    print(f"     Bullets extractifs ({len(target['summary'])} c.) — extrait :")
    print("     " + target['summary'][:200].replace("\n", "\n     ") + "…")

    t0 = time.time()
    fiche = await refine_chapter(
        title=target['title'],
        bullets=target['summary'],
        key_concepts=target.get('key_concepts', []) or [],
    )
    dt = time.time() - t0
    if fiche:
        print(f"\n  ✓ Fiche LLM générée ({dt:.1f}s, {len(fiche)} c.)")
        print("  ─── DÉBUT FICHE ───")
        print(fiche)
        print("  ─── FIN FICHE ───")
    else:
        print(f"  ✗ Fiche LLM échouée ({dt:.1f}s)")

    # ────────────────────────────────────────────────────────────
    # 2. Quiz LLM (3 questions seulement)
    # ────────────────────────────────────────────────────────────
    print("\n" + "═" * 70)
    print(" 2. QUIZ — 3 QCM via LLM")
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

    # ────────────────────────────────────────────────────────────
    # 3. Q&A RAG sur 1 question
    # ────────────────────────────────────────────────────────────
    print("\n" + "═" * 70)
    print(" 3. Q&A — RAG via LLM")
    print("═" * 70)
    question = "Qu'est-ce qu'une couche de convolution ?"
    print(f"  ❓ {question}")
    # Simuler une recherche FAISS simplifiée : prendre les 5 chunks les plus longs
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
    print("\n" + "═" * 70)
    print(" TESTS TERMINÉS")
    print("═" * 70)


if __name__ == "__main__":
    asyncio.run(main())
