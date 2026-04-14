import json
import httpx
import logging
from supabase import Client
from app.models.schemas import ChatRequest, ChatResponse
from app.services import hs_search
from app.services import regulations as regulations_service
from app.services import history as history_service
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent system prompt — instructs LLM to THINK first, then ACT with tools
# ---------------------------------------------------------------------------
AGENT_SYSTEM_PROMPT = """Bạn là chuyên gia tư vấn Hải quan và Xuất Nhập Khẩu Việt Nam - Trung Quốc.

## Cách làm việc
Bạn có quyền truy cập các công cụ tra cứu cơ sở dữ liệu. Hãy làm việc theo quy trình:

1. **Phân tích câu hỏi**: Đọc kỹ câu hỏi, xác định người dùng cần gì (mã HS, thuế suất, thủ tục, quy định, hay tổng hợp nhiều thứ).
2. **Quyết định hành động**: Chọn tool phù hợp để tra cứu. Có thể gọi nhiều tool nếu cần.
3. **Kiểm chứng**: Xem kết quả trả về, đánh giá có đủ thông tin chưa. Nếu chưa đủ → gọi thêm tool khác hoặc search với từ khóa khác.
4. **Kết luận**: Tổng hợp thông tin đã xác minh, trả lời chính xác.

## Nguyên tắc
- Luôn trả lời bằng tiếng Việt.
- KHÔNG bịa mã HS code hay thuế suất — chỉ dùng dữ liệu từ tool trả về.
- Nêu rõ mã HS code và thuế suất cụ thể khi có.
- Nếu tool không tìm thấy kết quả phù hợp, thử search với từ khóa khác trước khi kết luận.
- Nếu thực sự không đủ thông tin sau khi đã thử, hướng dẫn tra cứu tại trang chính thức (customs.gov.vn).
- Ngắn gọn, chính xác, chuyên nghiệp.
- Khi trả lời về thuế suất, phân biệt rõ: thuế MFN (thông thường), thuế ưu đãi ACFTA/RCEP, thuế đặc biệt.

## QUY TẮC MÃ HS 8 SỐ — BẮT BUỘC
- Mã HS 4-6 số (nhóm/phân nhóm): tương đối ổn định quốc tế, có thể trả lời tự tin.
- Mã HS 8 số (chi tiết): THAY ĐỔI THƯỜNG XUYÊN theo biểu thuế mới của Việt Nam. Database hiện tại CÓ THỂ CHƯA CẬP NHẬT.
- Khi trả lời mã 8 số, BẮT BUỘC ghi rõ: "Mã 8 số này tra từ cơ sở dữ liệu tham khảo. Vui lòng đối chiếu biểu thuế XNK mới nhất tại customs.gov.vn hoặc VBPL Hải quan để xác nhận mã chính xác."
- KHÔNG BAO GIỜ nói mã 8 số là "chính xác" hay "chắc chắn" — luôn dùng từ "tham khảo", "gợi ý phân loại".
- Ưu tiên trả lời ở mức nhóm 4-6 số (ổn định) + gợi ý hướng phân loại 8 số kèm cảnh báo.

## Lưu ý quan trọng
- Câu hỏi về "thuế nhập khẩu từ Trung Quốc" → ưu tiên thuế ACFTA/RCEP (ưu đãi) bên cạnh MFN.
- Câu hỏi về "thủ tục", "giấy tờ", "chứng từ" → dùng tool search_regulations.
- Câu hỏi chung chung → phân tích ý định, search HS code + quy định nếu cần.
- Nếu người dùng hỏi ngoài phạm vi hải quan/XNK → từ chối lịch sự, hướng dẫn lại phạm vi hỗ trợ.

## Giọng điệu kết luận — BẮT BUỘC
Khi kết thúc câu trả lời, bạn phải nói với tư cách chuyên gia ĐÃ TRA CỨU XONG, KHÔNG phải gợi ý user tự tra.

ĐÚNG (nói như đã làm):
- "Tôi đã xem kỹ chi tiết nhóm XX.XX và chú giải liên quan..."
- "Tôi đã kiểm tra tất cả Thông báo kết quả phân loại (TB-TCHQ) có liên quan đến từ khóa này."
- "Dựa trên dữ liệu đã tra cứu, tôi khuyến nghị: ..."

SAI (đẩy việc cho user):
- "Bạn nên xem xét kỹ Chú giải chi tiết nhóm..."
- "Kiểm tra các TB-TCHQ liên quan..."
- "Chuẩn bị hồ sơ đầy đủ..."

Sau khi kết luận, chỉ đưa 2 gợi ý hành động cụ thể:
1. Mô tả chi tiết hơn về hàng hóa (chất liệu, công dụng, xuất xứ...) để xác định chính xác mã HS.
2. Kiểm tra thêm văn bản chuyên ngành nếu hàng hóa thuộc diện quản lý đặc biệt."""

