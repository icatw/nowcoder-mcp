from pathlib import Path

import respx
from httpx import Response

from nowcoder_mcp.client import NOWCODER_SEARCH_URL, NowcoderClient
from nowcoder_mcp.models import Tag


def test_search_parses_discuss_and_feed_records():
    fixture = Path("tests/fixtures/search_response.json").read_text()
    with respx.mock:
        respx.post(NOWCODER_SEARCH_URL).mock(return_value=Response(200, content=fixture))
        client = NowcoderClient()
        result = client.search("字节 Java 面经", tag=Tag.interview, max_pages=1)

    assert result.total == 2
    assert len(result.records) == 2
    first = result.records[0]
    assert first.content_id == "12345"
    assert first.company == "字节跳动"
    assert first.url.endswith("/discuss/12345")
    second = result.records[1]
    assert second.uuid == "abc-uuid"
    assert second.url.endswith("/feed/main/detail/abc-uuid")
