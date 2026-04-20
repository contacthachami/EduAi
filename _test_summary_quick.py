"""Quick summary test: hit the endpoint and show first 5 chapters."""
import requests, time

COURSE_ID = "69e6314a6ba4f898782d1ff4"
URL = f"http://127.0.0.1:8000/api/summary/{COURSE_ID}"

print("=== QUICK SUMMARY TEST ===")
t0 = time.time()
r = requests.get(URL, timeout=600)
elapsed = time.time() - t0
print(f"Status: {r.status_code} ({elapsed:.1f}s)")

if r.status_code == 200:
    data = r.json()
    chapters = data.get("chapters", [])
    print(f"Total chapters: {len(chapters)}\n")
    for i, ch in enumerate(chapters[:5], 1):
        title = ch["title"]
        summary = ch["summary"]
        concepts = ch.get("key_concepts", [])
        flag = " *** REPETITIVE ***" if len(set(summary.lower().split())) / max(len(summary.lower().split()), 1) < 0.45 else ""
        print(f"  Ch {i} [{title}]{flag}")
        print(f"    Summary ({len(summary)} chars): {summary[:150]}...")
        print(f"    Concepts: {concepts}")
        print(f"    Pages: {ch['pages']}\n")
else:
    print(f"Error: {r.text[:300]}")
