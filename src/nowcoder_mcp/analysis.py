from __future__ import annotations

import re
from collections.abc import Iterable

from .models import (
    DiscussDetail,
    ExtractedSignal,
    FeedDetail,
    InterviewTopicsAnalysis,
    InterviewReport,
    PostSignals,
    SourceReference,
    TopicAggregate,
    TopicSource,
)

TECH_KEYWORDS = [
    "Java",
    "Go",
    "Python",
    "C++",
    "JavaScript",
    "TypeScript",
    "Spring",
    "Spring Boot",
    "MySQL",
    "Redis",
    "Kafka",
    "RocketMQ",
    "RabbitMQ",
    "Elasticsearch",
    "Docker",
    "Kubernetes",
    "K8s",
    "Linux",
    "Nginx",
    "HTTP",
    "TCP",
    "RPC",
    "微服务",
    "分布式",
    "缓存",
    "消息队列",
    "数据库",
    "索引",
]

ROLE_KEYWORDS = [
    "后端",
    "后台",
    "Java开发",
    "Go开发",
    "客户端",
    "前端",
    "测开",
    "测试开发",
    "算法",
    "数据开发",
    "AI",
    "Agent",
]

ROUND_PATTERNS = [
    ("一面", r"(?<![二三四终])一面|1\s*面|初面"),
    ("二面", r"二面|2\s*面"),
    ("三面", r"三面|3\s*面"),
    ("四面", r"四面|4\s*面"),
    ("HR面", r"HR\s*面|hr\s*面|人事面"),
    ("终面", r"终面|主管面|leader\s*面|总监面"),
]

ALGORITHM_PATTERNS = [
    ("算法题", r"算法|手撕|力扣|leetcode|LeetCode|代码题"),
    ("链表", r"链表|反转链表|环形链表"),
    ("二叉树", r"二叉树|树的遍历|前序|中序|后序"),
    ("动态规划", r"动态规划|\bdp\b|DP"),
    ("排序", r"排序|快排|归并|堆排"),
    ("数组/字符串", r"数组|字符串|双指针|滑动窗口"),
]

SYSTEM_DESIGN_PATTERNS = [
    ("系统设计", r"系统设计|设计一个|架构设计"),
    ("高并发", r"高并发|QPS|并发|限流|削峰"),
    ("缓存设计", r"缓存|Redis|缓存穿透|缓存击穿|缓存雪崩"),
    ("消息队列", r"消息队列|Kafka|RocketMQ|RabbitMQ|异步"),
    ("数据库设计", r"数据库设计|分库分表|索引|事务|MySQL"),
]

PROJECT_PATTERNS = [
    ("项目介绍", r"项目|实习|经历|做过|负责"),
    ("项目难点", r"难点|挑战|优化|瓶颈|问题"),
    ("项目追问", r"追问|深挖|为什么|怎么实现|如何保证"),
]

BEHAVIORAL_PATTERNS = [
    ("自我介绍", r"自我介绍|介绍一下自己"),
    ("职业规划", r"职业规划|未来规划|为什么选择"),
    ("优缺点", r"优点|缺点|优势|不足"),
]

PROCESS_PATTERNS = [
    ("流程时间", r"流程|时间线|多久|几天|约面|电话"),
    ("笔试", r"笔试|测评|性格测试"),
    ("OC", r"\bOC\b|oc|offer|意向书"),
]

RESULT_PATTERNS = [
    ("已过", r"已过|通过|oc|OC|offer|意向书|上岸"),
    ("挂了", r"挂|凉|拒|感谢信"),
    ("等待中", r"等通知|泡池|池子|pending|流程中"),
]

ADVICE_PATTERNS = [
    ("复习建议", r"建议|准备|复习|重点|一定要|需要掌握"),
    ("八股准备", r"八股|基础|原理|源码"),
]

QUESTION_RE = re.compile(r"[？?]|(^|[\n。；;])\s*(问|Q[:：]|问题|题目)", re.MULTILINE)


