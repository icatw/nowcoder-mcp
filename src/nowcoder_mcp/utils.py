from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .errors import NowcoderError
from .models import ErrorResult


def to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return value


def error_to_jsonable(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, NowcoderError):
        return ErrorResult(error=exc.code, message=exc.message, details=exc.details).model_dump(mode="json")
    return ErrorResult(error="UNEXPECTED_ERROR", message=str(exc)).model_dump(mode="json")
