"""
T05 integration test: Chatbot service with Ollama.
Run: cd backend && python3 scripts/test_t05_chatbot.py
"""
import asyncio
import sys
import os

# Add backend/ to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_client
from app.models.schemas import ChatRequest
from app.services import chatbot as chatbot_service


async def test_chatbot():
    db = get_client()
    errors = []

    # Test 1: Basic question about điện thoại
    print("\n[1] Hỏi về mã HS điện thoại...")
    req = ChatRequest(question="Mã HS code của điện thoại di động là gì? Thuế suất bao nhiêu?")
    resp = await chatbot_service.ask(db, req, user_id=None)
    if resp.answer and len(resp.answer) > 20:
        print(f"  ✓ Answer ({len(resp.answer)} chars): {resp.answer[:120]}...")
        print(f"  ✓ Citations: {resp.citations}")
    else:
        print(f"  ✗ Answer too short or empty: {resp.answer!r}")
        errors.append("answer too short")

    # Test 2: Question about thép
    print("\n[2] Hỏi về thép cuộn...")
    req2 = ChatRequest(question="Thuế nhập khẩu thép cuộn từ Trung Quốc là bao nhiêu?", session_id="test-session-1")
    resp2 = await chatbot_service.ask(db, req2, user_id=None)
    if resp2.answer and len(resp2.answer) > 20:
        print(f"  ✓ Answer ({len(resp2.answer)} chars): {resp2.answer[:120]}...")
        print(f"  ✓ Citations: {resp2.citations}")
        print(f"  ✓ Session ID: {resp2.session_id}")
    else:
        print(f"  ✗ Empty answer")
        errors.append("thep answer empty")

    # Test 3: General question (no HS match)
    print("\n[3] Hỏi tổng quát về thủ tục hải quan...")
    req3 = ChatRequest(question="Thủ tục hải quan xuất khẩu cần những giấy tờ gì?")
    resp3 = await chatbot_service.ask(db, req3, user_id=None)
    if resp3.answer and len(resp3.answer) > 20:
        print(f"  ✓ Answer ({len(resp3.answer)} chars): {resp3.answer[:120]}...")
    else:
        print(f"  ✗ Empty answer")
        errors.append("general answer empty")

    print("\n" + "="*50)
    if errors:
        print(f"FAILED: {errors}")
        sys.exit(1)
    else:
        print("T05 chatbot tests: ALL PASSED ✓")


if __name__ == "__main__":
    asyncio.run(test_chatbot())
