"""T05 Chatbot tests — unit tests (no external calls)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.chatbot import _build_context, ask, SYSTEM_PROMPT
from app.models.schemas import ChatRequest, ChatResponse


# ── _build_context ────────────────────────────────────────────

def test_build_context_empty():
    result = _build_context([])
    assert "Không tìm thấy" in result


def test_build_context_with_results():
    item = MagicMock()
    item.code = "8517.12.00"
    item.description_vi = "Điện thoại di động"
    item.tax_rate_normal = 10.0
    item.tax_rate_preferential = 0.0
    item.unit = "chiếc"

    result = _build_context([item])
    assert "8517.12.00" in result
    assert "Điện thoại di động" in result
    assert "MFN: 10.0%" in result
    assert "ACFTA: 0.0%" in result


def test_build_context_none_tax():
    item = MagicMock()
    item.code = "8471.30.00"
    item.description_vi = "Máy tính xách tay"
    item.tax_rate_normal = None
    item.tax_rate_preferential = None
    item.unit = None

    result = _build_context([item])
    assert "8471.30.00" in result
    assert "MFN" not in result


# ── SYSTEM_PROMPT ─────────────────────────────────────────────

def test_system_prompt_contains_required_content():
    assert "xuất nhập khẩu" in SYSTEM_PROMPT.lower() or "xuất nhập khẩu" in SYSTEM_PROMPT
    assert "MFN" in SYSTEM_PROMPT
    assert "ACFTA" in SYSTEM_PROMPT
    assert "tiếng Việt" in SYSTEM_PROMPT


# ── ask() — unit test with mocks ─────────────────────────────

@pytest.mark.asyncio
async def test_ask_returns_chat_response():
    mock_db = MagicMock()
    request = ChatRequest(question="Điện thoại di động mã HS là gì?", session_id="test-123")

    mock_hs_result = MagicMock()
    mock_hs_result.code = "8517.12.00"
    mock_hs_result.description_vi = "Điện thoại di động"
    mock_hs_result.tax_rate_normal = 10.0
    mock_hs_result.tax_rate_preferential = 0.0
    mock_hs_result.unit = "chiếc"

    with patch("app.services.chatbot.hs_search.search", new_callable=AsyncMock) as mock_search, \
         patch("app.services.chatbot._call_ollama", new_callable=AsyncMock) as mock_ollama, \
         patch("app.services.chatbot.history_service.record_search", new_callable=AsyncMock):

        mock_search.return_value = [mock_hs_result]
        mock_ollama.return_value = "Mã HS 8517.12.00 - Thuế MFN 10%, ACFTA 0%"

        resp = await ask(mock_db, request, user_id=None)

    assert isinstance(resp, ChatResponse)
    assert resp.answer == "Mã HS 8517.12.00 - Thuế MFN 10%, ACFTA 0%"
    assert "8517.12.00" in resp.citations
    assert resp.session_id == "test-123"


@pytest.mark.asyncio
async def test_ask_handles_ollama_connection_error():
    import httpx
    mock_db = MagicMock()
    request = ChatRequest(question="Test câu hỏi")

    with patch("app.services.chatbot.hs_search.search", new_callable=AsyncMock) as mock_search, \
         patch("app.services.chatbot._call_ollama", new_callable=AsyncMock) as mock_ollama, \
         patch("app.services.chatbot.history_service.record_search", new_callable=AsyncMock):

        mock_search.return_value = []
        mock_ollama.side_effect = httpx.ConnectError("Connection refused")

        resp = await ask(mock_db, request, user_id=None)

    assert isinstance(resp, ChatResponse)
    assert "Ollama" in resp.answer or "kết nối" in resp.answer


@pytest.mark.asyncio
async def test_ask_sends_context_to_ollama():
    mock_db = MagicMock()
    request = ChatRequest(question="Thuế nhập khẩu thép?")
    captured_messages = []

    mock_hs = MagicMock()
    mock_hs.code = "7210.49.11"
    mock_hs.description_vi = "Thép mạ kẽm"
    mock_hs.tax_rate_normal = 15.0
    mock_hs.tax_rate_preferential = 5.0
    mock_hs.unit = "kg"

    async def capture_ollama(messages):
        captured_messages.extend(messages)
        return "Thép mạ kẽm mã 7210.49.11, thuế MFN 15%, ACFTA 5%"

    with patch("app.services.chatbot.hs_search.search", new_callable=AsyncMock) as mock_search, \
         patch("app.services.chatbot._call_ollama", side_effect=capture_ollama), \
         patch("app.services.chatbot.history_service.record_search", new_callable=AsyncMock):

        mock_search.return_value = [mock_hs]
        resp = await ask(mock_db, request, user_id=None)

    # System message must match SYSTEM_PROMPT exactly
    assert captured_messages[0]["role"] == "system"
    assert captured_messages[0]["content"] == SYSTEM_PROMPT

    # User message must include HS context + question
    user_msg = captured_messages[1]["content"]
    assert "7210.49.11" in user_msg
    assert "Thuế nhập khẩu thép?" in user_msg
    assert resp.citations == ["7210.49.11"]
