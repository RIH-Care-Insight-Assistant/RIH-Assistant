"""
Phase 6: SafeStrandsAgent

A guarded wrapper around a Strands-style Agent.

Key rules:
- NEVER used for crisis or safety routing.
- ONLY runs if:
    STRANDS_ENABLED=true  AND  strands SDK is importable
- Fails CLOSED:
    - On import errors
    - On timeouts
    - On unexpected output
    - On disallowed topics
    - On safety keyword violations
- If anything is wrong, returns "" and logs a warning.

This file can exist safely even if:
- STRANDS_ENABLED defaults to "false"
- strands SDK is not installed
"""

import os
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import List

logger = logging.getLogger(__name__)

# Try to import a Strands-like Agent.
# This will be monkeypatched in tests; in production, this will be the real SDK.
try:
    from strands import Agent  # type: ignore
    STRANDS_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    Agent = None  # type: ignore
    STRANDS_AVAILABLE = False


def _call_with_timeout(fn, timeout_s: float, *args, **kwargs):
    """
    Run a function with a hard timeout.
    Returns fn(...) result or None on timeout/error.
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
        self._agent = None

        # Config flags
        env_flag = os.getenv("STRANDS_ENABLED", "false").lower() == "true"
        self.timeout_seconds = float(os.getenv("STRANDS_TIMEOUT_SECONDS", "10.0"))

        self.enabled = bool(env_flag and STRANDS_AVAILABLE)

        if self.enabled and Agent is not None:
            try:
                full_instructions = instructions + self._safety_constraints()

                # Newer and older Strands versions have slightly different Agent signatures.
                # We try a few safe variants so tests (FakeAgent) AND real SDK both work.
                agent = None
                last_err: Exception | None = None

                # 1) Old style used in our tests: Agent(name, instructions)
                try:
                    agent = Agent(name=name, instructions=full_instructions)  # type: ignore[arg-type]
                except TypeError as e:
                    last_err = e

                # 2) Newer style: Agent(name=..., system_message=...)
                if agent is None:
                    try:
                        agent = Agent(name=name, system_message=full_instructions)  # type: ignore[arg-type]
                    except TypeError as e:
                        last_err = e

                # 3) Fallback: Agent(name=name) – we’ll pass the prompt at call time
                if agent is None:
                    try:
                        agent = Agent(name=name)  # type: ignore[arg-type]
                    except Exception as e:
                        last_err = e

                if agent is None:
                    raise last_err or RuntimeError("Unable to initialize Strands Agent")

                self._agent = agent
                logger.info(
                    "SafeStrandsAgent '%s' initialized (topics=%s, timeout=%.2fs)",
                    name,
                    self.allowed_topics,
                    self.timeout_seconds,
                )
            except Exception as e:
                # Fail closed: disable integration completely
                logger.warning(
                    "Failed to initialize SDK Agent for SafeStrandsAgent '%s': %s. "
                    "Continuing with HTTP-only mode.",
                    name,
                    e,
                )
                self.enabled = False
                self._agent = None
        else:
            if env_flag and not STRANDS_AVAILABLE:
                logger.debug(
                    "STRANDS_ENABLED=true but strands SDK not available; "
                    "SafeStrandsAgent '%s' disabled.",
                    name,
                )

        # ===================== PUBLIC API =====================

    def generate(self, user_text: str, base_response: str) -> str:
        """
        Optionally enhance/augment a base response.

        - If disabled or unsafe → returns base_response (no change).
        - If enabled:
            * Only runs on allowed topics.
            * Hard timeout.
            * If Strands result violates safety rules → fallback to base_response.
        """
        # If not correctly initialized, do nothing.
        if not (self.enabled and self._agent):
            return base_response

        # Never touch crisis/safety flows
        if self._looks_like_crisis(user_text) or self._looks_like_crisis(base_response):
            return base_response

        # Check topic whitelist
        if not self._is_allowed_topic(user_text):
            return base_response

        prompt = (
            "You are an assistant enhancing responses for a university health services "
            "FAQ assistant. Improve clarity, empathy, and structure of the reply "
            "WITHOUT changing factual content, URLs, or phone numbers.\n\n"
            f"User message:\n{user_text}\n\n"
            f"Current reply:\n{base_response}\n\n"
            "Return ONLY the improved reply text."
        )

        def _run():
            # Support both:
            #  - FakeAgent / older-style: agent.run(prompt)
            #  - Newer Strands Agent: agent(prompt)
            if hasattr(self._agent, "run"):
                return self._agent.run(prompt)  # type: ignore[call-arg]
            return self._agent(prompt)  # type: ignore[call-arg]

        strands_reply = _call_with_timeout(_run, self.timeout_seconds)

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

    def _looks_like_crisis(self, text) -> bool:
        """
        Very simple crisis keyword check.

        Accepts either a plain string or an AgentResult-like object.
        We always coerce to str() before checking, so new SDK types are safe.
        """
        if not text:
            return False

        t = str(text).lower()

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
