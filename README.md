# nowcoder-mcp

Read-only MCP server for 牛客/Nowcoder interview, resume, and job-research workflows.

`nowcoder-mcp` exposes public Nowcoder search and post-reading capabilities to MCP clients such as Hermes Agent. It is designed for research and preparation tasks: finding interview experiences, reading posts, extracting visible comments, collecting image asset URLs from resume-review posts, and building deterministic interview-prep summaries.

## Features

- Search public Nowcoder content by keyword.
- Filter by interview experiences, job progress, referrals, company reviews, or all content.
- Run batch searches for multiple companies, roles, or skill keywords.
- Fetch discuss post details by `content_id`.
- Fetch Feed details by `uuid` with lightweight HTML and SSR-state parsing.
- Extract image asset URLs from a single discuss or Feed post without OCR.
- Fetch visible discuss comments by `content_id`.
- Fetch public user profile metadata by `user_id`.
- Search interview experiences by company, role, tech stack, and year.
- Extract structured interview signals from a single discuss or Feed post.
- Analyze recurring interview topics from search results with source URLs.
- Build Feishu-friendly Markdown interview preparation reports.
- Optionally capture and reuse login state via Playwright storage state or WeChat QR login.
- Probe current login state without exposing cookies or headers.

## Non-goals

This server is read-only. It does not provide posting, commenting, liking, following, messaging, applying, or profile mutation.

It also does not run OCR. Image extraction returns image asset URLs only, so a caller can decide whether to view, download, or OCR them separately.

## Install

This project uses `uv` and Python 3.12+.

```bash
uv sync --dev
```

Run the MCP server over stdio:

```bash
uv run nowcoder-mcp serve
```

## Hermes MCP Config

Example Hermes config:

```yaml
mcp_servers:
  nowcoder:
    command: uv
    args:
      - --directory
      - /absolute/path/to/nowcoder-mcp
      - run
      - nowcoder-mcp
      - serve
    env:
      NOWCODER_AUTH_MODE: anonymous
```

After changing Hermes config, restart/reload Hermes and verify discovery:

```bash
hermes mcp test nowcoder
```

Expected discovery currently includes 17 tools, including `get_nowcoder_post_assets`.

## CLI Examples

Search Nowcoder:

```bash
uv run nowcoder-mcp smoke-search "字节跳动 Java 面经" --max-pages 1
uv run nowcoder-mcp smoke-search "AI Agent 开发 面经" --tag all --sort relevance
```

Fetch details and comments:

```bash
uv run nowcoder-mcp smoke-comments 877151327091027968
uv run nowcoder-mcp smoke-user <user_id>
```

Extract interview signals and build reports:

```bash
uv run nowcoder-mcp smoke-signals --content-id <content_id>
uv run nowcoder-mcp smoke-signals --uuid <feed_uuid>
uv run nowcoder-mcp smoke-topics "字节跳动 Java 面经" --max-posts 3
uv run nowcoder-mcp smoke-report "字节跳动 Java 面经" --max-posts 3 --markdown-only
```

Extract image assets without OCR:

```bash
uv run nowcoder-mcp smoke-assets --content-id <content_id>
uv run nowcoder-mcp smoke-assets --uuid <feed_uuid>
```

Example output shape:

```json
{
  "source_type": "feed",
  "source_id": "7cc65b74b053461893959f09b244765f",
  "title": "嵌入式三本秋招简历，求锐评",
  "url": "https://www.nowcoder.com/feed/main/detail/7cc65b74b053461893959f09b244765f",
  "images": [
    {
      "url": "https://uploadfiles.nowcoder.com/images/20251208/326127462_1765178274313/72E29057FF33329991E31137D4A1F8C7",
      "alt": "屏幕截图 2025-12-08 151739.png",
      "source": "imgMoment"
    }
  ]
}
```

Multiple images are returned in the `images` array in source order. The extractor handles discuss HTML images and Feed SSR fields such as `imgMoment` and `contentImageUrls`, including Nowcoder upload URLs without `.jpg` or `.png` suffixes.

## MCP Tools

- `search_nowcoder(query, tag="interview", sort="latest", max_pages=1, use_auth=false)`
- `batch_search_nowcoder(queries, tag="all", sort="latest", max_pages=1, use_auth=false)`
- `get_nowcoder_discuss_detail(content_id, use_auth=false)`
- `get_nowcoder_feed_detail(uuid, use_auth=false)`
- `get_nowcoder_post_assets(content_id=None, uuid=None, use_auth=false)`
- `get_nowcoder_discuss_comments(content_id, page=1, use_auth=false)`
- `get_nowcoder_user_public_profile(user_id, use_auth=false)`
- `search_nowcoder_interviews(company=None, role=None, tech_stack=None, year=None, max_pages=2)`
- `extract_nowcoder_post_signals(content_id=None, uuid=None, use_auth=false)`
- `analyze_nowcoder_interview_topics(query, max_pages=1, max_posts=5, use_auth=false)`
- `build_nowcoder_interview_report(query, max_pages=1, max_posts=5, use_auth=false)`
- `nowcoder_auth_status()`
- `nowcoder_auth_probe()`
- `nowcoder_me()`
- `nowcoder_wechat_login_qr_code(save_image=false)`
- `nowcoder_wechat_login_status(ticket, callback=None)`
- `nowcoder_wechat_login_wait(ticket, callback=None, timeout_seconds=120, interval_seconds=3.0)`

## Auth

Anonymous mode is the default and is enough for public search, public details, and public image asset extraction where Nowcoder exposes the data.

```bash
uv run nowcoder-mcp auth status
```

For authenticated reads, either capture Playwright storage state:

```bash
uv run nowcoder-mcp auth login
NOWCODER_AUTH_MODE=playwright_state uv run nowcoder-mcp auth probe
NOWCODER_AUTH_MODE=playwright_state uv run nowcoder-mcp me
```

Or use WeChat QR login:

```bash
uv run nowcoder-mcp auth wechat-qr --save-image
uv run nowcoder-mcp auth wechat-status <ticket>
uv run nowcoder-mcp auth wechat-wait <ticket>
```

Tool outputs never include raw cookies, request headers, or storage state content.

## Development

```bash
uv run pytest -q
uv run ruff check .
uv run nowcoder-mcp --help
hermes mcp test nowcoder
```

Live smoke examples used during development:

```bash
uv run nowcoder-mcp smoke-assets --uuid 7cc65b74b053461893959f09b244765f
uv run nowcoder-mcp smoke-assets --content-id 900896686346694656
```
