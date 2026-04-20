"""Quick summary test - test the hallucination fix with a sample chapter."""
import requests
import json
import time

BASE = "http://127.0.0.1:8000/api"
CID = "69e6314a6ba4f898782d1ff4"

print("=== TEST SUMMARY ===")
print("(This takes ~18 min for 32 chapters, please wait...)")
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
        if not summary or summary.startswith("Resume non disponible"):
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
    # Show first 5 samples
    for i, ch in enumerate(chapters[:5]):
        print(f"\n  Ch {i+1} [{ch['title']}]")
        print(f"    Summary: {ch['summary'][:150]}...")
        print(f"    Concepts: {ch['key_concepts'][:5]}")
        print(f"    Pages: {ch['pages']}")
else:
    print(f"ERROR: {r.text[:500]}")

print(f"\nTotal time: {elapsed:.1f}s")
