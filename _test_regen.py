"""Quick test: trigger summary regeneration and display results."""
import requests
import time

COURSE_ID = "69e6ab9fe8eaf33994528fae"
BASE = "http://127.0.0.1:8000/api/summary"

# Trigger generation
r = requests.get(f"{BASE}/{COURSE_ID}")
print("Initial:", r.json().get("status"))

# Poll until ready
for i in range(20):
    time.sleep(10)
    r = requests.get(f"{BASE}/{COURSE_ID}")
    data = r.json()
    status = data.get("status")
    print(f"Poll {i+1}: {status}")
    if status == "ready":
        chapters = data.get("chapters", [])
        print(f"\nTotal chapters: {len(chapters)}")
        for j, ch in enumerate(chapters):
            print("\n" + "=" * 60)
            print(f"Chapter {j+1}: {ch['title']}")
            print(f"Pages: {ch['pages']}")
            print(f"Key Concepts: {ch['key_concepts']}")
            print(f"Summary:\n{ch['summary']}")
        break
else:
    print("Timed out waiting for generation")