def extract_post_signals(detail: DiscussDetail | FeedDetail) -> PostSignals:
    text = _normalize_text(f"{detail.title}\n{detail.content}")
    source = _source_from_detail(detail)
    return PostSignals(
        source=source,
        interview_rounds=_find_pattern_signals(text, ROUND_PATTERNS, 0.9),
        roles=_find_keyword_signals(text, ROLE_KEYWORDS, "role", 0.78),
        tech_stack=_find_keyword_signals(text, TECH_KEYWORDS, "tech", 0.74),
        algorithms=_find_pattern_signals(text, ALGORITHM_PATTERNS, 0.76),
        system_design=_find_pattern_signals(text, SYSTEM_DESIGN_PATTERNS, 0.78),
        project_deep_dive=_find_pattern_signals(text, PROJECT_PATTERNS, 0.72),
        behavioral=_find_pattern_signals(text, BEHAVIORAL_PATTERNS, 0.72),
        process=_find_pattern_signals(text, PROCESS_PATTERNS, 0.7),
        result_status=_find_pattern_signals(text, RESULT_PATTERNS, 0.76),
        preparation_advice=_find_pattern_signals(text, ADVICE_PATTERNS, 0.68),
        question_count=len(QUESTION_RE.findall(text)),
        raw_excerpt=text[:1200],
    )


