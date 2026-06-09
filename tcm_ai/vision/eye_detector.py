"""Deprecated: use tcm_ai.adapters.vision.eye_detector."""

import warnings

from tcm_ai.adapters.vision.eye_detector import *  # noqa: F403

warnings.warn(
    "tcm_ai.vision.eye_detector is deprecated; import from tcm_ai.adapters.vision.eye_detector",
    DeprecationWarning,
    stacklevel=2,
)
