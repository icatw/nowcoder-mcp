import json

import respx
from httpx import Response

from nowcoder_mcp.auth import NowcoderSessionStore, redact_cookie_text
from nowcoder_mcp.config import NowcoderConfig


def test_playwright_state_extracts_only_nowcoder_cookies(tmp_path):
    state = {
        "cookies": [
            {"domain": ".nowcoder.com", "name": "NOWCODERUID", "value": "secret"},
            {"domain": ".example.com", "name": "OTHER", "value": "leak"},
        ]
    }
    state_path = tmp_path / "storage_state.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    store = NowcoderSessionStore(NowcoderConfig(auth_mode="playwright_state", auth_state_path=state_path))

    assert store.cookie_header(use_auth=True) == "NOWCODERUID=secret"
    status = store.safe_status()
    assert status.authenticated is True
    assert "secret" not in status.model_dump_json()


def test_redact_cookie_text_never_returns_cookie_values():
    assert redact_cookie_text("a=1; b=2") == "[redacted]; [redacted]"


def test_wechat_login_qr_code_returns_safe_fields():
    store = NowcoderSessionStore()
    with respx.mock:
        respx.get("https://www.nowcoder.com/oauth2/login/wechat_qr_code").mock(
            return_value=Response(
                200,
                json={
                    "code": 0,
                    "msg": "OK",
                    "data": {"ticket": "ticket-1", "imageUrl": "https://qr.example", "expireSecond": 120},
                },
            )
        )
        result = store.wechat_login_qr_code()

    assert result.ticket == "ticket-1"
    assert result.image_url == "https://qr.example"
    assert "cookie" not in result.model_dump_json().lower()


def test_wechat_login_qr_code_can_save_image(tmp_path):
    store = NowcoderSessionStore(NowcoderConfig(auth_state_path=tmp_path / "storage_state.json"))
    with respx.mock:
        respx.get("https://www.nowcoder.com/oauth2/login/wechat_qr_code").mock(
            return_value=Response(
                200,
                json={
                    "code": 0,
                    "msg": "OK",
                    "data": {"ticket": "ticket-1", "imageUrl": "https://qr.example/img.jpg", "expireSecond": 120},
                },
            )
        )
        respx.get("https://qr.example/img.jpg").mock(return_value=Response(200, content=b"fake-jpg"))
        result = store.wechat_login_qr_code(save_image=True)

    assert result.image_path is not None
    assert (tmp_path / "wechat_login_qr_ticket1.jpg").read_bytes() == b"fake-jpg"
    assert "cookie" not in result.model_dump_json().lower()


def test_wechat_login_status_not_scanned_does_not_create_state(tmp_path):
    store = NowcoderSessionStore(NowcoderConfig(auth_state_path=tmp_path / "storage_state.json"))
    with respx.mock:
        respx.get("https://www.nowcoder.com/oauth2/login/wechat_mp_status").mock(
            return_value=Response(200, json={"code": 1, "msg": "二维码未被扫描"})
        )
        result = store.wechat_login_status("ticket-1")

    assert result.authenticated is False
    assert result.state_file_exists is False
    assert not store.state_path.exists()


def test_wechat_login_wait_times_out_without_state(tmp_path):
    store = NowcoderSessionStore(NowcoderConfig(auth_state_path=tmp_path / "storage_state.json"))
    with respx.mock:
        respx.get("https://www.nowcoder.com/oauth2/login/wechat_mp_status").mock(
            return_value=Response(200, json={"code": 1, "msg": "二维码未被扫描"})
        )
        result = store.wechat_login_wait("ticket-1", timeout_seconds=1, interval_seconds=0.5)

    assert result.authenticated is False
    assert result.code == 1
    assert not store.state_path.exists()
