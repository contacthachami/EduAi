from pymongo import MongoClient
import re
c = MongoClient('mongodb://localhost:27017')
chunks = list(c['eduai_db']['chunks'].find({'course_id':'69e8ab5bcc7caaec228d6848','page':1}))
print(f"Page 1 chunks: {len(chunks)}")
for i, ch in enumerate(chunks[:3]):
    print(f"\n=== Chunk {i} chap='{ch.get('chapter')}' ===")
    print(repr(ch['text'][:600]))
