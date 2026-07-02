from pathlib import Path

import respx
from httpx import Response

from nowcoder_mcp.client import NOWCODER_DISCUSS_DETAIL_URL, NOWCODER_FEED_URL, NowcoderClient


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
