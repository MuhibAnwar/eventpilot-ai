import json
from unittest.mock import MagicMock, patch

import pytest

from app.agent import ALLOWED_TOOLS, extract_tool_from_text, pick_tool, route_user_query


def test_extract_tool_from_text_fences_and_prose():
    assert extract_tool_from_text('{"tool":"count_participants"}') == "count_participants"
    wrapped = 'Here:\n```json\n{"tool":"find_duplicates"}\n```'
    assert extract_tool_from_text(wrapped) == "find_duplicates"
    assert extract_tool_from_text('noise {"tool": "show_all"} end') == "show_all"
    assert extract_tool_from_text('{"tool":"evil_tool"}') == "none"
    assert extract_tool_from_text("no json") == "none"


def test_allowlist_unknown_becomes_none():
    assert extract_tool_from_text(json.dumps({"tool": "DROP TABLE"})) == "none"
    assert "none" in ALLOWED_TOOLS


@patch("app.agent._generate")
def test_pick_tool_uses_model_text(mock_generate):
    mock_generate.return_value = '{"tool":"invalid_emails"}'
    assert pick_tool("bad emails please") == "invalid_emails"
    mock_generate.assert_called()


@patch("app.agent._generate")
def test_pick_tool_retries_without_config(mock_generate):
    mock_generate.side_effect = [
        Exception("schema not supported"),
        '{"tool":"count_participants"}',
    ]
    assert pick_tool("how many people") == "count_participants"
    assert mock_generate.call_count == 2


@patch("app.agent.pick_tool", side_effect=RuntimeError("network"))
def test_route_user_query_api_error(_mock):
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        assert route_user_query("hello") == {"error": "AI unavailable"}


def test_route_user_query_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert route_user_query("hello") == {"error": "AI unavailable"}
