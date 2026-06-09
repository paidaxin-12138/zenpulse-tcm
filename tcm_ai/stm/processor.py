# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""Deprecated: use tcm_ai.adapters.stm.processor."""

import warnings

from tcm_ai.adapters.stm.processor import *  # noqa: F403

warnings.warn(
    "tcm_ai.stm.processor is deprecated; import from tcm_ai.adapters.stm.processor",
    DeprecationWarning,
    stacklevel=2,
)
