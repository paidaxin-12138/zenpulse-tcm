"""Deprecated: use tcm_ai.adapters.stm.processor."""

import warnings

from tcm_ai.adapters.stm.processor import *  # noqa: F403

warnings.warn(
    "tcm_ai.stm.processor is deprecated; import from tcm_ai.adapters.stm.processor",
    DeprecationWarning,
    stacklevel=2,
)
