from nowcoder_mcp.analysis import extract_post_signals
from nowcoder_mcp.models import DiscussDetail, FeedDetail


def test_extract_discuss_post_signals_detects_interview_topics():
    detail = DiscussDetail(
        content_id="12345",
        title="字节后端 Java 一面面经 已OC",
        content="自我介绍后问了 Java、Redis 缓存穿透、MySQL 索引、Kafka。手撕链表，项目深挖如何保证高并发。建议复习八股和项目难点。",
        url="https://www.nowcoder.com/discuss/12345",
    )

    result = extract_post_signals(detail)

    assert result.source.source_type == "discuss"
    assert result.source.source_id == "12345"
    assert [signal.value for signal in result.tech_stack] >= ["Java"]
    assert any(signal.label == "一面" for signal in result.interview_rounds)
    assert any(signal.label == "链表" for signal in result.algorithms)
    assert any(signal.label == "高并发" for signal in result.system_design)
    assert any(signal.label == "自我介绍" for signal in result.behavioral)
    assert any(signal.label == "复习建议" for signal in result.preparation_advice)
    assert any(signal.label == "OC" or signal.value.lower() == "oc" for signal in result.process)
    assert result.raw_excerpt


def test_extract_feed_post_signals_keeps_feed_source():
    detail = FeedDetail(
        uuid="abc",
        title="客户端二面",
        content="二面主要问项目经历、为什么这么设计、排序算法和职业规划。",
        url="https://www.nowcoder.com/feed/main/detail/abc",
    )

    result = extract_post_signals(detail)

    assert result.source.source_type == "feed"
    assert result.source.source_id == "abc"
    assert any(signal.label == "二面" for signal in result.interview_rounds)
    assert any(signal.value == "客户端" for signal in result.roles)
