from __future__ import annotations

import json
import re
from typing import Any

import httpx

from .auth import NowcoderSessionStore
from .cache import TTLCache
from .config import NowcoderConfig
from .errors import AuthExpiredError, NotFoundError, UpstreamChangedError
from .html_parse import extract_feed_content, html_to_text
from .models import (
    AuthProbe,
    CommentRecord,
    CommentResult,
    CurrentUser,
    DiscussDetail,
    FeedDetail,
    SearchRecord,
    SearchResult,
    Sort,
    TAG_TO_NOWCODER,
    Tag,
    UserPublicProfile,
)
from .rate_limit import SlidingWindowRateLimiter

NOWCODER_SEARCH_URL = "https://gw-c.nowcoder.com/api/sparta/pc/search"
NOWCODER_DISCUSS_DETAIL_URL = "https://gw-c.nowcoder.com/api/sparta/detail/content-data/detail"
NOWCODER_DISCUSS_URL = "https://www.nowcoder.com/discuss"
NOWCODER_FEED_URL = "https://www.nowcoder.com/feed/main/detail"


class NowcoderClient:
    def __init__(
        self,
        config: NowcoderConfig | None = None,
        http_client: httpx.Client | None = None,
        session_store: NowcoderSessionStore | None = None,
        cache: TTLCache | None = None,
        rate_limiter: SlidingWindowRateLimiter | None = None,
    ):
        self.config = config or NowcoderConfig.from_env()
        self.session_store = session_store or NowcoderSessionStore(self.config)
        self.cache = cache or TTLCache(self.config.cache_ttl_seconds)
        self.rate_limiter = rate_limiter or SlidingWindowRateLimiter(self.config.rate_limit_per_minute)
        self._owns_client = http_client is None
        self.http = http_client or httpx.Client(
            timeout=self.config.timeout_seconds,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Origin": "https://www.nowcoder.com",
                "Referer": "https://www.nowcoder.com/",
                "Content-Type": "application/json; charset=UTF-8",
            },
            follow_redirects=True,
            trust_env=False,
        )

    def close(self) -> None:
        if self._owns_client:
            self.http.close()

    def _headers(self, use_auth: bool = False) -> dict[str, str]:
        headers: dict[str, str] = {}
        cookie = self.session_store.cookie_header(use_auth=use_auth)
        if use_auth and not cookie:
            raise AuthExpiredError("Nowcoder auth is enabled for this call but no usable cookie was found")
        if cookie:
            headers["Cookie"] = cookie
        return headers

    def _request(self, method: str, url: str, *, use_auth: bool = False, **kwargs: Any) -> httpx.Response:
        self.rate_limiter.check()
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.update(self._headers(use_auth=use_auth))
        response = self.http.request(method, url, headers=headers, **kwargs)
        if response.status_code in {401, 403}:
            raise AuthExpiredError("Nowcoder returned an authentication or access error")
        response.raise_for_status()
        return response

    def _cache_key(self, *parts: Any) -> str:
        return json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)

    def search(
        self,
        query: str,
        tag: Tag | str = Tag.interview,
        sort: Sort | str = Sort.latest,
        max_pages: int = 1,
        use_auth: bool = False,
    ) -> SearchResult:
        tag = Tag(tag)
        sort = Sort(sort)
        max_pages = max(1, min(max_pages, self.config.max_pages_cap))
        cache_key = self._cache_key("search", query, tag.value, sort.value, max_pages, use_auth)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        first = self._search_page(query=query, tag=tag, sort=sort, page=1, use_auth=use_auth)
        total_pages = first.total_pages
        pages_to_fetch = min(max_pages, max(total_pages, 1))
        records = list(first.records)
        seen = {self._record_identity(record) for record in records if self._record_identity(record)}

        for page in range(2, pages_to_fetch + 1):
            page_result = self._search_page(query=query, tag=tag, sort=sort, page=page, use_auth=use_auth)
            for record in page_result.records:
                identity = self._record_identity(record)
                if identity and identity in seen:
                    continue
                if identity:
                    seen.add(identity)
                records.append(record)

        result = SearchResult(
            query=query,
            tag=tag,
            sort=sort,
            current=1,
            total=first.total,
            total_pages=first.total_pages,
            records=records,
        )
        self.cache.set(cache_key, result)
        return result

    def _search_page(
        self, query: str, tag: Tag, sort: Sort, page: int, use_auth: bool = False
    ) -> SearchResult:
        tag_payload = []
        if tag != Tag.all:
            tag_id, tag_name = TAG_TO_NOWCODER[tag]
            tag_payload = [{"name": tag_name, "id": tag_id, "count": None}]
        payload = {
            "type": "all",
            "query": query,
            "page": page,
            "tag": tag_payload,
            "order": "create" if sort == Sort.latest else "",
            "gioParams": {"searchFrom_var": "顶部导航栏", "searchEnter_var": "主站"},
        }
        response = self._request("POST", NOWCODER_SEARCH_URL, json=payload, use_auth=use_auth)
        data = response.json()
        if not data.get("success"):
            raise UpstreamChangedError(f"Nowcoder search failed: {data.get('msg') or data.get('message') or data}")
        return self._parse_search_response(query=query, tag=tag, sort=sort, data=data)

    def _parse_search_response(self, query: str, tag: Tag, sort: Sort, data: dict[str, Any]) -> SearchResult:
        page_data = data.get("data") or {}
        records: list[SearchRecord] = []
        for raw in page_data.get("records") or []:
            record = self._parse_record(raw)
            if record:
                records.append(record)
        return SearchResult(
            query=query,
            tag=tag,
            sort=sort,
            current=int(page_data.get("current") or 1),
            total=int(page_data.get("total") or 0),
            total_pages=int(page_data.get("totalPage") or page_data.get("total_page") or 0),
            records=records,
        )

    def _parse_record(self, raw: dict[str, Any]) -> SearchRecord | None:
        rc_type = int(raw.get("rc_type") or raw.get("rcType") or 0)
        data = raw.get("data") or {}
        frequency = data.get("frequencyData") or {}
        user_brief = data.get("userBrief") or {}
        company, job_title = self._extract_identity(user_brief)
        if rc_type == 201:
            moment = data.get("momentData") or {}
            uuid = moment.get("uuid")
            if not uuid:
                return None
            title = moment.get("title") or raw.get("title") or ""
            return SearchRecord(
                title=title,
                rc_type=rc_type,
                uuid=str(uuid),
                content_id=None,
                created_at_ms=moment.get("createdAt"),
                edited_at_ms=moment.get("editTime"),
                view_count=int(frequency.get("viewCnt") or 0),
                like_count=int(frequency.get("likeCnt") or 0),
                comment_count=int(frequency.get("commentCnt") or 0),
                company=company,
                job_title=job_title,
                url=f"{NOWCODER_FEED_URL}/{uuid}",
            )
        if rc_type == 207:
            content = data.get("contentData") or {}
            content_id = content.get("id") or data.get("contentId")
            if not content_id:
                return None
            title = content.get("title") or raw.get("title") or ""
            return SearchRecord(
                title=title,
                rc_type=rc_type,
                uuid=None,
                content_id=str(content_id),
                created_at_ms=content.get("createTime"),
                edited_at_ms=content.get("editTime"),
                view_count=int(frequency.get("viewCnt") or 0),
                like_count=int(frequency.get("likeCnt") or 0),
                comment_count=int(frequency.get("commentCnt") or 0),
                company=company,
                job_title=job_title,
                url=f"{NOWCODER_DISCUSS_URL}/{content_id}",
            )
        return None

    @staticmethod
    def _extract_identity(user_brief: dict[str, Any]) -> tuple[str | None, str | None]:
        identities = user_brief.get("identityList") or []
        if not identities:
            return None, None
        first = identities[0] or {}
        return first.get("companyName"), first.get("jobName")

    @staticmethod
    def _record_identity(record: SearchRecord) -> str | None:
        return record.uuid or record.content_id

    def get_discuss_detail(self, content_id: str, use_auth: bool = False) -> DiscussDetail:
        cache_key = self._cache_key("discuss", content_id, use_auth)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        response = self._request(
            "GET", f"{NOWCODER_DISCUSS_DETAIL_URL}/{content_id}", use_auth=use_auth
        )
        data = response.json()
        if not data.get("success"):
            raise NotFoundError(f"Nowcoder discuss content not found: {content_id}")
        content_data = data.get("data") or {}
        detail = DiscussDetail(
            content_id=content_id,
            title=content_data.get("title") or "",
            content=html_to_text(content_data.get("richText") or content_data.get("content") or ""),
            url=f"{NOWCODER_DISCUSS_URL}/{content_id}",
        )
        self.cache.set(cache_key, detail)
        return detail

    def get_feed_detail(self, uuid: str, use_auth: bool = False) -> FeedDetail:
        cache_key = self._cache_key("feed", uuid, use_auth)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        url = f"{NOWCODER_FEED_URL}/{uuid}"
        response = self._request("GET", url, use_auth=use_auth)
        page = response.text
        if "内容不存在" in page:
            raise NotFoundError(f"Nowcoder feed content not found: {uuid}")
        title, content = extract_feed_content(page)
        detail = FeedDetail(uuid=uuid, title=title, content=content, url=url)
        self.cache.set(cache_key, detail)
        return detail

    def search_interviews(
        self,
        company: str | None = None,
        role: str | None = None,
        tech_stack: list[str] | None = None,
        year: int | None = None,
        max_pages: int = 2,
    ) -> SearchResult:
        parts = [part for part in [company, role, *(tech_stack or []), "面经", str(year) if year else None] if part]
        query = " ".join(parts) if parts else "面经"
        return self.search(query=query, tag=Tag.interview, sort=Sort.latest, max_pages=max_pages)

    def get_discuss_comments(
        self, content_id: str, page: int = 1, use_auth: bool = False
    ) -> CommentResult:
        page = max(1, page)
        cache_key = self._cache_key("discuss-comments", content_id, page, use_auth)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        response = self._request(
            "GET", f"{NOWCODER_DISCUSS_URL}/{content_id}", params={"page": page}, use_auth=use_auth
        )
        comments = self._parse_comments_from_html(response.text)
        result = CommentResult(content_id=content_id, page=page, comments=comments)
        self.cache.set(cache_key, result)
        return result

    def get_user_public_profile(self, user_id: str, use_auth: bool = False) -> UserPublicProfile:
        cache_key = self._cache_key("user-profile", user_id, use_auth)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        url = f"https://www.nowcoder.com/users/{user_id}"
        response = self._request("GET", url, use_auth=use_auth)
        profile = self._parse_user_public_profile(user_id=user_id, url=url, html=response.text)
        self.cache.set(cache_key, profile)
        return profile

    def me(self) -> CurrentUser:
        response = self._request("GET", "https://www.nowcoder.com/profile", use_auth=True)
        return self._parse_current_user(str(response.url), response.text)

    def auth_probe(self) -> AuthProbe:
        cookie_available = bool(self.session_store.cookie_header(use_auth=True))
        try:
            user = self.me()
            return AuthProbe(
                mode=self.config.auth_mode,
                cookie_available=cookie_available,
                authenticated=user.authenticated,
                profile_url=user.profile_url,
                user_id=user.user_id,
                nickname=user.nickname,
            )
        except Exception as exc:
            return AuthProbe(
                mode=self.config.auth_mode,
                cookie_available=cookie_available,
                authenticated=False,
                error=str(exc),
            )

    @staticmethod
    def _parse_current_user(url: str, html: str) -> CurrentUser:
        if "/login" in url or "/404" in url:
            return CurrentUser(authenticated=False)
        user_id = None
        id_match = re.search(r"/users/(\d+)", url)
        if id_match:
            user_id = id_match.group(1)
        nickname = NowcoderClient._first_json_text(html, "rawNickname") or NowcoderClient._first_json_text(
            html, "nickname"
        )
        profile_url = f"https://www.nowcoder.com/users/{user_id}" if user_id else url
        return CurrentUser(
            authenticated=bool(user_id or nickname),
            user_id=user_id,
            nickname=nickname,
            profile_url=profile_url,
            raw={"final_url": url},
        )

    @staticmethod
    def _first_json_text(text: str, key: str) -> str | None:
        match = re.search(rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"', text)
        if not match:
            return None
        return NowcoderClient._decode_json_string(match.group(1))

    @staticmethod
    def _parse_comments_from_html(page: str) -> list[CommentRecord]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(page, "html.parser")
        comments: list[CommentRecord] = []
        seen: set[str] = set()
        for selector in ["[data-comment-id]", ".comment-item", ".js-comment-item"]:
            for node in soup.select(selector):
                comment_id = node.get("data-comment-id") or node.get("data-id")
                text = node.get_text(" ", strip=True)
                key = comment_id or text
                if not text or key in seen:
                    continue
                seen.add(key)
                comments.append(CommentRecord(comment_id=comment_id, content=text))
        if comments:
            return comments

        for match in re.finditer(r'"commentId"\s*:\s*"?(?P<id>\d+)"?.{0,600}?"content"\s*:\s*"(?P<content>(?:\\.|[^"\\])*)"', page):
            content = NowcoderClient._decode_json_string(match.group("content"))
            if content:
                comments.append(CommentRecord(comment_id=match.group("id"), content=html_to_text(content)))
        return comments

    @staticmethod
    def _parse_user_public_profile(user_id: str, url: str, html: str) -> UserPublicProfile:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("title")
        nickname = ""
        if title and title.get_text(strip=True):
            nickname = title.get_text(strip=True).split("-")[0].strip()
        for selector in [".profile-user-name", ".user-name", "[class*=nickname]", "[class*=name]"]:
            node = soup.select_one(selector)
            if node and node.get_text(strip=True):
                nickname = node.get_text(strip=True)
                break
        raw = {
            "title": title.get_text(strip=True) if title else "",
            "description": NowcoderClient._meta_content(soup, "description"),
        }
        return UserPublicProfile(user_id=user_id, nickname=nickname, url=url, raw=raw)

    @staticmethod
    def _meta_content(soup: Any, name: str) -> str:
        node = soup.find("meta", attrs={"name": name})
        return str(node.get("content") or "") if node else ""

    @staticmethod
    def _decode_json_string(value: str) -> str:
        try:
            return json.loads(f'"{value}"')
        except json.JSONDecodeError:
            return value