def _source_from_detail(detail: DiscussDetail | FeedDetail) -> SourceReference:
    if isinstance(detail, DiscussDetail):
        return SourceReference(
            source_type="discuss",
            source_id=detail.content_id,
            title=detail.title,
            url=detail.url,
        )
    return SourceReference(
        source_type="feed",
        source_id=detail.uuid,
        title=detail.title,
        url=detail.url,
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def _find_keyword_signals(
    text: str,
    keywords: Iterable[str],
    label: str,
    confidence: float,
) -> list[ExtractedSignal]:
    signals: list[ExtractedSignal] = []
    seen: set[str] = set()
    for keyword in keywords:
        pattern = re.escape(keyword)
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match or keyword.lower() in seen:
            continue
        seen.add(keyword.lower())
        signals.append(
            ExtractedSignal(
                label=label,
                value=keyword,
                confidence=confidence,
                evidence=_evidence_window(text, match.start(), match.end()),
            )
        )
    return signals


def _find_pattern_signals(
    text: str,
    patterns: Iterable[tuple[str, str]],
    confidence: float,
) -> list[ExtractedSignal]:
    signals: list[ExtractedSignal] = []
    seen: set[str] = set()
    for label, pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match or label in seen:
            continue
        seen.add(label)
        signals.append(
            ExtractedSignal(
                label=label,
                value=match.group(0),
                confidence=confidence,
                evidence=_evidence_window(text, match.start(), match.end()),
            )
        )
    return signals


def _evidence_window(text: str, start: int, end: int, radius: int = 70) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return text[left:right].replace("\n", " ").strip()


def aggregate_interview_topics(
    query: str,
    posts: list[PostSignals],
    total_search_results: int = 0,
    skipped_records: int = 0,
    max_topics: int = 10,
    max_sources_per_topic: int = 5,
) -> InterviewTopicsAnalysis:
    return InterviewTopicsAnalysis(
        query=query,
        fetched_posts=len(posts),
        skipped_records=skipped_records,
        total_search_results=total_search_results,
        high_frequency_topics=_aggregate_signal_groups(
            posts,
            ["tech_stack", "algorithms", "system_design", "project_deep_dive"],
            max_topics=max_topics,
            max_sources_per_topic=max_sources_per_topic,
        ),
        project_deep_dive=_aggregate_signal_groups(
            posts,
            ["project_deep_dive"],
            max_topics=max_topics,
            max_sources_per_topic=max_sources_per_topic,
        ),
        algorithms=_aggregate_signal_groups(
            posts,
            ["algorithms"],
            max_topics=max_topics,
            max_sources_per_topic=max_sources_per_topic,
        ),
        system_design=_aggregate_signal_groups(
            posts,
            ["system_design"],
            max_topics=max_topics,
            max_sources_per_topic=max_sources_per_topic,
        ),
        source_posts=[post.source for post in posts],
    )


def _aggregate_signal_groups(
    posts: list[PostSignals],
    fields: list[str],
    max_topics: int,
    max_sources_per_topic: int,
) -> list[TopicAggregate]:
    by_topic: dict[str, TopicAggregate] = {}
    seen_sources: dict[str, set[str]] = {}
    for post in posts:
        for field in fields:
            for signal in getattr(post, field):
                topic = _topic_name(signal)
                source_key = post.source.url
                aggregate = by_topic.setdefault(topic, TopicAggregate(topic=topic))
                source_keys = seen_sources.setdefault(topic, set())
                if source_key in source_keys:
                    continue
                source_keys.add(source_key)
                aggregate.count += 1
                if len(aggregate.sources) < max_sources_per_topic:
                    aggregate.sources.append(
                        TopicSource(
                            title=post.source.title,
                            url=post.source.url,
                            evidence=signal.evidence,
                        )
                    )
    return sorted(by_topic.values(), key=lambda item: (-item.count, item.topic))[:max_topics]


def _topic_name(signal: ExtractedSignal) -> str:
    if signal.label in {"tech", "role"}:
        return signal.value
    return signal.label


def build_interview_report(analysis: InterviewTopicsAnalysis) -> InterviewReport:
    lines: list[str] = [
        f"# 牛客面经准备报告：{analysis.query}",
        "",
        "## 概览",
        f"- 搜索结果总数：{analysis.total_search_results}",
        f"- 已抓取可分析帖子：{analysis.fetched_posts}",
        f"- 已跳过记录：{analysis.skipped_records}",
        "- 说明：以下内容来自牛客公开帖子，属于候选人经验样本，不代表官方招聘要求。",
        "",
    ]
    lines.extend(_topic_section("## 高频技术题", analysis.high_frequency_topics))
    lines.extend(_topic_section("## 项目深挖", analysis.project_deep_dive))
    lines.extend(_topic_section("## 算法准备", analysis.algorithms))
    lines.extend(_topic_section("## 系统设计", analysis.system_design))
    lines.extend(_action_checklist(analysis))
    lines.extend(_source_section(analysis))
    markdown = "\n".join(lines).strip() + "\n"
    return InterviewReport(query=analysis.query, markdown=markdown, analysis=analysis)


def _topic_section(title: str, topics: list[TopicAggregate]) -> list[str]:
    lines = [title]
    if not topics:
        return [*lines, "- 暂无稳定信号。", ""]
    for topic in topics:
        lines.append(f"- **{topic.topic}**：出现 {topic.count} 次")
        for source in topic.sources[:3]:
            title_text = source.title or source.url
            evidence = _compact_text(source.evidence, 110)
            lines.append(f"  - 来源：[{title_text}]({source.url})")
            if evidence:
                lines.append(f"  - 证据：{evidence}")
    lines.append("")
    return lines


def _action_checklist(analysis: InterviewTopicsAnalysis) -> list[str]:
    topics = [topic.topic for topic in analysis.high_frequency_topics[:6]]
    algorithms = [topic.topic for topic in analysis.algorithms[:4]]
    system_design = [topic.topic for topic in analysis.system_design[:4]]
    project_topics = [topic.topic for topic in analysis.project_deep_dive[:4]]
    lines = ["## 准备清单"]
    if topics:
        lines.append(f"- 先复盘高频基础：{'、'.join(topics)}。")
    if project_topics:
        lines.append(f"- 准备项目追问：{'、'.join(project_topics)}，每项都要能讲背景、方案、取舍和结果。")
    if algorithms:
        lines.append(f"- 算法练习优先级：{'、'.join(algorithms)}，准备口述复杂度和边界条件。")
    if system_design:
        lines.append(f"- 系统设计准备：{'、'.join(system_design)}，重点讲容量、瓶颈、降级和一致性。")
    if not any([topics, project_topics, algorithms, system_design]):
        lines.append("- 当前样本不足，建议增加 `max_posts` 或换更具体的公司/岗位关键词。")
    return [*lines, ""]


def _source_section(analysis: InterviewTopicsAnalysis) -> list[str]:
    lines = ["## 来源帖子"]
    if not analysis.source_posts:
        return [*lines, "- 暂无可分析来源。", ""]
    for source in analysis.source_posts:
        title = source.title or source.url
        lines.append(f"- [{title}]({source.url})")
    lines.append("")
    return lines


def _compact_text(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"
