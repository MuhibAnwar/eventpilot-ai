from app.agent import ALLOWED_TOOLS, extract_tool_from_text


def test_validate_tool_name_allowlist():
    assert extract_tool_from_text('{"tool":"invalid_emails"}') == "invalid_emails"
    assert extract_tool_from_text('{"tool":"DROP TABLE"}') == "none"
    assert set(ALLOWED_TOOLS) == {
        "show_all",
        "invalid_emails",
        "find_duplicates",
        "count_participants",
        "none",
    }
