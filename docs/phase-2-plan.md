# Phase 2 Plan

Goal: turn the read-only Nowcoder MCP primitives into higher-level job research and interview-prep workflows while keeping the server safe, source-backed, and read-only.

## Scope

Phase 2 should add analysis-oriented tools on top of existing search/detail APIs. The MCP should still avoid posting, liking, following, messaging, applying, profile mutation, or exposing private account data.

## Proposed Tools

1. `analyze_nowcoder_interview_topics`

   Search and fetch high-signal interview posts for a company/role, then extract recurring topics, technologies, project-deep-dive prompts, algorithms, system design prompts, and behavioral/process signals.

2. `compare_nowcoder_company_roles`

   Run a matrix search for multiple companies and roles, then summarize hit counts, representative posts, freshness, common requirements, and risk/noise notes.

3. `build_nowcoder_interview_report`

   Generate a structured Markdown-ready report from search results and fetched details. Include source URLs, dates when available, uncertainty labels, and a preparation checklist.

4. `extract_nowcoder_post_signals`

   Given a `content_id` or feed `uuid`, classify a single post into structured signals: interview round, role, tech stack, question list, project questions, result status, and preparation advice.

5. `track_nowcoder_job_progress_signals`

   Search 求职进度 / OC / 泡池 / 感谢信 posts for a target company and summarize timeline patterns. Treat all posts as anecdotal, not authoritative hiring policy.

## Implementation Notes

- Reuse `NowcoderClient`; do not duplicate HTTP calls in analysis modules.
- Add a dedicated `analysis.py` module for deterministic extraction, scoring, deduplication, and report shaping.
- Keep LLM-dependent interpretation outside the MCP server unless a clear local deterministic prompt/adapter is added later. The MCP should return structured evidence that Hermes can summarize.
- Add input caps: max queries, max posts fetched, max content length per post, and max total report sources.
- Preserve source provenance on every derived signal.
- Avoid fabricating missing metadata. If company, role, round, or result cannot be extracted, return `null` or low-confidence notes.

## Verification

- Unit tests for extraction from fixed fixtures.
- Mocked tests for multi-query orchestration and deduplication.
- CLI smoke commands for each new workflow.
- Live smoke against one company/role target, verifying nonzero sources and source URLs.
- Privacy regression tests asserting no cookies, headers, or storage state appear in outputs.

## Suggested Milestones

1. Add data models and deterministic single-post extraction.
2. Add multi-result analysis and topic aggregation.
3. Add report builder and CLI smoke commands.
4. Add MCP tool wrappers and tests.
5. Update README, docs, and `nowcoder-job-research` skill.
