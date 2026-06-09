"""Deprecated: use tcm_ai.adapters.vision.tongue_detector."""

import warnings

from tcm_ai.adapters.vision.tongue_detector import *  # noqa: F403

warnings.warn(
    "tcm_ai.vision.tongue_detector is deprecated; import from tcm_ai.adapters.vision.tongue_detector",
    DeprecationWarning,
    stacklevel=2,
)
