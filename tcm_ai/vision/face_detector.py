"""Deprecated: use tcm_ai.adapters.vision.face_detector."""

import warnings

from tcm_ai.adapters.vision.face_detector import *  # noqa: F403

warnings.warn(
    "tcm_ai.vision.face_detector is deprecated; import from tcm_ai.adapters.vision.face_detector",
    DeprecationWarning,
    stacklevel=2,
)
