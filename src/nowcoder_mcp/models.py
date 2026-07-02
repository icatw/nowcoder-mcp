from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Tag(str, Enum):
    all = "all"
    interview = "interview"
    progress = "progress"
    referral = "referral"
    company_review = "company_review"


class Sort(str, Enum):
    relevance = "relevance"
    latest = "latest"


TAG_TO_NOWCODER = {
    Tag.interview: (818, "面经"),
    Tag.progress: (861, "求职进度"),
    Tag.referral: (823, "内推"),
    Tag.company_review: (856, "公司评价"),
}


class SearchRecord(BaseModel):
    title: str = ""
    rc_type: int
    uuid: str | None = None
    content_id: str | None = None
    created_at_ms: int | None = None
    edited_at_ms: int | None = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    company: str | None = None
    job_title: str | None = None
    url: str


class SearchResult(BaseModel):
    query: str
    tag: Tag
    sort: Sort
    current: int = 1
    total: int = 0
    total_pages: int = 0
    records: list[SearchRecord] = Field(default_factory=list)


class DiscussDetail(BaseModel):
    content_id: str
    title: str = ""
    content: str = ""
    url: str


class FeedDetail(BaseModel):
    uuid: str
    title: str = ""
    content: str = ""
    url: str


class AuthStatus(BaseModel):
    mode: str
    state_file_exists: bool = False
    state_file_mode: str | None = None
    authenticated: bool = False
    username_hint: str | None = None
    error: str | None = None


class AuthProbe(BaseModel):
    mode: str
    cookie_available: bool = False
    authenticated: bool = False
    profile_url: str | None = None
    user_id: str | None = None
    nickname: str | None = None
    error: str | None = None


class CurrentUser(BaseModel):
    authenticated: bool = False
    user_id: str | None = None
    nickname: str | None = None
    profile_url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class WechatLoginQrCode(BaseModel):
    ticket: str
    image_url: str
    expire_second: int = 0
    image_path: str | None = None


class WechatLoginStatus(BaseModel):
    ticket: str
    code: int
    message: str = ""
    authenticated: bool = False
    state_file_exists: bool = False
    state_file_mode: str | None = None
    callback: str | None = None


class UserPublicProfile(BaseModel):
    user_id: str
    nickname: str = ""
    url: str
    raw: dict[str, Any] = Field(default_factory=dict)


class CommentRecord(BaseModel):
    comment_id: str | None = None
    content: str = ""
    created_at_ms: int | None = None
    like_count: int = 0
    user_nickname: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class CommentResult(BaseModel):
    content_id: str
    page: int = 1
    comments: list[CommentRecord] = Field(default_factory=list)


class SourceReference(BaseModel):
    source_type: str
    source_id: str
    title: str = ""
    url: str


class ExtractedSignal(BaseModel):
    label: str
    value: str
    confidence: float = 0.0
    evidence: str = ""


class PostSignals(BaseModel):
    source: SourceReference
    interview_rounds: list[ExtractedSignal] = Field(default_factory=list)
    roles: list[ExtractedSignal] = Field(default_factory=list)
    tech_stack: list[ExtractedSignal] = Field(default_factory=list)
    algorithms: list[ExtractedSignal] = Field(default_factory=list)
    system_design: list[ExtractedSignal] = Field(default_factory=list)
    project_deep_dive: list[ExtractedSignal] = Field(default_factory=list)
    behavioral: list[ExtractedSignal] = Field(default_factory=list)
    process: list[ExtractedSignal] = Field(default_factory=list)
    result_status: list[ExtractedSignal] = Field(default_factory=list)
    preparation_advice: list[ExtractedSignal] = Field(default_factory=list)
    question_count: int = 0
    raw_excerpt: str = ""


class ErrorResult(BaseModel):
    error: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