# ---------------------------------------------------------------------------
# Tool definitions (OpenAI function calling format)
# ---------------------------------------------------------------------------
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_hs_codes",
            "description": "Tìm kiếm mã HS code theo mô tả hàng hóa hoặc mã số. Trả về danh sách mã HS kèm thuế suất, đơn vị tính. Dùng khi cần tìm mã HS cho một mặt hàng cụ thể.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Từ khóa tìm kiếm (tên hàng hóa, mô tả, hoặc mã HS). VD: 'điện thoại di động', 'thép cuộn', '8517'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số kết quả tối đa (mặc định 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_hs_detail",
            "description": "Lấy thông tin chi tiết của một mã HS code cụ thể (thuế suất, mô tả, ghi chú). Dùng khi đã biết mã HS chính xác và cần xem chi tiết.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Mã HS code chính xác. VD: '85171400', '7210'"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_regulations",
            "description": "Tra cứu quy định hải quan theo danh mục. Dùng khi câu hỏi liên quan đến thủ tục, chứng từ, kiểm tra chuyên ngành, hoặc quy định thuế.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Danh mục quy định",
                        "enum": ["thu-tuc", "chung-tu", "thue", "kiem-tra"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số kết quả tối đa (mặc định 5)",
                        "default": 5
                    }
                },
                "required": []
            }
        }
    },
]

# Maximum tool-call iterations to prevent infinite loops
MAX_AGENT_ITERATIONS = 5

# ---------------------------------------------------------------------------
# Provider chain — smart fallback across multiple LLM providers
# Uses api_manager for key rotation (ưu tiên free → paid)
#
# Strategy: "reason" chain customized for HS code reasoning
#   DeepSeek V3 (reasoning mạnh, $0.14/1M) → Groq (FREE, nhanh)
#   → Gemini Flash (FREE, ổn định) → OpenRouter (quality, fallback cuối)
#   → Ollama (local offline)
# ---------------------------------------------------------------------------
PROVIDER_CHAIN = [
    {
        "name": "deepseek",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
        "timeout": 60.0,
    },
    {
        "name": "groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "timeout": 30.0,
    },
    {
        "name": "gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.0-flash",
        "timeout": 45.0,
    },
    {
        "name": "openrouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "anthropic/claude-3.5-sonnet",
        "timeout": 60.0,
    },
]


