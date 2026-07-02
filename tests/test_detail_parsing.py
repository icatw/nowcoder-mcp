from pathlib import Path

import respx
from httpx import Response

from nowcoder_mcp.client import NOWCODER_DISCUSS_DETAIL_URL, NOWCODER_FEED_URL, NowcoderClient
from nowcoder_mcp.server import extract_nowcoder_post_signals


def test_discuss_detail_converts_html_to_text():
    fixture = Path("tests/fixtures/discuss_detail_response.json").read_text()
    with respx.mock:
        respx.get(f"{NOWCODER_DISCUSS_DETAIL_URL}/12345").mock(return_value=Response(200, content=fixture))
        client = NowcoderClient()
        detail = client.get_discuss_detail("12345")

    assert detail.title == "讨论帖标题"
    assert "第一行" in detail.content
    assert "第二行 & 内容" in detail.content
    assert detail.url.endswith("/discuss/12345")


def test_feed_detail_extracts_visible_content():
    fixture = Path("tests/fixtures/feed_detail.html").read_text()
    with respx.mock:
        respx.get(f"{NOWCODER_FEED_URL}/abc-uuid").mock(return_value=Response(200, text=fixture))
        client = NowcoderClient()
        detail = client.get_feed_detail("abc-uuid")

    assert detail.uuid == "abc-uuid"
    assert detail.title == "Feed标题"
    assert "Feed 第一行" in detail.content
    assert "Feed 第二行" in detail.content


def test_client_extract_post_signals_reuses_discuss_detail():
    fixture = Path("tests/fixtures/discuss_detail_response.json").read_text()
    with respx.mock:
        respx.get(f"{NOWCODER_DISCUSS_DETAIL_URL}/12345").mock(return_value=Response(200, content=fixture))
        client = NowcoderClient()
        signals = client.extract_post_signals(content_id="12345")

    assert signals.source.source_type == "discuss"
    assert signals.source.source_id == "12345"
    assert signals.raw_excerpt


def test_extract_post_signals_tool_returns_jsonable_dict():
    fixture = Path("tests/fixtures/discuss_detail_response.json").read_text()
    with respx.mock:
        respx.get(f"{NOWCODER_DISCUSS_DETAIL_URL}/12345").mock(return_value=Response(200, content=fixture))
        result = extract_nowcoder_post_signals(content_id="12345")

    assert result["source"]["source_type"] == "discuss"
    assert result["source"]["source_id"] == "12345"
    assert "raw_excerpt" in result
