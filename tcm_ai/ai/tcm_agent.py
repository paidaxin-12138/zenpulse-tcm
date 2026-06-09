# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""Deprecated: use tcm_ai.services.tcm_agent."""

import warnings

from tcm_ai.services.tcm_agent import TCMAgent

warnings.warn(
    "tcm_ai.ai.tcm_agent is deprecated; import from tcm_ai.services.tcm_agent",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["TCMAgent"]
