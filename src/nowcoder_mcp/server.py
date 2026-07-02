from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP

from .auth import NowcoderSessionStore
from .client import NowcoderClient
from .models import Sort, Tag
from .utils import error_to_jsonable, to_jsonable

mcp = FastMCP("nowcoder-mcp")


def _client() -> NowcoderClient:
    return NowcoderClient()


@mcp.tool(description="Search public Nowcoder content by keyword. Read-only.")
def search_nowcoder(
    query: str,
    tag: Literal["all", "interview", "progress", "referral", "company_review"] = "interview",
    sort: Literal["relevance", "latest"] = "latest",
    max_pages: int = 1,
    use_auth: bool = False,
) -> dict:
    client = _client()
    try:
        return to_jsonable(
            client.search(
                query=query,
                tag=Tag(tag),
                sort=Sort(sort),
                max_pages=max_pages,
                use_auth=use_auth,
            )
        )
    except Exception as exc:  # MCP tools should return actionable errors.
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Run multiple Nowcoder searches and return results keyed by query. Read-only.")
def batch_search_nowcoder(
    queries: list[str],
    tag: Literal["all", "interview", "progress", "referral", "company_review"] = "all",
    sort: Literal["relevance", "latest"] = "latest",
    max_pages: int = 1,
    use_auth: bool = False,
) -> dict:
    client = _client()
    try:
        results = {
            query: client.search(
                query=query,
                tag=Tag(tag),
                sort=Sort(sort),
                max_pages=max_pages,
                use_auth=use_auth,
            )
            for query in queries
        }
        return to_jsonable(results)
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Fetch full content for a Nowcoder discuss post by content_id. Read-only.")
def get_nowcoder_discuss_detail(content_id: str, use_auth: bool = False) -> dict:
    client = _client()
    try:
        return to_jsonable(client.get_discuss_detail(content_id=content_id, use_auth=use_auth))
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Fetch full content for a Nowcoder Feed item by uuid. Read-only.")
def get_nowcoder_feed_detail(uuid: str, use_auth: bool = False) -> dict:
    client = _client()
    try:
        return to_jsonable(client.get_feed_detail(uuid=uuid, use_auth=use_auth))
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Convenience search for interview experiences by company, role, tech stack, and year. Read-only.")
def search_nowcoder_interviews(
    company: str | None = None,
    role: str | None = None,
    tech_stack: list[str] | None = None,
    year: int | None = None,
    max_pages: int = 2,
) -> dict:
    client = _client()
    try:
        return to_jsonable(
            client.search_interviews(
                company=company,
                role=role,
                tech_stack=tech_stack or [],
                year=year,
                max_pages=max_pages,
            )
        )
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Extract structured interview signals from one Nowcoder discuss or feed post. Read-only.")
def extract_nowcoder_post_signals(
    content_id: str | None = None,
    uuid: str | None = None,
    use_auth: bool = False,
) -> dict:
    client = _client()
    try:
        return to_jsonable(
            client.extract_post_signals(content_id=content_id, uuid=uuid, use_auth=use_auth)
        )
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Fetch visible comments for a Nowcoder discuss post. Read-only.")
def get_nowcoder_discuss_comments(content_id: str, page: int = 1, use_auth: bool = False) -> dict:
    client = _client()
    try:
        return to_jsonable(
            client.get_discuss_comments(content_id=content_id, page=page, use_auth=use_auth)
        )
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Fetch public Nowcoder user profile metadata by user_id. Read-only.")
def get_nowcoder_user_public_profile(user_id: str, use_auth: bool = False) -> dict:
    client = _client()
    try:
        return to_jsonable(client.get_user_public_profile(user_id=user_id, use_auth=use_auth))
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Fetch the current logged-in Nowcoder user. Requires auth mode. Never returns cookies.")
def nowcoder_me() -> dict:
    client = _client()
    try:
        return to_jsonable(client.me())
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Actively verify Nowcoder auth by visiting the logged-in profile page. Never returns cookies.")
def nowcoder_auth_probe() -> dict:
    client = _client()
    try:
        return to_jsonable(client.auth_probe())
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Return safe Nowcoder auth status. Never returns cookies or headers. Read-only.")
def nowcoder_auth_status() -> dict:
    client = _client()
    try:
        return to_jsonable(client.session_store.safe_status())
    except Exception as exc:
        return error_to_jsonable(exc)
    finally:
        client.close()


@mcp.tool(description="Create a WeChat login QR code URL for Nowcoder. Never returns cookies. Read-only.")
def nowcoder_wechat_login_qr_code(save_image: bool = False) -> dict:
    try:
        return to_jsonable(NowcoderSessionStore().wechat_login_qr_code(save_image=save_image))
    except Exception as exc:
        return error_to_jsonable(exc)


@mcp.tool(description="Check WeChat QR login status and save local auth state after success. Never returns cookies.")
def nowcoder_wechat_login_status(ticket: str, callback: str | None = None) -> dict:
    try:
        return to_jsonable(NowcoderSessionStore().wechat_login_status(ticket=ticket, callback=callback))
    except Exception as exc:
        return error_to_jsonable(exc)


@mcp.tool(description="Wait for WeChat QR login and save local auth state after success. Never returns cookies.")
def nowcoder_wechat_login_wait(
    ticket: str,
    callback: str | None = None,
    timeout_seconds: int = 120,
    interval_seconds: float = 3.0,
) -> dict:
    try:
        return to_jsonable(
            NowcoderSessionStore().wechat_login_wait(
                ticket=ticket,
                callback=callback,
                timeout_seconds=timeout_seconds,
                interval_seconds=interval_seconds,
            )
        )
    except Exception as exc:
        return error_to_jsonable(exc)


def run_stdio() -> None:
    mcp.run()
