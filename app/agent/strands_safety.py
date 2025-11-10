from __future__ import annotations
import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

# Set up logging
logger = logging.getLogger(__name__)

try:
    from strands import Agent  # type: ignore
    STRANDS_AVAILABLE = True
    logger.info("Strands SDK successfully imported")
except ImportError:
    Agent = None
    STRANDS_AVAILABLE = False
    logger.info("Strands SDK not available - running in fallback mode")

def _call_with_timeout(fn, timeout_s: float, *args, **kwargs):
    """
    Execute a function with a hard timeout to prevent hanging.
    Returns the function result or None if timeout occurs.
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout_s)
        except FuturesTimeout:
            logger.warning(f"Function timed out after {timeout_s}s")
            return None
        except Exception as e:
            logger.warning(f"Function execution failed: {e}")
            return None

class SafeStrandsAgent:
    """
    Guarded wrapper around Strands Agent. 
    NEVER used for crisis routing - only enhances non-crisis responses.
    Fails closed (returns "") if Strands not available or disabled.
    Includes hard timeout protection to prevent blocking requests.
    """
    
    def __init__(self, name: str, instructions: str, allowed_topics: list[str]):
        self.name = name
        self.enabled = (os.getenv("STRANDS_ENABLED", "false").lower() == "true" 
                       and STRANDS_AVAILABLE)
        self.allowed_topics = allowed_topics
        
        # Configurable timeout from environment
        self.timeout_seconds = float(os.getenv("STRANDS_TIMEOUT_SECONDS", "10.0"))
        
        if self.enabled:
            full_instructions = instructions + self._safety_constraints()
            self._agent = Agent(name=name, instructions=full_instructions)
            logger.info(f"Strands agent '{name}' initialized with topics: {allowed_topics}, timeout: {self.timeout_seconds}s")
        else:
            self._agent = None
            if not STRANDS_AVAILABLE:
                logger.debug(f"Strands SDK not available for agent '{name}'")
            else:
                logger.debug(f"Strands disabled for agent '{name}'")

    def _safety_constraints(self) -> str:
        return f"""
CRITICAL SAFETY CONSTRAINTS:
- NEVER analyze or respond to crisis, suicide, self-harm, or violence topics.
- NEVER override existing safety routing decisions.
- ONLY work with these approved topics: {self.allowed_topics}.
- If unsure or error occurs, return an empty response.
- ALWAYS defer to UMBC RIH safety protocols and existing routing.
- NEVER provide medical advice or diagnosis.
- NEVER process personally identifiable information (PII) or protected health information (PHI).
"""

    def safe_run(self, prompt: str) -> str:
        """Run agent with multiple layers of safety validation and hard timeout protection"""
        if not self.enabled or not self._agent:
            return ""
        
        # Early safety check: don't send crisis-related prompts to Strands at all
        if self._contains_safety_terms(prompt):
            logger.warning(f"Strands agent '{self.name}' blocked crisis-related prompt")
            return ""
        
        try:
            # Use hard timeout to prevent hanging
            start_time = time.time()
            response = _call_with_timeout(self._agent.run, self.timeout_seconds, prompt)
            
            if response is None:
                logger.warning(f"Strands agent '{self.name}' timed out after {self.timeout_seconds}s")
                return ""
            
            elapsed_time = time.time() - start_time
            
            # Log slow calls for monitoring
            if elapsed_time > 5.0:
                logger.warning(f"Strands agent '{self.name}' took {elapsed_time:.2f}s (slow)")
            
            validated_response = self._validate_safety(response)
            
            if not validated_response:
                logger.debug(f"Strands safety validation blocked response in agent '{self.name}'")
            
            return validated_response
            
        except Exception as e:
            logger.warning(f"Strands error in agent '{self.name}': {e}")
            return ""

    def _contains_safety_terms(self, text: str) -> bool:
        """Check if text contains safety terms to avoid sending to Strands entirely"""
        text_lower = text.lower()
        safety_terms = [
            "suicide", "kill myself", "self-harm", "hurt myself", "hurt others",
            "crisis", "take my life", "kys", "kms", "unalive", "end it all",
            "988", "911"
        ]
        return any(term in text_lower for term in safety_terms)

    def _validate_safety(self, response: str) -> str:
        """Ensure response doesn't contain safety violations"""
        if not response:
            return ""
            
        response_lower = response.lower()
        
        # Block safety/crisis terms
        safety_terms = [
            "suicide", "kill myself", "self-harm", "hurt myself", "hurt others",
            "crisis", "take my life", "kys", "kms", "unalive", "end it all",
            "988", "911"
        ]
        
        # If response contains any safety terms, reject it entirely
        if any(term in response_lower for term in safety_terms):
            logger.warning(f"Strands safety violation detected in agent '{self.name}'")
            return ""
            
        return response.strip()
