from pathlib import Path

import respx
from httpx import Response

from nowcoder_mcp.client import NOWCODER_DISCUSS_URL, NOWCODER_SEARCH_URL
from nowcoder_mcp.server import (
    get_nowcoder_discuss_comments,
    nowcoder_auth_probe,
    nowcoder_auth_status,
    nowcoder_me,
    search_nowcoder,
)


def test_search_tool_returns_jsonable_dict():
    fixture = Path("tests/fixtures/search_response.json").read_text()
    with respx.mock:
        respx.post(NOWCODER_SEARCH_URL).mock(return_value=Response(200, content=fixture))
        result = search_nowcoder("字节 Java 面经", max_pages=1)

    assert isinstance(result, dict)
    assert result["total"] == 2
    assert result["records"][0]["content_id"] == "12345"


def test_auth_status_tool_does_not_expose_cookie(monkeypatch):
    monkeypatch.setenv("NOWCODER_AUTH_MODE", "cookie_env")
    monkeypatch.setenv("NOWCODER_COOKIE", "NOWCODERUID=secret")
    result = nowcoder_auth_status()
    assert result["authenticated"] is True
    assert "secret" not in str(result)


def test_discuss_comments_tool_returns_jsonable_dict():
    html = '<div class="comment-item" data-comment-id="7">评论内容</div>'
    with respx.mock:
        respx.get(f"{NOWCODER_DISCUSS_URL}/12345").mock(return_value=Response(200, text=html))
        result = get_nowcoder_discuss_comments("12345")

    assert result["content_id"] == "12345"
    assert result["comments"][0]["comment_id"] == "7"


def test_me_tool_returns_safe_current_user(monkeypatch):
    monkeypatch.setenv("NOWCODER_AUTH_MODE", "cookie_env")
    monkeypatch.setenv("NOWCODER_COOKIE", "NOWCODERUID=secret")
    html = '{"rawNickname":"鹿满川"}'
    with respx.mock:
        respx.get("https://www.nowcoder.com/profile").mock(
            return_value=Response(200, text=html, headers={"location": "https://www.nowcoder.com/users/376305945"})
        )
        result = nowcoder_me()

    assert result["authenticated"] is True
    assert result["nickname"] == "鹿满川"
    assert "secret" not in str(result)


def test_auth_probe_tool_never_exposes_cookie(monkeypatch):
    monkeypatch.setenv("NOWCODER_AUTH_MODE", "cookie_env")
    monkeypatch.setenv("NOWCODER_COOKIE", "NOWCODERUID=secret")
    with respx.mock:
        respx.get("https://www.nowcoder.com/profile").mock(
            return_value=Response(200, text='{"nickname":"鹿满川"}')
        )
        result = nowcoder_auth_probe()

    assert result["cookie_available"] is True
    assert "secret" not in str(result)
