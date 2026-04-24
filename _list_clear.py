from pymongo import MongoClient
c = MongoClient('mongodb://localhost:27017')
db = c['eduai_db']
for course in db.courses.find({}, {'_id': 1, 'name': 1, 'title': 1, 'filename': 1}):
    print(str(course['_id']), '|', course.get('name') or course.get('title') or course.get('filename') or '?')
print()
r = db.summaries.delete_many({})
print('Deleted', r.deleted_count, 'cached summaries')