# ---------------------------------------------------------------------------
# Tool executor — dispatches tool calls to actual service functions
# ---------------------------------------------------------------------------
async def _execute_tool(db: Client, name: str, args: dict) -> tuple[str, list[str]]:
    """
    Execute a tool call and return (result_text, hs_codes_cited).
    """
    citations: list[str] = []

    if name == "search_hs_codes":
        query = args.get("query", "")
        limit = args.get("limit", 5)
        results = await hs_search.search(db, query, limit=limit, threshold=0.10)
        if not results:
            return "Không tìm thấy mã HS nào phù hợp với từ khóa này.", citations

        has_8digit = False
        lines = []
        for r in results:
            citations.append(r.code)
            code_clean = r.code.replace(".", "")
            is_8digit = len(code_clean) >= 8
            if is_8digit:
                has_8digit = True
            tag = " [THAM KHẢO - cần đối chiếu biểu thuế mới]" if is_8digit else ""
            line = f"- Mã {r.code}{tag}: {r.description_vi}"
            if r.description_en:
                line += f" ({r.description_en})"
            if r.tax_rate_normal is not None:
                line += f" | Thuế MFN: {r.tax_rate_normal}%"
            if r.tax_rate_preferential is not None:
                line += f" | ACFTA/RCEP: {r.tax_rate_preferential}%"
            if r.tax_rate_special is not None:
                line += f" | Thuế đặc biệt: {r.tax_rate_special}%"
            if r.unit:
                line += f" | ĐVT: {r.unit}"
            if r.notes:
                line += f" | Ghi chú: {r.notes}"
            lines.append(line)
        result_text = "\n".join(lines)
        if has_8digit:
            result_text += "\n\n⚠️ LƯU Ý: Các mã 8 số trên tra từ CSDL tham khảo, có thể chưa cập nhật biểu thuế mới nhất. Khi trả lời khách, BẮT BUỘC ghi rõ đây là mã tham khảo và hướng dẫn đối chiếu biểu thuế XNK hiện hành."
        return result_text, citations

    elif name == "get_hs_detail":
        code = args.get("code", "")
        result = await hs_search.get_by_code(db, code)
        if not result:
            return f"Không tìm thấy mã HS '{code}' trong cơ sở dữ liệu.", citations

        citations.append(result.code)
        code_clean = result.code.replace(".", "")
        is_8digit = len(code_clean) >= 8
        ref_tag = " [THAM KHẢO]" if is_8digit else ""
        detail = f"Mã HS: {result.code}{ref_tag}\n"
        detail += f"Mô tả (VI): {result.description_vi}\n"
        if result.description_en:
            detail += f"Mô tả (EN): {result.description_en}\n"
        if result.tax_rate_normal is not None:
            detail += f"Thuế MFN (thông thường): {result.tax_rate_normal}%\n"
        if result.tax_rate_preferential is not None:
            detail += f"Thuế ưu đãi ACFTA/RCEP: {result.tax_rate_preferential}%\n"
        if result.tax_rate_special is not None:
            detail += f"Thuế đặc biệt: {result.tax_rate_special}%\n"
        if result.unit:
            detail += f"Đơn vị tính: {result.unit}\n"
        if result.notes:
            detail += f"Ghi chú: {result.notes}\n"
        if is_8digit:
            detail += "\n⚠️ Mã 8 số này từ CSDL tham khảo, có thể chưa cập nhật biểu thuế mới nhất. BẮT BUỘC ghi rõ là mã tham khảo khi trả lời khách."
        return detail, citations

    elif name == "search_regulations":
        category = args.get("category")
        limit = args.get("limit", 5)
        results = await regulations_service.list_regulations(db, category, limit)
        if not results:
            msg = "Không tìm thấy quy định"
            if category:
                msg += f" trong danh mục '{category}'"
            return msg + ".", citations

        lines = []
        for r in results:
            line = f"- [{r.category or 'chung'}] {r.title}"
            if r.effective_date:
                line += f" (hiệu lực: {r.effective_date})"
            if r.source_document:
                line += f" — {r.source_document}"
            if r.content_vi:
                # Truncate long content for context window
                content_preview = r.content_vi[:300]
                if len(r.content_vi) > 300:
                    content_preview += "..."
                line += f"\n  Nội dung: {content_preview}"
            lines.append(line)
        return "\n".join(lines), citations

    else:
        return f"Tool '{name}' không tồn tại.", citations


# ---------------------------------------------------------------------------
# Main entry point — Agentic loop
# ---------------------------------------------------------------------------
async def ask(db: Client, request: ChatRequest, user_id: str | None) -> ChatResponse:
    """
    Agentic chatbot flow:
    1. LLM analyzes the question, decides which tools to call
    2. Execute tool calls, feed results back to LLM
    3. LLM reviews results, may call more tools or produce final answer
    4. Repeat up to MAX_AGENT_ITERATIONS
    5. Log history and return
    """
    question = request.question.strip()
    all_citations: list[str] = []

    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    # --- Agentic loop: think → act → observe → repeat ---
    answer = "Xin lỗi, tôi không thể xử lý câu hỏi này. Vui lòng thử lại."

    for iteration in range(MAX_AGENT_ITERATIONS):
        logger.info(f"Agent iteration {iteration + 1}/{MAX_AGENT_ITERATIONS}")

        response_data = await _call_llm_with_tools(messages)

        if response_data is None:
            # LLM call failed entirely
            answer = "Xin lỗi, hệ thống AI đang bận. Vui lòng thử lại sau."
            break

        choice = response_data["choices"][0]
        finish_reason = choice.get("finish_reason", "stop")
        assistant_message = choice["message"]

        if finish_reason == "tool_calls" or assistant_message.get("tool_calls"):
            # --- Agent wants to use tools ---
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls", [])
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except (json.JSONDecodeError, TypeError):
                    fn_args = {}

                logger.info(f"Agent calling tool: {fn_name}({fn_args})")
                result_text, cited_codes = await _execute_tool(db, fn_name, fn_args)
                all_citations.extend(cited_codes)

                # Feed tool result back to LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_text,
                })

            # Continue loop — LLM will see tool results and decide next step

        else:
            # --- Agent produced final answer (no more tool calls) ---
            content = assistant_message.get("content", "")
            if content:
                answer = content.strip()
            break

    # Deduplicate citations preserving order
    seen = set()
    unique_citations = []
    for c in all_citations:
        if c not in seen:
            seen.add(c)
            unique_citations.append(c)

    # --- Log search history (non-fatal) ---
    try:
        from app.core.database import get_service_client
        service_db = get_service_client()
        await history_service.record_search(
            db=service_db,
            query=question,
            result_codes=unique_citations,
            user_id=user_id,
            user_session=request.session_id,
        )
    except Exception as e:
        logger.warning(f"record_search failed (non-fatal): {e}")

    return ChatResponse(
        answer=answer,
        citations=unique_citations,
        session_id=request.session_id,
    )


