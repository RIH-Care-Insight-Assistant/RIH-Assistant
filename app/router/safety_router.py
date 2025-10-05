# Purpose: Backwards‑compatible interface + class wrapper that uses Rules.
# • Provides RouteResult with both response_key and auto_reply_key (alias)
# • Exposes class SafetyRouter with .route()
# • Keeps legacy module‑level function route(message) for old callers
# ─────────────────────────────────────────────
from dataclasses import dataclass
from typing import Optional


from .rules import Rules


@dataclass
class RouteResult:
      level: Optional[str]
      response_key: Optional[str]
      auto_reply_key: Optional[str] # legacy alias — same as response_key


class SafetyRouter:
  def __init__(self, rules: Rules | None = None):
      self.rules = rules or Rules()


  def route(self, text: str) -> RouteResult:
      cat, key = self.rules.match(text)
      return RouteResult(level=cat, response_key=key, auto_reply_key=key)


# Legacy functional API for older code paths
_default_router = SafetyRouter()


def route(message: str) -> RouteResult | None:
    rr = _default_router.route(message)
    return rr if rr.level else None
