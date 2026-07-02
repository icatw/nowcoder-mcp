from __future__ import annotations

import html
import json
import re

from bs4 import BeautifulSoup


def html_to_text(raw_html: str | None) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = html.unescape(text).replace("\xa0", " ")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def extract_json_string_field(page: str, field: str) -> str:
    pattern = rf'"{re.escape(field)}"\s*:\s*"((?:\\.|[^"\\])*)"'
    match = re.search(pattern, page)
    if not match:
        return ""
    try:
        return json.loads(f'"{match.group(1)}"')
    except json.JSONDecodeError:
        return match.group(1)


def extract_feed_content(page: str) -> tuple[str, str]:
    title = extract_json_string_field(page, "title")
    soup = BeautifulSoup(page, "html.parser")
    content_node = soup.select_one(".feed-content-text")
    content = html_to_text(str(content_node)) if content_node else ""
    if not content:
        content = html_to_text(extract_json_string_field(page, "content"))
    return title, content
