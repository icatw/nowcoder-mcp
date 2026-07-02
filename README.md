# nowcoder-mcp

`nowcoder-mcp` 是一个只读的牛客（Nowcoder）MCP 服务，用于面经检索、简历参考、求职调研和面试准备。

它把牛客公开搜索、帖子详情、评论、图片资源提取和面经分析能力暴露给 Hermes Agent 等 MCP 客户端。典型用途包括：搜索某公司/岗位面经、读取帖子正文、从简历求锐评帖子里提取简历图片 URL、汇总高频面试主题、生成面试准备报告。

## 功能

- 按关键词搜索牛客公开内容。
- 支持按面经、求职进度、内推、公司评价或全部内容过滤。
- 支持批量搜索多个公司、岗位或技术关键词。
- 通过 `content_id` 获取 discuss 文章详情。
- 通过 `uuid` 获取 Feed 动态详情，支持轻量 HTML 和 SSR 状态解析。
- 从单篇 discuss 或 Feed 帖子中提取图片资源 URL，不做 OCR。
- 获取 discuss 帖子的可见评论。
- 获取公开用户主页元信息。
- 按公司、岗位、技术栈、年份搜索面经。
- 从单篇帖子中抽取结构化面试信号。
- 从搜索结果中聚合高频面试主题，并保留来源链接。
- 生成适合飞书阅读的 Markdown 面试准备报告。
- 可选使用 Playwright storage state 或微信扫码登录复用登录态。
- 可安全检查登录状态，不输出 cookie、header 或 storage state。

## 非目标

本项目保持只读，不提供发帖、评论、点赞、关注、私信、投递、修改个人资料等写操作。

本项目不做 OCR。图片提取只返回图片资源 URL，调用方可以按需要自行查看、下载或交给其他 OCR/视觉工具处理。

## 安装

项目使用 `uv` 和 Python 3.12+。

```bash
uv sync --dev
```

启动 stdio MCP 服务：

```bash
uv run nowcoder-mcp serve
```

## Hermes MCP 配置

示例配置：

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

修改 Hermes 配置后，重启或重载 Hermes，并验证工具发现：

```bash
hermes mcp test nowcoder
```

当前预期能发现 17 个工具，包括 `get_nowcoder_post_assets`。

## CLI 示例

搜索牛客内容：

```bash
uv run nowcoder-mcp smoke-search "字节跳动 Java 面经" --max-pages 1
uv run nowcoder-mcp smoke-search "AI Agent 开发 面经" --tag all --sort relevance
```

读取详情和评论：

```bash
uv run nowcoder-mcp smoke-comments 877151327091027968
uv run nowcoder-mcp smoke-user <user_id>
```

抽取面试信号并生成报告：

```bash
uv run nowcoder-mcp smoke-signals --content-id <content_id>
uv run nowcoder-mcp smoke-signals --uuid <feed_uuid>
uv run nowcoder-mcp smoke-topics "字节跳动 Java 面经" --max-posts 3
uv run nowcoder-mcp smoke-report "字节跳动 Java 面经" --max-posts 3 --markdown-only
```

提取图片资源，不做 OCR：

```bash
uv run nowcoder-mcp smoke-assets --content-id <content_id>
uv run nowcoder-mcp smoke-assets --uuid <feed_uuid>
```

返回示例：

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

如果一篇帖子有多张图片，会按来源顺序全部放在 `images` 数组里返回。提取器支持 discuss 正文 HTML 图片，也支持 Feed SSR 字段，例如 `imgMoment`、`contentImageUrls`。牛客上传图片有时没有 `.jpg` 或 `.png` 后缀，也会被正常识别。

## MCP 工具

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

## 登录态

匿名模式是默认模式。对于牛客公开暴露的数据，匿名模式足够完成搜索、详情读取和图片资源提取。

```bash
uv run nowcoder-mcp auth status
```

如果需要登录态读取，可以用浏览器捕获 Playwright storage state：

```bash
uv run nowcoder-mcp auth login
NOWCODER_AUTH_MODE=playwright_state uv run nowcoder-mcp auth probe
NOWCODER_AUTH_MODE=playwright_state uv run nowcoder-mcp me
```

也可以使用微信扫码登录：

```bash
uv run nowcoder-mcp auth wechat-qr --save-image
uv run nowcoder-mcp auth wechat-status <ticket>
uv run nowcoder-mcp auth wechat-wait <ticket>
```

所有工具输出都不会包含原始 cookie、请求 header 或 storage state 内容。

## 开发

```bash
uv run pytest -q
uv run ruff check .
uv run nowcoder-mcp --help
hermes mcp test nowcoder
```

开发时使用过的真实 smoke 示例：

```bash
uv run nowcoder-mcp smoke-assets --uuid 7cc65b74b053461893959f09b244765f
uv run nowcoder-mcp smoke-assets --content-id 900896686346694656
```
