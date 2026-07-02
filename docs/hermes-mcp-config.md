# Hermes MCP Configuration

Prefer stdio for local Hermes usage.

```yaml
mcp_servers:
  nowcoder:
    command: "uv"
    args: ["--directory", "/home/ubuntu/nowcoder-mcp-plan", "run", "nowcoder-mcp", "serve"]
    env:
      NOWCODER_AUTH_MODE: "anonymous"
```

If using a saved Playwright storage state later:

```yaml
mcp_servers:
  nowcoder:
    command: "uv"
    args: ["--directory", "/home/ubuntu/nowcoder-mcp-plan", "run", "nowcoder-mcp", "serve"]
    env:
      NOWCODER_AUTH_MODE: "playwright_state"
      NOWCODER_AUTH_STATE: "/home/ubuntu/.config/nowcoder-mcp/storage_state.json"
```

After editing config:

```bash
hermes mcp test nowcoder
hermes mcp list
```

Restart Hermes or the gateway for newly discovered MCP tools to appear.
