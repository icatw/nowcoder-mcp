# Auth Model

Default mode is anonymous. Public search and public details do not require login.

Supported modes:

- `anonymous`: no cookies used.
- `cookie_env`: reads a cookie string from `NOWCODER_COOKIE`.
- `playwright_state`: reads cookies from a Playwright `storage_state.json` file.

Security rules:

- Never provide username/password to the agent.
- QR login may return a short-lived WeChat QR image URL, ticket, and optional local image path to the user; it must not return cookies, headers, or storage state.
- Never return cookies, headers, or storage state in MCP tool results.
- Never store cookie values in Hermes config. Store only the state file path.
- Keep storage state file permissions at `0600` when writing login capture later.
- Write operations are intentionally excluded from this MCP server.

Login capture options:

- `auth login` opens a browser and saves Playwright storage state after manual login.
- `auth wechat-qr --save-image` returns a short-lived WeChat QR login image URL, ticket, and optional local image file.
- `auth wechat-status <ticket>` polls the ticket once; after success it saves local storage state and still does not print cookie values.
- `auth wechat-wait <ticket>` polls until scan success, failure, or timeout.
- `auth probe` visits the logged-in profile page and returns a safe current-user summary when auth is valid.
- `me` returns the safe current-user summary; it requires `NOWCODER_AUTH_MODE=playwright_state` or `cookie_env`.
