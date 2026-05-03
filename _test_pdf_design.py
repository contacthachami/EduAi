"""Test the redesigned PDF export with real MongoDB data."""
import asyncio, sys
sys.path.insert(0, '.')

async def test():
    from motor.motor_asyncio import AsyncIOMotorClient
    from backend.config import get_settings
    from backend.routers.export import _generate_summary_pdf, _generate_flashcards_pdf
    from bson import ObjectId

    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    course_id = "69f67101e57b1c6d074ff9eb"
    course  = await db.courses.find_one({"_id": ObjectId(course_id)})
    summary = await db.summaries.find_one({"course_id": course_id})
    flashcards = await db.flashcards.find({"course_id": course_id}).to_list(length=None)

    print(f"Course   : {course['name']}")
    print(f"Chapters : {len(summary.get('chapters', []))}")
    print(f"Flashcards: {len(flashcards)}")

    # Test summary PDF
    try:
        buf = _generate_summary_pdf(course["name"], summary.get("chapters", []))
        data = buf.read()
        with open("_test_resume.pdf", "wb") as f:
            f.write(data)
        print(f"Summary PDF  : OK — {len(data)} bytes → _test_resume.pdf")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"Summary PDF  : FAILED — {e}")

    # Test flashcards PDF
    if flashcards:
        try:
            buf2 = _generate_flashcards_pdf(course["name"], flashcards)
            data2 = buf2.read()
            with open("_test_flashcards.pdf", "wb") as f:
                f.write(data2)
            print(f"Flashcards PDF: OK — {len(data2)} bytes → _test_flashcards.pdf")
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"Flashcards PDF: FAILED — {e}")

    client.close()

asyncio.run(test())
