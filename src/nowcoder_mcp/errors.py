class NowcoderError(Exception):
    code = "NOWCODER_ERROR"

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthRequiredError(NowcoderError):
    code = "AUTH_REQUIRED"


class AuthExpiredError(NowcoderError):
    code = "AUTH_EXPIRED"


class RateLimitedError(NowcoderError):
    code = "RATE_LIMITED"


class UpstreamChangedError(NowcoderError):
    code = "UPSTREAM_CHANGED"


class NotFoundError(NowcoderError):
    code = "NOT_FOUND"
