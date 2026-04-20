"""Final comprehensive test for both Summary and Quiz features."""
import requests, time, json

COURSE_ID = "69e6314a6ba4f898782d1ff4"
BASE = "http://127.0.0.1:8000/api"

def test_summary():
    print("=" * 60)
    print("SUMMARY TEST")
    print("=" * 60)
    url = f"{BASE}/summary/{COURSE_ID}"
    t0 = time.time()
    r = requests.get(url, timeout=900)
    elapsed = time.time() - t0
    print(f"Status: {r.status_code} ({elapsed:.1f}s)")
    
    if r.status_code != 200:
        print(f"FAIL: {r.text[:300]}")
        return False
    
    data = r.json()
    chapters = data.get("chapters", [])
    print(f"Chapters: {len(chapters)}")
    
    issues = []
    for i, ch in enumerate(chapters, 1):
        title = ch["title"]
        summary = ch["summary"]
        concepts = ch.get("key_concepts", [])
        
        # Check for problems
        words = summary.lower().split()
        if len(words) >= 6:
            ratio = len(set(words)) / len(words)
            if ratio < 0.45:
                issues.append(f"  Ch {i} ({title}): REPETITIVE (ratio={ratio:.2f})")
        
        # Check for non-Latin chars
        import re
        non_latin = re.findall(r"[^\u0000-\u024F\u1E00-\u1EFF0-9\s.,;:!?'\"()\-\u2013\u2014/\u25CF\u25CB\u25AA\u25A0\u25B6\u2192\u2190]", summary)
        if non_latin:
            issues.append(f"  Ch {i} ({title}): NON-LATIN chars: {''.join(set(non_latin))}")
        
        # Check for truncated concepts
        bad_concepts = [c for c in concepts if c.endswith("Introduc") or len(c) > 50]
        if bad_concepts:
            issues.append(f"  Ch {i} ({title}): BAD CONCEPTS: {bad_concepts}")
    
    if issues:
        print(f"\nISSUES ({len(issues)}):")
        for issue in issues:
            print(issue)
    else:
        print("\nNo issues found!")
    
    # Show first 5
    print()
    for i, ch in enumerate(chapters[:5], 1):
        print(f"  Ch {i} [{ch['title']}]")
        print(f"    Summary: {ch['summary'][:120]}...")
        print(f"    Concepts: {ch.get('key_concepts', [])}")
    
    return len(issues) == 0

def test_quiz():
    print("\n" + "=" * 60)
    print("QUIZ TEST")
    print("=" * 60)
    
    # Generate quiz
    url = f"{BASE}/quiz/{COURSE_ID}"
    t0 = time.time()
    r = requests.get(url, timeout=120)
    elapsed = time.time() - t0
    print(f"GET Status: {r.status_code} ({elapsed:.1f}s)")
    
    if r.status_code != 200:
        print(f"FAIL: {r.text[:300]}")
        return False
    
    data = r.json()
    questions = data.get("questions", [])
    print(f"Questions: {len(questions)}")
    
    issues = []
    answers = {}
    for i, q in enumerate(questions, 1):
        qtext = q.get("question", "")
        options = q.get("options", [])
        correct = q.get("correct_index", -1)
        
        if not qtext.strip().endswith("?"):
            issues.append(f"  Q{i}: Missing '?' -> {qtext[:80]}")
        if len(options) < 3:
            issues.append(f"  Q{i}: Only {len(options)} options")
        if correct < 0 or correct >= len(options):
            issues.append(f"  Q{i}: Bad correct_index={correct}")
        
        # Check for duplicate options
        lower_opts = [o.lower().strip() for o in options]
        if len(set(lower_opts)) != len(lower_opts):
            issues.append(f"  Q{i}: Duplicate options")
        
        answers[q["id"]] = correct
        
        print(f"\n  Q{i}: {qtext}")
        for j, opt in enumerate(options):
            marker = " <-- correct" if j == correct else ""
            print(f"    [{j}] {opt}{marker}")
    
    if issues:
        print(f"\nQUIZ ISSUES ({len(issues)}):")
        for issue in issues:
            print(issue)
    else:
        print("\nNo quiz issues found!")
    
    # Submit quiz (all correct)
    print("\n--- Submit (all correct) ---")
    quiz_id = data.get("quiz_id", "")
    submit_url = f"{BASE}/quiz/submit"
    # Build answers list matching question order
    answers_list = [q["correct_index"] for q in questions]
    payload = {"quiz_id": quiz_id, "answers": answers_list}
    r2 = requests.post(submit_url, json=payload, timeout=30)
    print(f"POST Status: {r2.status_code}")
    if r2.status_code == 200:
        result = r2.json()
        print(f"Score: {result['score']}/{result['total']} ({result['percentage']}%)")
        print(f"Passed: {result['passed']}")
    else:
        print(f"FAIL: {r2.text[:300]}")
        issues.append("Submit failed")
    
    return len(issues) == 0


if __name__ == "__main__":
    print("FINAL VALIDATION - Summary & Quiz\n")
    s_ok = test_summary()
    q_ok = test_quiz()
    
    print("\n" + "=" * 60)
    print(f"RESULT: Summary={'PASS' if s_ok else 'ISSUES'}, Quiz={'PASS' if q_ok else 'ISSUES'}")
    print("=" * 60)
