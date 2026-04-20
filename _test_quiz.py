"""Quick quiz-only test."""
import requests
import json
import time
import random

BASE = "http://127.0.0.1:8000/api"
CID = "69e6314a6ba4f898782d1ff4"

print("=== TEST QUIZ (5 questions) ===")
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
        if len(options) != 4:
            issues.append(f"  Q{i+1}: WRONG OPTION COUNT ({len(options)})")
        if correct_idx < 0 or correct_idx >= len(options):
            issues.append(f"  Q{i+1}: INVALID correct_index={correct_idx}")
        if len(qtext) < 10:
            issues.append(f"  Q{i+1}: QUESTION TOO SHORT ({len(qtext)} chars)")
        # Check duplicates
        lower_opts = [o.lower().strip() for o in options]
        if len(set(lower_opts)) != len(lower_opts):
            issues.append(f"  Q{i+1}: DUPLICATE OPTIONS")
        # Check question mark
        if not qtext.strip().endswith("?"):
            issues.append(f"  Q{i+1}: NO QUESTION MARK")
    if issues:
        print(f"ISSUES FOUND ({len(issues)}):")
        for iss in issues:
            print(iss)
    else:
        print("No structural issues in quiz data.")
    # Show all questions
    for i, q in enumerate(questions):
        print(f"\n  Q{i+1}: {q['question']}")
        for j, opt in enumerate(q['options']):
            marker = " *" if j == q['correct_index'] else ""
            print(f"    {chr(65+j)}. {opt}{marker}")

    # Test submit
    print("\n=== TEST QUIZ SUBMIT ===")
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
            print(f"  Detail keys: {list(details[0].keys())}")
    else:
        print(f"ERROR: {r2.text[:300]}")
else:
    print(f"ERROR: {r.text[:500]}")
