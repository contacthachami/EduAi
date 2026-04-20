"""Quick test script for summary + quiz endpoints."""
import requests
import json
import time

BASE = "http://127.0.0.1:8000/api"
CID = "69e6314a6ba4f898782d1ff4"

# ── Test Summary ──
print("=== TEST SUMMARY ===")
t0 = time.time()
r = requests.get(f"{BASE}/summary/{CID}", timeout=1800)
elapsed = time.time() - t0
print(f"Status: {r.status_code} ({elapsed:.1f}s)")

if r.status_code == 200:
    data = r.json()
    chapters = data.get("chapters", [])
    print(f"Chapters returned: {len(chapters)}")
    issues = []
    for i, ch in enumerate(chapters):
        title = ch.get("title", "?")
        summary = ch.get("summary", "")
        concepts = ch.get("key_concepts", [])
        pages = ch.get("pages", [])
        if not summary or summary.startswith("Résumé non disponible"):
            issues.append(f"  Ch {i+1} ({title}): NO SUMMARY")
        if len(summary) < 20:
            issues.append(f"  Ch {i+1} ({title}): TOO SHORT ({len(summary)} chars)")
        if not concepts:
            issues.append(f"  Ch {i+1} ({title}): NO KEY CONCEPTS")
        if not pages:
            issues.append(f"  Ch {i+1} ({title}): NO PAGES")
    if issues:
        print(f"ISSUES FOUND ({len(issues)}):")
        for iss in issues:
            print(iss)
    else:
        print("No obvious issues in summary data.")
    # Show samples
    for ch in chapters[:3]:
        print(f"  [{ch['title']}] => {ch['summary'][:120]}...")
        print(f"    concepts: {ch['key_concepts'][:5]}, pages: {ch['pages']}")
else:
    print(f"ERROR: {r.text[:300]}")

# ── Test Quiz ──
print("\n=== TEST QUIZ (5 questions) ===")
t0 = time.time()
r = requests.get(f"{BASE}/quiz/{CID}", params={"num_questions": 5}, timeout=300)
elapsed = time.time() - t0
print(f"Status: {r.status_code} ({elapsed:.1f}s)")

if r.status_code == 200:
    data = r.json()
    quiz_id = data.get("quiz_id", "")
    questions = data.get("questions", [])
    print(f"Quiz ID: {quiz_id}")
    print(f"Questions returned: {len(questions)}")
    issues = []
    for i, q in enumerate(questions):
        qtext = q.get("question", "")
        options = q.get("options", [])
        correct_idx = q.get("correct_index", -1)
        explanation = q.get("explanation", "")
        if len(options) != 4:
            issues.append(f"  Q{i+1}: WRONG OPTION COUNT ({len(options)})")
        if correct_idx < 0 or correct_idx >= len(options):
            issues.append(f"  Q{i+1}: INVALID correct_index={correct_idx}")
        if len(qtext) < 10:
            issues.append(f"  Q{i+1}: QUESTION TOO SHORT ({len(qtext)} chars)")
        # Check if options have duplicates
        if len(set(o.lower().strip() for o in options)) != len(options):
            issues.append(f"  Q{i+1}: DUPLICATE OPTIONS")
        # Check if correct answer is in options
        if correct_idx >= 0 and correct_idx < len(options):
            correct_answer = options[correct_idx]
            if not correct_answer or len(correct_answer.strip()) < 2:
                issues.append(f"  Q{i+1}: EMPTY/SHORT correct answer")
    if issues:
        print(f"ISSUES FOUND ({len(issues)}):")
        for iss in issues:
            print(iss)
    else:
        print("No obvious issues in quiz data.")
    # Show samples
    for q in questions[:3]:
        print(f"  Q: {q['question'][:100]}")
        print(f"    Options: {q['options']}")
        print(f"    Correct: index={q['correct_index']} => {q['options'][q['correct_index']]}")

    # ── Test Quiz Submit ──
    print("\n=== TEST QUIZ SUBMIT ===")
    # Submit with random answers
    import random
    answers = [random.randint(0, 3) for _ in questions]
    r2 = requests.post(f"{BASE}/quiz/submit", json={"quiz_id": quiz_id, "answers": answers}, timeout=30)
    print(f"Submit status: {r2.status_code}")
    if r2.status_code == 200:
        result = r2.json()
        print(f"Score: {result.get('score')}/{result.get('total')} ({result.get('percentage')}%)")
        print(f"Passed: {result.get('passed')}")
        details = result.get("details", [])
        print(f"Details count: {len(details)}")
        if details:
            d = details[0]
            print(f"  Detail keys: {list(d.keys())}")
    else:
        print(f"ERROR: {r2.text[:300]}")
else:
    print(f"ERROR: {r.text[:300]}")

print("\n=== ALL TESTS COMPLETE ===")
