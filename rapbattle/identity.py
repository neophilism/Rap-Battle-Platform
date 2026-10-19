"""Adapter to the reviewed engine library; no downstream identity/token issuer."""
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .engine_contract import ENGINE_REVISION


class IdentityError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class EngineUnavailable(Exception):
    pass


@dataclass(frozen=True)
class Principal:
    account_id: str
    session_id: str
    organization_id: str


class UnconfiguredEngine:
    def ready(self):
        return False

    def authorize(self, authorization, organization_id, action):
        raise EngineUnavailable("Engine adapter is not configured")


class NodeEngine:
    def __init__(self, checkout, *, node="node", timeout=5):
        self.checkout = str(Path(checkout).resolve())
        self.node = node
        self.timeout = timeout
        self.bridge = str(Path(__file__).with_name("engine_bridge.mjs"))

    def _call(self, payload):
        try:
            result = subprocess.run(
                [self.node, "--experimental-strip-types", self.bridge, self.checkout],
                input=json.dumps(payload), capture_output=True, text=True,
                timeout=self.timeout, check=False,
            )
            # Raw stdout/stderr may contain upstream diagnostics; never relay them.
            if result.returncode != 0 or len(result.stdout)>8192:
                raise EngineUnavailable("Engine verification unavailable")
            response = json.loads(result.stdout)
            if not isinstance(response, dict) or response.get("revision") != ENGINE_REVISION:
                raise EngineUnavailable("Engine revision is unverified")
            return response
        except (OSError, subprocess.TimeoutExpired, ValueError):
            raise EngineUnavailable("Engine verification unavailable") from None

    def ready(self):
        try:
            return self._call({"operation": "ready"}).get("ready") is True
        except EngineUnavailable:
            return False

    def authorize(self, authorization, organization_id, action):
        if not isinstance(authorization, str) or not re.fullmatch(r"Bearer [A-Za-z0-9_-]{43}", authorization):
            raise IdentityError("missing" if not authorization else "invalid")
        if action not in ("content.view_private", "tenant.manage"):
            raise IdentityError("forbidden")
        response = self._call({"operation": "authorize", "authorization": authorization,
                               "organizationId": organization_id, "action": action})
        if response.get("error") in ("missing", "invalid", "expired", "revoked", "forbidden"):
            raise IdentityError(response["error"])
        p = response.get("principal")
        if (not isinstance(p, dict) or p.get("organizationId") != organization_id or
                not all(isinstance(p.get(k), str) and p[k] for k in ("accountId", "sessionId"))):
            raise EngineUnavailable("Engine principal is invalid")
        return Principal(p["accountId"], p["sessionId"], organization_id)
