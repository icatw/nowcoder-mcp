from pathlib import Path

import respx
from httpx import Response

from nowcoder_mcp.client import NOWCODER_DISCUSS_DETAIL_URL, NOWCODER_FEED_URL, NowcoderClient
from nowcoder_mcp.server import (
    analyze_nowcoder_interview_topics,
    build_nowcoder_interview_report,
    extract_nowcoder_post_signals,
    get_nowcoder_post_assets,
)


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


def test_discuss_assets_extracts_images_from_rich_text():
    fixture = (
        '{"success":true,"data":{"title":"带图帖子","richText":"'
        '<p>简历</p><img src=\\"//uploadfiles.nowcoder.com/resume.png\\" alt=\\"简历图\\">'
        '<img data-src=\\"https://static.nowcoder.com/dup.jpg\\">'
        '<img src=\\"https://static.nowcoder.com/dup.jpg\\">'
        '"}}'
    )
    with respx.mock:
        respx.get(f"{NOWCODER_DISCUSS_DETAIL_URL}/with-images").mock(
            return_value=Response(200, content=fixture)
        )
        client = NowcoderClient()
        assets = client.get_discuss_assets("with-images")

    assert assets.source_type == "discuss"
    assert assets.title == "带图帖子"
    assert [image.url for image in assets.images] == [
        "https://uploadfiles.nowcoder.com/resume.png",
        "https://static.nowcoder.com/dup.jpg",
    ]
    assert assets.images[0].alt == "简历图"


def test_feed_assets_extracts_img_and_embedded_json_images():
    html = """
    <html><head><script>window.__DATA__={"title":"Feed标题","imageUrl":"https://img.nowcoder.com/a.webp","imgMoment":[{"src":"https:\\/\\/uploadfiles.nowcoder.com\\/images\\/20260627\\/1_2\\/ABCDEF"}]}</script></head>
    <body><div class="feed-content-text"><p>正文</p><img data-original="/relative.jpg" alt="相对图"></div></body></html>
    """
    with respx.mock:
        respx.get(f"{NOWCODER_FEED_URL}/image-feed").mock(return_value=Response(200, text=html))
        client = NowcoderClient()
        assets = client.get_feed_assets("image-feed")

    assert assets.source_type == "feed"
    assert assets.title == "Feed标题"
    assert [image.url for image in assets.images] == [
        "https://www.nowcoder.com/relative.jpg",
        "https://img.nowcoder.com/a.webp",
        "https://uploadfiles.nowcoder.com/images/20260627/1_2/ABCDEF",
    ]


def test_feed_assets_prefers_current_post_initial_state_images():
    html = """
    <html><body>
      <img src="https://static.nowcoder.com/logo.png">
      <script>window.__INITIAL_STATE__={"prefetchData":{"2":{"ssrCommonData":{"contentData":{"uuid":"target-feed","title":"目标帖","imgMoment":[{"src":"https:\\/\\/uploadfiles.nowcoder.com\\/images\\/20260627\\/1_2\\/RESUME","alt":"简历"}]}}}}};</script>
    </body></html>
    """
    with respx.mock:
        respx.get(f"{NOWCODER_FEED_URL}/target-feed").mock(return_value=Response(200, text=html))
        client = NowcoderClient()
        assets = client.get_feed_assets("target-feed")

    assert assets.title == "目标帖"
    assert [image.url for image in assets.images] == [
        "https://uploadfiles.nowcoder.com/images/20260627/1_2/RESUME"
    ]
    assert assets.images[0].source == "imgMoment"


