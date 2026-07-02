from __future__ import annotations

import json
import logging

import typer

from .auth import NowcoderSessionStore
from .client import NowcoderClient
from .config import NowcoderConfig
from .models import Sort, Tag
from .server import run_stdio
from .utils import to_jsonable

app = typer.Typer(help="Read-only Nowcoder MCP server and debugging CLI.")
auth_app = typer.Typer(help="Manage optional Nowcoder auth state.")
app.add_typer(auth_app, name="auth")


def _quiet_http_logs() -> None:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    _quiet_http_logs()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def serve() -> None:
    """Start the MCP server over stdio."""
    run_stdio()


@app.command("smoke-search")
def smoke_search(
    query: str,
    tag: Tag = Tag.interview,
    sort: Sort = Sort.latest,
    max_pages: int = typer.Option(1, min=1, max=10),
    use_auth: bool = False,
) -> None:
    """Run a real Nowcoder search and print JSON for debugging."""
    client = NowcoderClient()
    try:
        result = client.search(query=query, tag=tag, sort=sort, max_pages=max_pages, use_auth=use_auth)
        typer.echo(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))
    finally:
        client.close()


@app.command("smoke-comments")
def smoke_comments(content_id: str, page: int = 1, use_auth: bool = False) -> None:
    """Fetch visible discuss comments and print safe JSON for debugging."""
    client = NowcoderClient()
    try:
        result = client.get_discuss_comments(content_id=content_id, page=page, use_auth=use_auth)
        typer.echo(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))
    finally:
        client.close()


@app.command("smoke-user")
def smoke_user(user_id: str, use_auth: bool = False) -> None:
    """Fetch public user profile metadata and print safe JSON for debugging."""
    client = NowcoderClient()
    try:
        result = client.get_user_public_profile(user_id=user_id, use_auth=use_auth)
        typer.echo(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))
    finally:
        client.close()


@app.command("smoke-signals")
def smoke_signals(
    content_id: str | None = None,
    uuid: str | None = None,
    use_auth: bool = False,
) -> None:
    """Extract structured interview signals from one discuss or feed post."""
    client = NowcoderClient()
    try:
        result = client.extract_post_signals(content_id=content_id, uuid=uuid, use_auth=use_auth)
        typer.echo(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))
    finally:
        client.close()


@app.command("smoke-assets")
def smoke_assets(
    content_id: str | None = None,
    uuid: str | None = None,
    use_auth: bool = False,
) -> None:
    """Extract image assets from one discuss or feed post without OCR."""
    client = NowcoderClient()
    try:
        result = client.get_post_assets(content_id=content_id, uuid=uuid, use_auth=use_auth)
        typer.echo(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))
    finally:
        client.close()


@app.command("smoke-topics")
def smoke_topics(
    query: str,
    max_pages: int = typer.Option(1, min=1, max=10),
    max_posts: int = typer.Option(5, min=1, max=20),
    use_auth: bool = False,
) -> None:
    """Analyze recurring interview topics from Nowcoder discuss posts."""
    client = NowcoderClient()
    try:
        result = client.analyze_interview_topics(
            query=query,
            max_pages=max_pages,
            max_posts=max_posts,
            use_auth=use_auth,
        )
        typer.echo(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))
    finally:
        client.close()


@app.command("smoke-report")
def smoke_report(
    query: str,
    max_pages: int = typer.Option(1, min=1, max=10),
    max_posts: int = typer.Option(5, min=1, max=20),
    markdown_only: bool = False,
    use_auth: bool = False,
) -> None:
    """Build a Feishu-friendly Markdown interview prep report."""
    client = NowcoderClient()
    try:
        result = client.build_interview_report(
            query=query,
            max_pages=max_pages,
            max_posts=max_posts,
            use_auth=use_auth,
        )
        if markdown_only:
            typer.echo(result.markdown)
        else:
            typer.echo(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))
    finally:
        client.close()


@app.command("me")
def me() -> None:
    """Fetch the current logged-in Nowcoder user. Requires auth mode."""
    client = NowcoderClient()
    try:
        result = client.me()
        typer.echo(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))
    finally:
        client.close()


@auth_app.command("login")
def auth_login(headless: bool = False) -> None:
    """Open a browser for manual Nowcoder login and save storage_state safely."""
    store = NowcoderSessionStore(NowcoderConfig.from_env())
    path = store.capture_login_state(headless=headless)
    typer.echo(f"Saved Nowcoder auth state at {path}")


@auth_app.command("wechat-qr")
def auth_wechat_qr(save_image: bool = False) -> None:
    """Create a WeChat login QR code URL without exposing cookies."""
    store = NowcoderSessionStore(NowcoderConfig.from_env())
    result = store.wechat_login_qr_code(save_image=save_image)
    typer.echo(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


@auth_app.command("wechat-status")
def auth_wechat_status(ticket: str, callback: str | None = None) -> None:
    """Check a WeChat login QR ticket and save auth state after success."""
    store = NowcoderSessionStore(NowcoderConfig.from_env())
    result = store.wechat_login_status(ticket=ticket, callback=callback)
    typer.echo(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


@auth_app.command("wechat-wait")
def auth_wechat_wait(
    ticket: str,
    callback: str | None = None,
    timeout_seconds: int = typer.Option(120, min=1, max=300),
    interval_seconds: float = typer.Option(3.0, min=0.5, max=10.0),
) -> None:
    """Wait for a WeChat login QR ticket and save auth state after success."""
    store = NowcoderSessionStore(NowcoderConfig.from_env())
    result = store.wechat_login_wait(
        ticket=ticket,
        callback=callback,
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
    )
    typer.echo(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


@auth_app.command("probe")
def auth_probe() -> None:
    """Actively verify auth by visiting the logged-in profile page."""
    client = NowcoderClient()
    try:
        result = client.auth_probe()
        typer.echo(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))
    finally:
        client.close()


@auth_app.command("status")
def auth_status() -> None:
    """Print safe auth status without exposing cookies."""
    store = NowcoderSessionStore(NowcoderConfig.from_env())
    typer.echo(json.dumps(store.safe_status().model_dump(mode="json"), ensure_ascii=False, indent=2))


@auth_app.command("clear")
def auth_clear() -> None:
    """Delete the configured Playwright storage_state file if present."""
    store = NowcoderSessionStore(NowcoderConfig.from_env())
    path = store.state_path
    store.clear()
    typer.echo(f"Cleared Nowcoder auth state at {path}")


if __name__ == "__main__":
    app()
