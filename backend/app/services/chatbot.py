import httpx
import logging
from supabase import Client
from app.models.schemas import ChatRequest, ChatResponse
from app.core.config import settings
from app.services import hs_search, history as history_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên về xuất nhập khẩu Việt Nam – Trung Quốc.
Nhiệm vụ: tư vấn mã HS code, thuế suất, thủ tục hải quan dựa trên dữ liệu được cung cấp.

Nguyên tắc:
- Trả lời bằng tiếng Việt, ngắn gọn, chính xác.
- Chỉ trả lời dựa trên dữ liệu HS codes được cung cấp trong context.
- Nếu không tìm thấy thông tin liên quan, nói rõ "Không tìm thấy mã HS phù hợp".
- Khi đề cập mã HS, luôn kèm theo thuế suất MFN và ACFTA (nếu có).
- Không bịa đặt số liệu thuế suất ngoài dữ liệu cung cấp."""


def _build_context(hs_results) -> str:
    if not hs_results:
        return "Không tìm thấy mã HS liên quan trong cơ sở dữ liệu."
    lines = ["Dữ liệu HS Codes liên quan:"]
    for item in hs_results:
        line = f"- {item.code}: {item.description_vi}"
        if item.tax_rate_normal is not None:
            line += f" | Thuế MFN: {item.tax_rate_normal}%"
        if item.tax_rate_preferential is not None:
            line += f" | ACFTA: {item.tax_rate_preferential}%"
        if item.unit:
            line += f" | ĐVT: {item.unit}"
        lines.append(line)
    return "\n".join(lines)


async def _call_ollama(messages: list[dict]) -> str:
    """Call Ollama OpenAI-compatible endpoint."""
    url = f"{settings.OLLAMA_BASE_URL}/v1/chat/completions"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1024,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def ask(db: Client, request: ChatRequest, user_id: str | None) -> ChatResponse:
    """
    Chatbot RAG flow:
    1. search_hs_codes() → top 5 relevant HS codes
    2. Build context from results
    3. Call Ollama (qwen2.5-coder:32b) with system prompt + context + question
    4. Log to search_history (non-fatal if fails)
    5. Return answer + citation codes
    """
    # Step 1: RAG — search top 5 HS codes
    hs_results = await hs_search.search(db, request.question, limit=5, threshold=0.1)

    # Step 2: Build context
    context = _build_context(hs_results)
    citation_codes = [r.code for r in hs_results]

    # Step 3: Call Ollama
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"{context}\n\nCâu hỏi: {request.question}",
        },
    ]

    try:
        answer = await _call_ollama(messages)
    except httpx.ConnectError:
        answer = (
            "Không thể kết nối Ollama. Vui lòng đảm bảo Ollama đang chạy "
            "tại http://localhost:11434 và model đã được tải."
        )
        logger.error("Ollama connection refused")
    except httpx.TimeoutException:
        answer = "Ollama mất quá nhiều thời gian phản hồi. Vui lòng thử lại."
        logger.error("Ollama timeout")
    except Exception as e:
        answer = f"Lỗi hệ thống: {str(e)[:100]}"
        logger.error(f"Ollama error: {e}")

    # Step 4: Log search (non-fatal)
    service_db = None
    try:
        from app.core.database import get_service_client
        service_db = get_service_client()
        await history_service.record_search(
            service_db,
            query=request.question,
            result_codes=citation_codes,
            user_id=user_id,
            user_session=request.session_id,
        )
    except Exception as e:
        logger.warning(f"history record_search failed (non-fatal): {e}")

    return ChatResponse(
        answer=answer,
        citations=citation_codes,
        session_id=request.session_id,
    )
