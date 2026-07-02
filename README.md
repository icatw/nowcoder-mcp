# nowcoder-mcp

Read-only MCP server for 牛客/Nowcoder interview and job research.

## Features

- Search Nowcoder public content by keyword.
- Filter by interview experiences, job progress, referrals, company reviews, or all content.
- Fetch discuss post details by `content_id`.
- Fetch visible discuss comments by `content_id`.
- Fetch Feed details by `uuid` with lightweight HTML parsing.
- Fetch public user profile metadata by `user_id`.
- Fetch the current logged-in user's safe profile summary.
- Actively probe whether saved login state is still valid.
- Generate WeChat QR login links, optionally save QR images locally, and wait for scan completion.
- Convenience interview search by company, role, tech stack, and year.
- Optional login state via Playwright storage state or a cookie env var; cookies are never exposed to MCP tools or logs.

## Non-goals

This server does **not** provide write operations: no posting, commenting, liking, following, messaging, applying, or profile mutation.

## Install

```bash
uv sync --dev
```

## CLI

```bash
uv run nowcoder-mcp --help
uv run nowcoder-mcp smoke-search "字节跳动 Java 面经" --max-pages 1
uv run nowcoder-mcp smoke-comments 877151327091027968
uv run nowcoder-mcp smoke-user <user_id>
NOWCODER_AUTH_MODE=playwright_state uv run nowcoder-mcp me
uv run nowcoder-mcp auth status
NOWCODER_AUTH_MODE=playwright_state uv run nowcoder-mcp auth probe
uv run nowcoder-mcp auth login
uv run nowcoder-mcp auth wechat-qr --save-image
uv run nowcoder-mcp auth wechat-status <ticket>
uv run nowcoder-mcp auth wechat-wait <ticket>
```

For authenticated reads, either set `NOWCODER_AUTH_MODE=playwright_state` after `auth login` or successful WeChat QR login, or set `NOWCODER_AUTH_MODE=cookie_env` with `NOWCODER_COOKIE` in the environment. Tool outputs never include cookie values or raw headers.

## MCP stdio

```bash
uv run nowcoder-mcp serve
```

Hermes config example is in `docs/hermes-mcp-config.md`.

## Tool list

- `search_nowcoder`
- `batch_search_nowcoder`
- `get_nowcoder_discuss_detail`
- `get_nowcoder_discuss_comments`
- `get_nowcoder_feed_detail`
- `get_nowcoder_user_public_profile`
- `search_nowcoder_interviews`
- `nowcoder_me`
- `nowcoder_auth_probe`
- `nowcoder_auth_status`
- `nowcoder_wechat_login_qr_code`
- `nowcoder_wechat_login_status`
- `nowcoder_wechat_login_wait`

## Development

```bash
uv run pytest -q
uv run ruff check .
```
