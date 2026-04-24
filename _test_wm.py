import sys
sys.path.insert(0, '.')
from pymongo import MongoClient
from backend.services.summarizer import _detect_watermarks
c = MongoClient('mongodb://localhost:27017')
chunks = list(c['eduai_db']['chunks'].find({'course_id':'69e8ab5bcc7caaec228d6848'}))
print(f"Chunks: {len(chunks)}")
wms = _detect_watermarks(chunks)
print(f"Watermarks detected: {len(wms)}")
for w in wms[:20]:
    print(" -", repr(w))
