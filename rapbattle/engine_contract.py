"""Pinned upstream contract metadata; this module does not authenticate users."""
from dataclasses import dataclass
from urllib.parse import urlsplit

ENGINE_REPOSITORY = "neophilism/Live-Competition-Engine"
ENGINE_REVISION = "3a316219da1b97cffd2faed1e99967a1fb8c6362"


@dataclass(frozen=True)
class EngineBinding:
    origin: str
    revision: str

    def __post_init__(self):
        parsed = urlsplit(self.origin)
        if (parsed.scheme != "https" or not parsed.hostname or
                parsed.username is not None or parsed.password is not None or
                parsed.path not in ("", "/") or parsed.query or parsed.fragment or
                any(c.isspace() for c in self.origin) or "\\" in self.origin):
            raise ValueError("Engine origin must be an HTTPS origin without credentials")
        try:
            if parsed.port not in (None, 443):
                raise ValueError("Engine origin must use the HTTPS default port")
        except ValueError:
            raise ValueError("Engine origin must use the HTTPS default port") from None
        if self.revision != ENGINE_REVISION:
            raise ValueError("Engine revision has not been reviewed for this shell")

    @property
    def health_url(self):
        return self.origin.rstrip("/") + "/api/health"

    def readiness(self, observed_revision: str | None, session_verified: bool):
        """Both values must come from a trusted adapter, never request parameters.

        The current upstream health endpoint does not supply a revision, and its
        tenant-context endpoint does not authenticate a session. Neither alone
        can satisfy these prerequisites. No network request is made here.
        """
        reasons = []
        if observed_revision != self.revision:
            reasons.append("engine_revision_unverified")
        if session_verified is not True:
            reasons.append("engine_session_unverified")
        return {"ready": not reasons, "reasons": reasons}
