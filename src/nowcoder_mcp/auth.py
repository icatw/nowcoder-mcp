from __future__ import annotations

import json
import os
import stat
import time
from pathlib import Path
from typing import Any

import httpx

from .config import NowcoderConfig
from .models import AuthStatus, WechatLoginQrCode, WechatLoginStatus


class NowcoderSessionStore:
    def __init__(self, config: NowcoderConfig | None = None):
        self.config = config or NowcoderConfig.from_env()

    @property
    def state_path(self) -> Path:
        return self.config.auth_state_path

    def state_file_exists(self) -> bool:
        return self.state_path.exists()

    def ensure_state_dir(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.state_path.parent.chmod(0o700)
        except OSError:
            pass

    def save_storage_state(self, state: dict[str, Any]) -> None:
        self.ensure_state_dir()
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        self.secure_state_file()

    def secure_state_file(self) -> None:
        if self.state_path.exists():
            try:
                self.state_path.chmod(0o600)
            except OSError:
                pass

    def state_file_mode(self) -> str | None:
        if not self.state_path.exists():
            return None
        return oct(stat.S_IMODE(self.state_path.stat().st_mode))

    def clear(self) -> None:
        if self.state_path.exists():
            self.state_path.unlink()

    def cookie_header_from_env(self) -> str | None:
        value = os.getenv(self.config.cookie_env_name)
        return value.strip() if value and value.strip() else None

    def load_storage_state(self) -> dict[str, Any] | None:
        if not self.state_path.exists():
            return None
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def cookie_header_from_playwright_state(self) -> str | None:
        data = self.load_storage_state()
        if not data:
            return None
        cookies = data.get("cookies") or []
        parts: list[str] = []
        for cookie in cookies:
            if not isinstance(cookie, dict):
                continue
            domain = str(cookie.get("domain") or "")
            if "nowcoder.com" not in domain:
                continue
            name = cookie.get("name")
            value = cookie.get("value")
            if name and value is not None:
                parts.append(f"{name}={value}")
        return "; ".join(parts) if parts else None

    def cookie_header(self, use_auth: bool = False) -> str | None:
        if not use_auth:
            return None
        mode = self.config.auth_mode
        if mode == "cookie_env":
            return self.cookie_header_from_env()
        if mode == "playwright_state":
            return self.cookie_header_from_playwright_state()
        return None

    def safe_status(self, authenticated: bool | None = None, error: str | None = None) -> AuthStatus:
        mode = self.config.auth_mode
        exists = self.state_file_exists()
        has_cookie = bool(self.cookie_header(use_auth=True)) if mode != "anonymous" else False
        return AuthStatus(
            mode=mode,
            state_file_exists=exists,
            state_file_mode=self.state_file_mode(),
            authenticated=has_cookie if authenticated is None else authenticated,
            username_hint=None,
            error=error
            if error is not None
            else (None if mode == "anonymous" or has_cookie else "No usable Nowcoder auth cookie found"),
        )

    def capture_login_state(self, *, headless: bool = False, timeout_ms: int = 300_000) -> Path:
        """Open a browser for manual login and save Playwright storage state."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError("Install auth support with `uv sync --extra auth --dev`") from exc

        self.ensure_state_dir()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.nowcoder.com/", wait_until="domcontentloaded", timeout=timeout_ms)
            input("Log in to Nowcoder in the opened browser, then press Enter here to save auth state...")
            context.storage_state(path=str(self.state_path))
            browser.close()
        self.secure_state_file()
        return self.state_path

    def wechat_login_qr_code(self, *, save_image: bool = False) -> WechatLoginQrCode:
        with self._login_http_client() as client:
            response = client.get("/oauth2/login/wechat_qr_code")
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data") or {}
            result = WechatLoginQrCode(
                ticket=str(data.get("ticket") or ""),
                image_url=str(data.get("imageUrl") or ""),
                expire_second=int(data.get("expireSecond") or 0),
            )
            if save_image and result.image_url:
                result.image_path = str(self.save_wechat_qr_image(result.image_url, result.ticket, client))
            return result

    def save_wechat_qr_image(
        self, image_url: str, ticket: str, client: httpx.Client | None = None
    ) -> Path:
        self.ensure_state_dir()
        image_path = self.state_path.parent / f"wechat_login_qr_{self._safe_ticket_name(ticket)}.jpg"
        owns_client = client is None
        http = client or self._login_http_client()
        try:
            response = http.get(image_url)
            response.raise_for_status()
            image_path.write_bytes(response.content)
            try:
                image_path.chmod(0o600)
            except OSError:
                pass
            return image_path
        finally:
            if owns_client:
                http.close()

    def wechat_login_status(self, ticket: str, *, callback: str | None = None) -> WechatLoginStatus:
        with self._login_http_client() as client:
            params = {"ticket": ticket}
            if callback:
                params["callBack"] = callback
            response = client.get("/oauth2/login/wechat_mp_status", params=params)
            response.raise_for_status()
            payload = response.json()
            code = int(payload.get("code") or 0)
            message = str(payload.get("msg") or payload.get("message") or "")
            authenticated = code == 0 and self._has_nowcoder_cookie(client)
            if authenticated:
                self.save_storage_state(self._storage_state_from_client(client))
            data = payload.get("data") or {}
            return WechatLoginStatus(
                ticket=ticket,
                code=code,
                message=message,
                authenticated=authenticated,
                state_file_exists=self.state_file_exists(),
                state_file_mode=self.state_file_mode(),
                callback=str(data.get("callBack") or "") or None,
            )

    def wechat_login_wait(
        self,
        ticket: str,
        *,
        callback: str | None = None,
        timeout_seconds: int = 120,
        interval_seconds: float = 3.0,
    ) -> WechatLoginStatus:
        deadline = time.monotonic() + max(1, timeout_seconds)
        last_status: WechatLoginStatus | None = None
        while time.monotonic() <= deadline:
            last_status = self.wechat_login_status(ticket=ticket, callback=callback)
            if last_status.authenticated or last_status.code not in {1, 2}:
                return last_status
            time.sleep(max(0.5, interval_seconds))
        return last_status or WechatLoginStatus(
            ticket=ticket,
            code=-1,
            message="Timed out waiting for WeChat QR login",
        )

    def _login_http_client(self) -> httpx.Client:
        return httpx.Client(
            base_url="https://www.nowcoder.com",
            follow_redirects=True,
            timeout=self.config.timeout_seconds,
            trust_env=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.nowcoder.com/login",
            },
        )

    @staticmethod
    def _has_nowcoder_cookie(client: httpx.Client) -> bool:
        return any("nowcoder" in cookie.domain.lower() for cookie in client.cookies.jar)

    @staticmethod
    def _safe_ticket_name(ticket: str) -> str:
        safe = "".join(ch for ch in ticket if ch.isalnum())[:32]
        return safe or "unknown"

    @staticmethod
    def _storage_state_from_client(client: httpx.Client) -> dict[str, Any]:
        cookies = []
        for cookie in client.cookies.jar:
            if "nowcoder" not in cookie.domain.lower():
                continue
            cookies.append(
                {
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain,
                    "path": cookie.path,
                    "expires": cookie.expires or -1,
                    "httpOnly": bool(cookie.has_nonstandard_attr("HttpOnly")),
                    "secure": bool(cookie.secure),
                    "sameSite": "Lax",
                }
            )
        return {"cookies": cookies, "origins": []}


def redact_cookie_text(text: str) -> str:
    if not text:
        return text
    if "=" not in text:
        return "[redacted]"
    return "; ".join("[redacted]" for _ in text.split(";"))
