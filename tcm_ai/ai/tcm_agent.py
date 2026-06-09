"""Deprecated: use tcm_ai.services.tcm_agent."""

import warnings

from tcm_ai.services.tcm_agent import TCMAgent

warnings.warn(
    "tcm_ai.ai.tcm_agent is deprecated; import from tcm_ai.services.tcm_agent",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["TCMAgent"]
