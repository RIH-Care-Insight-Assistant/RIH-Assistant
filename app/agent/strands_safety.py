"""
Phase 6: SafeStrandsAgent

A guarded wrapper around a Strands-style Agent.

Key rules:
- NEVER used for crisis or safety routing.
- ONLY runs if:
    STRANDS_ENABLED=true AND STRANDS_BASE_URL and STRANDS_API_KEY are set
- Fails CLOSED:
    - On import errors
    - On timeouts
    - On HTTP errors
    - On unexpected output
    - On disallowed topics
    - On safety keyword violations
- If anything is wrong, returns the original base_response and logs a warning.

This file can exist safely even without the strands SDK installed:
- With STRANDS_ENABLED defaulting to "false"
- Without "strands" Python package present
"""

import os
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import List

import requests  # Real HTTP calls

logger = logging.getLogger(__name__)

# Try to import a Strands-like Agent SDK.
# This can be used as a secondary path, but is no longer required.
try:  # pragma: no cover - environment dependent
    from strands import Agent  # type: ignore
    STRANDS_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    Agent = None  # type: ignore
    STRANDS_AVAILABLE = False


def _call_with_timeout(fn, timeout_s: float, *args, **kwargs):
    """
    Run a function with a hard timeout.
    Returns fn(...) result or None on timeout/error.
    (Kept for compatibility and optional SDK usage.)
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout_s)
        except FuturesTimeout:
            logger.warning("Strands call timed out after %.2fs", timeout_s)
            return None
        except Exception as e:
            logger.warning("Strands call failed: %s", e)
            return None


class SafeStrandsAgent:
    """
    Guarded, optional integration layer.

    Usage pattern:
        agent = SafeStrandsAgent(
            name="response_enhancer",
            instructions="...",
            allowed_topics=["tone", "clarity"]
        )
        maybe_text = agent.generate(user_text, base_response)
    """

    def __init__(self, name: str, instructions: str, allowed_topics: List[str]):
        self.name = name
        self.allowed_topics = allowed_topics or []
        self._agent = None  # Optional SDK agent (not required)
        self._instructions = instructions

        # Config flags
        env_flag = os.getenv("STRANDS_ENABLED", "false").lower() == "true"
        self.timeout_seconds = float(os.getenv("STRANDS_TIMEOUT_SECONDS", "10.0"))

        # HTTP config for real API calls
        self._base_url = os.getenv("STRANDS_BASE_URL", "").strip()
        self._api_key = os.getenv("STRANDS_API_KEY", "").strip()

        # Enabled only if env flag + HTTP config present
        self.enabled = bool(env_flag and self._base_url and self._api_key)

        if env_flag and not self.enabled:
            logger.warning(
                "STRANDS_ENABLED=true but STRANDS_BASE_URL or STRANDS_API_KEY "
                "is missing; SafeStrandsAgent '%s' disabled.",
                name,
            )

        # Optional: try to initialize SDK agent if available (not required)
        if self.enabled and STRANDS_AVAILABLE and Agent is not None:
            try:
                full_instructions = instructions + self._safety_constraints()
                self._agent = Agent(name=name, instructions=full_instructions)  # type: ignore
                logger.info(
                    "SafeStrandsAgent '%s' initialized with SDK (topics=%s, timeout=%.2fs)",
                    name,
                    self.allowed_topics,
                    self.timeout_seconds,
                )
            except Exception as e:  # pragma: no cover - defensive
                logger.warning(
                    "Failed to initialize SDK Agent for SafeStrandsAgent '%s': %s. "
                    "Continuing with HTTP-only mode.",
                    name,
                    e,
                )
                self._agent = None

    # ===================== PUBLIC API =====================

    def generate(self, user_text: str, base_response: str) -> str:
        """
        Optionally enhance/augment a base response.

        - If disabled or unsafe → returns base_response (no change).
        - If enabled:
            * Only runs on allowed topics.
            * Uses HTTP call to a Strands-style service (and optionally SDK).
            * Hard timeout via requests.
            * If Strands result violates safety rules → fallback to base_response.
        """
        # If not correctly initialized, do nothing.
        if not self.enabled:
            return base_response

        # Never touch crisis/safety flows
        if self._looks_like_crisis(user_text) or self._looks_like_crisis(base_response):
            return base_response

        # Check topic whitelist
        if not self._is_allowed_topic(user_text):
            return base_response

        # Build a safe, constrained prompt
        prompt = (
            "You are an assistant enhancing responses for a university health services "
            "FAQ assistant. Improve clarity, empathy, and structure of the reply "
            "WITHOUT changing factual content, URLs, or phone numbers.\n\n"
            f"User message:\n{user_text}\n\n"
            f"Current reply:\n{base_response}\n\n"
            "Return ONLY the improved reply text."
        )

        # === Primary path: HTTP call to Strands-style backend ===
        strands_reply = self._call_strands_http(prompt)

        # Optional secondary path: SDK, if configured & HTTP returned nothing
        if not strands_reply and self._agent is not None:
            strands_reply = _call_with_timeout(self._agent.run, self.timeout_seconds, prompt)  # type: ignore[attr-defined]

        if not strands_reply:
            return base_response

        if self._looks_like_crisis(strands_reply):
            logger.warning(
                "SafeStrandsAgent '%s' produced safety-violating text; discarded.",
                self.name,
            )
            return base_response

        # Final safeguard: strip weird whitespace
        cleaned = str(strands_reply).strip()
        if not cleaned:
            return base_response

        return cleaned

    # ===================== INTERNAL HTTP HELPER =====================

    def _call_strands_http(self, prompt: str) -> str | None:
        """
        Call a Strands-style HTTP endpoint.

        Expected env:
            STRANDS_BASE_URL  e.g. https://strands.example.com
            STRANDS_API_KEY   e.g. xyz123

        This function:
        - Returns cleaned text on success.
        - Returns None on any error or bad status.
        """
        if not (self._base_url and self._api_key):
            return None

        try:
            url = self._base_url.rstrip("/") + "/v1/run"  # Adjust path as needed

            payload = {
                "agent": self.name,
                "instructions": self._instructions + self._safety_constraints(),
                "input": prompt,
                "allowed_topics": self.allowed_topics,
            }

            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }

            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )

            if resp.status_code != 200:
                logger.warning(
                    "SafeStrandsAgent '%s' HTTP call failed with status %s",
                    self.name,
                    resp.status_code,
                )
                return None

            data = resp.json()
            # Be flexible about response schema
            text = data.get("text") or data.get("output") or ""
            text = (text or "").strip()
            return text or None

        except Exception as e:
            logger.warning("SafeStrandsAgent '%s' HTTP error: %s", self.name, e)
            return None

    # ===================== INTERNAL SAFETY HELPERS =====================

    def _safety_constraints(self) -> str:
        return (
            "\n\nCRITICAL SAFETY CONSTRAINTS:\n"
            "- NEVER provide medical advice or diagnosis.\n"
            "- NEVER override or contradict crisis/safety messaging.\n"
            "- NEVER handle suicide, self-harm, or violence content.\n"
            "- ONLY operate on approved non-crisis topics.\n"
            "- If uncertain or error occurs, return an empty response.\n"
        )

    def _is_allowed_topic(self, user_text: str) -> bool:
        """Simple whitelist check based on allowed_topics substrings."""
        if not self.allowed_topics:
            return False
        text = (user_text or "").lower()
        return any(t.lower() in text for t in self.allowed_topics)

    def _looks_like_crisis(self, text: str) -> bool:
        if not text:
            return False
        t = text.lower()
        crisis_terms = [
            "suicide",
            "kill myself",
            "hurt myself",
            "hurt others",
            "self-harm",
            "take my life",
            "end my life",
            "end it all",
            "kys",
            "kms",
            "unalive",
            "overdose",
            "jump off",
            "shoot myself",
            "stab myself",
            "988",
            "911",
        ]
        return any(term in t for term in crisis_terms)
