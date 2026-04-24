import asyncio
from backend.database.mongodb import connect_db, get_db, close_db

async def m():
    await connect_db()
    db = get_db()
    cursor = db.summaries.find({}, {"course_id": 1, "cache_version": 1, "chapters.title": 1})
    async for d in cursor:
        chs = d.get("chapters", [])
        print(d.get("course_id"), "v=", d.get("cache_version"), "n_chapters=", len(chs))
    # Also list courses collection
    print("\n--- COURSES ---")
    async for c in db.courses.find({}, {"_id": 1, "title": 1}):
        print(c.get("_id"), c.get("title"))
    await close_db()

asyncio.run(m())
