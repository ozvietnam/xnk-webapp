import httpx
import logging
from supabase import Client
from app.models.schemas import ChatRequest, ChatResponse
from app.services import hs_search
from app.services import history as history_service
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là chuyên gia tư vấn Hải quan và Xuất Nhập Khẩu Việt Nam - Trung Quốc.
Nhiệm vụ: Hỗ trợ tra cứu mã HS code, thuế suất, thủ tục hải quan, quy định xuất nhập khẩu.

Nguyên tắc trả lời:
- Luôn trả lời bằng tiếng Việt
- Dựa vào thông tin HS codes được cung cấp trong context
- Nêu rõ mã HS code và thuế suất cụ thể khi có
- Nếu không đủ thông tin, hướng dẫn tra cứu thêm tại trang chính thức
- Ngắn gọn, chính xác, chuyên nghiệp"""


def _build_context(hs_results: list) -> str:
    """Format HS code search results into LLM context."""
    if not hs_results:
        return "Không tìm thấy mã HS liên quan trong cơ sở dữ liệu."

    lines = ["Các mã HS code liên quan:\n"]
    for r in hs_results:
        line = f"- Mã {r.code}: {r.description_vi}"
        if r.description_en:
            line += f" ({r.description_en})"
        if r.tax_rate_normal is not None:
            line += f" | Thuế MFN: {r.tax_rate_normal}%"
        if r.tax_rate_preferential is not None:
            line += f" | ACFTA/RCEP: {r.tax_rate_preferential}%"
        if r.unit:
            line += f" | ĐVT: {r.unit}"
        lines.append(line)

    return "\n".join(lines)


async def ask(db: Client, request: ChatRequest, user_id: str | None) -> ChatResponse:
    """
    Chatbot flow:
    1. Search HS DB (top 5 relevant codes)
    2. Build context prompt
    3. Call Ollama (qwen2.5-coder:32b via OpenAI-compatible API)
    4. Log to search_history
    5. Return answer + citations
    """
    question = request.question.strip()

    # Step 1: Search top 5 HS codes
    try:
        hs_results = await hs_search.search(db, question, limit=5, threshold=0.10)
    except Exception as e:
        logger.warning(f"HS search failed: {e}")
        hs_results = []

    # Step 2: Build context
    context = _build_context(hs_results)
    citations = [r.code for r in hs_results]

    user_message = f"""Câu hỏi: {question}

Context từ cơ sở dữ liệu HS codes:
{context}

Hãy trả lời câu hỏi dựa trên thông tin trên."""

    # Step 3: Call Ollama OpenAI-compatible endpoint
    answer = await _call_ollama(user_message)

    # Step 4: Log search history (non-fatal)
    try:
        from app.core.database import get_service_client
        service_db = get_service_client()
        await history_service.record_search(
            db=service_db,
            query=question,
            result_codes=citations,
            user_id=user_id,
            user_session=request.session_id,
        )
    except Exception as e:
        logger.warning(f"record_search failed (non-fatal): {e}")

    return ChatResponse(
        answer=answer,
        citations=citations,
        session_id=request.session_id,
    )


async def _call_ollama(user_message: str) -> str:
    """Call Ollama via OpenAI-compatible /v1/chat/completions endpoint."""
    url = f"{settings.OLLAMA_BASE_URL}/v1/chat/completions"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.TimeoutException:
        logger.error("Ollama request timed out")
        return "Xin lỗi, hệ thống AI đang bận. Vui lòng thử lại sau."
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama HTTP error: {e.response.status_code} — {e.response.text}")
        return "Xin lỗi, không thể kết nối tới hệ thống AI. Vui lòng thử lại sau."
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        return "Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi. Vui lòng thử lại."