def test_get_post_assets_requires_exactly_one_identifier():
    client = NowcoderClient()
    try:
        client.get_post_assets()
    except ValueError as exc:
        assert "exactly one" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_get_post_assets_tool_returns_jsonable_dict():
    fixture = (
        '{"success":true,"data":{"title":"带图帖子","richText":"'
        '<img src=\\"https://static.nowcoder.com/resume.jpg\\">'
        '"}}'
    )
    with respx.mock:
        respx.get(f"{NOWCODER_DISCUSS_DETAIL_URL}/with-images").mock(
            return_value=Response(200, content=fixture)
        )
        result = get_nowcoder_post_assets(content_id="with-images")

    assert result["source_type"] == "discuss"
    assert result["images"][0]["url"] == "https://static.nowcoder.com/resume.jpg"


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


def test_client_analyze_interview_topics_fetches_discuss_sources_only():
    search_fixture = Path("tests/fixtures/search_response.json").read_text()
    detail_fixture = Path("tests/fixtures/discuss_detail_response.json").read_text()
    with respx.mock:
        respx.post("https://gw-c.nowcoder.com/api/sparta/pc/search").mock(
            return_value=Response(200, content=search_fixture)
        )
        respx.get(f"{NOWCODER_DISCUSS_DETAIL_URL}/12345").mock(
            return_value=Response(200, content=detail_fixture)
        )
        client = NowcoderClient()
        result = client.analyze_interview_topics("字节 Java 面经", max_posts=3)

    assert result.query == "字节 Java 面经"
    assert result.fetched_posts == 1
    assert result.skipped_records == 1
    assert result.source_posts[0].url.endswith("/discuss/12345")
    assert all(source.url for topic in result.high_frequency_topics for source in topic.sources)


def test_analyze_interview_topics_tool_returns_jsonable_dict():
    search_fixture = Path("tests/fixtures/search_response.json").read_text()
    detail_fixture = Path("tests/fixtures/discuss_detail_response.json").read_text()
    with respx.mock:
        respx.post("https://gw-c.nowcoder.com/api/sparta/pc/search").mock(
            return_value=Response(200, content=search_fixture)
        )
        respx.get(f"{NOWCODER_DISCUSS_DETAIL_URL}/12345").mock(
            return_value=Response(200, content=detail_fixture)
        )
        result = analyze_nowcoder_interview_topics("字节 Java 面经", max_posts=3)

    assert result["fetched_posts"] == 1
    assert result["skipped_records"] == 1
    assert result["source_posts"][0]["url"].endswith("/discuss/12345")


def test_client_build_interview_report_returns_markdown():
    search_fixture = Path("tests/fixtures/search_response.json").read_text()
    detail_fixture = Path("tests/fixtures/discuss_detail_response.json").read_text()
    with respx.mock:
        respx.post("https://gw-c.nowcoder.com/api/sparta/pc/search").mock(
            return_value=Response(200, content=search_fixture)
        )
        respx.get(f"{NOWCODER_DISCUSS_DETAIL_URL}/12345").mock(
            return_value=Response(200, content=detail_fixture)
        )
        client = NowcoderClient()
        report = client.build_interview_report("字节 Java 面经", max_posts=3)

    assert report.markdown.startswith("# 牛客面经准备报告：字节 Java 面经")
    assert report.analysis.fetched_posts == 1
    assert "https://www.nowcoder.com/discuss/12345" in report.markdown


def test_build_interview_report_tool_returns_markdown_and_analysis():
    search_fixture = Path("tests/fixtures/search_response.json").read_text()
    detail_fixture = Path("tests/fixtures/discuss_detail_response.json").read_text()
    with respx.mock:
        respx.post("https://gw-c.nowcoder.com/api/sparta/pc/search").mock(
            return_value=Response(200, content=search_fixture)
        )
        respx.get(f"{NOWCODER_DISCUSS_DETAIL_URL}/12345").mock(
            return_value=Response(200, content=detail_fixture)
        )
        result = build_nowcoder_interview_report("字节 Java 面经", max_posts=3)

    assert result["query"] == "字节 Java 面经"
    assert result["analysis"]["fetched_posts"] == 1
    assert result["markdown"].startswith("# 牛客面经准备报告：字节 Java 面经")
    assert "|" not in result["markdown"]
