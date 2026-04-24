from pymongo import MongoClient
import re
c = MongoClient('mongodb://localhost:27017')
chunks = list(c['eduai_db']['chunks'].find({'course_id':'69e8ab5bcc7caaec228d6848'}))
print(f"Total chunks: {len(chunks)}")
# Look for Y.TAOUIL occurrences
count = 0
for ch in chunks:
    if 'TAOUIL' in ch['text']:
        count += 1
print(f"Chunks containing TAOUIL: {count}")
# Show 3 sample contexts
shown = 0
for ch in chunks:
    if 'TAOUIL' in ch['text'] and shown < 3:
        idx = ch['text'].find('TAOUIL')
        print(f"\n--- Chunk page {ch.get('page')} chap {ch.get('chapter','?')[:50]} ---")
        print(repr(ch['text'][max(0,idx-50):idx+150]))
        shown += 1
# Now lines analysis
print("\n=== LINE ANALYSIS ===")
from collections import Counter
line_counts = Counter()
for ch in chunks:
    for ln in ch['text'].split('\n'):
        ln_n = re.sub(r'\d+', '#', ln).strip()
        ln_n = re.sub(r'\s+', ' ', ln_n)
        if 8 < len(ln_n) < 150 and 'TAOUIL' in ln_n.upper():
            line_counts[ln_n] += 1
for ln, cnt in line_counts.most_common(10):
    print(f"  [{cnt}x] {ln!r}")