# ---------------------------------------------------------------------------
# LLM call — multi-provider fallback with api_manager key rotation
# ---------------------------------------------------------------------------
async def _call_llm_with_tools(messages: list[dict]) -> dict | None:
    """
    Call LLM with tool definitions using multi-provider fallback.

    Strategy (from api_manager SKILL.md):
      1. DeepSeek V3  — reasoning mạnh, tool calling, $0.14/1M tokens
      2. Groq          — FREE, Llama 3.3 70B, inference cực nhanh
      3. Gemini Flash   — FREE, 9000 req/ngày, ổn định
      4. OpenRouter     — PAID, access Claude 3.5, fallback quality cao
      5. Ollama         — local, offline fallback cuối cùng

    Key rotation: api_manager tự xoay vòng key, ưu tiên key ít dùng nhất hôm nay.
    """
    # Try to use api_manager for smart key rotation
    api_mgr_available = False
    try:
        from app.core.api_manager import get_key
        api_mgr_available = True
    except ImportError:
        logger.warning("api_manager not available — falling back to config-based keys")

    if api_mgr_available:
        for provider in PROVIDER_CHAIN:
            key = get_key(provider["name"], use_case="reason")
            if not key:
                logger.debug(f"No key for {provider['name']}, skipping")
                continue

            logger.info(f"Trying provider: {provider['name']} ({provider['model']})")
            result = await _call_openai_compat(
                url=provider["url"],
                model=provider["model"],
                key=key,
                messages=messages,
                timeout=provider["timeout"],
            )
            if result is not None:
                logger.info(f"LLM success via {provider['name']}")
                return result
            logger.warning(f"{provider['name']} failed, trying next...")

    else:
        # Fallback: use settings-based keys (old behavior)
        if settings.GEMINI_API_KEY:
            result = await _call_openai_compat(
                url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                model=settings.GEMINI_MODEL,
                key=settings.GEMINI_API_KEY,
                messages=messages,
                timeout=45.0,
            )
            if result is not None:
                return result

    # Ultimate fallback: local Ollama
    logger.info("All cloud providers failed — trying local Ollama")
    return await _call_ollama_with_tools(messages)


# ---------------------------------------------------------------------------
# Generic OpenAI-compatible provider call (works for all providers)
# ---------------------------------------------------------------------------
async def _call_openai_compat(
    url: str,
    model: str,
    key: str,
    messages: list[dict],
    timeout: float = 45.0,
) -> dict | None:
    """
    Call any OpenAI-compatible endpoint with function calling support.
    Works with: DeepSeek, Groq, Gemini, OpenRouter, OpenAI, Cerebras, NVIDIA.
    """
    payload = {
        "model": model,
        "messages": messages,
        "tools": AGENT_TOOLS,
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error(f"Timeout calling {url}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} from {url}: {e.response.text[:300]}")
    except Exception as e:
        logger.error(f"Failed calling {url}: {e}")
    return None


# ---------------------------------------------------------------------------
# Ollama local fallback (no api_manager needed)
# ---------------------------------------------------------------------------
async def _call_ollama_with_tools(messages: list[dict]) -> dict | None:
    """Call Ollama via OpenAI-compatible endpoint with function calling."""
    url = f"{settings.OLLAMA_BASE_URL}/v1/chat/completions"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "tools": AGENT_TOOLS,
        "temperature": 0.3,
        "max_tokens": 2048,
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error("Ollama request timed out")
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama HTTP error: {e.response.status_code} — {e.response.text[:300]}")
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
    return None
