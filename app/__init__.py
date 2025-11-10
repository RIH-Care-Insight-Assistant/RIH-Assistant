"""
RIH Care Insight Assistant - Phase 6 with Strands Integration
Core Safety Principle: "Strands enhances, never replaces, safety routing"
"""

import os
import logging

# Configure logging only if no handlers are already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

# Create logger for this module
logger = logging.getLogger(__name__)

# Log Strands status on startup
strands_enabled = os.getenv("STRANDS_ENABLED", "false").lower() == "true"
if strands_enabled:
    logger.info("RIH Care Insight Assistant initialized with Strands integration enabled")
else:
    logger.info("RIH Care Insight Assistant initialized with Strands integration DISABLED (fallback mode)")
