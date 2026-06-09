# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""Deprecated: use tcm_ai.adapters.vision.tongue_detector."""

import warnings

from tcm_ai.adapters.vision.tongue_detector import *  # noqa: F403

warnings.warn(
    "tcm_ai.vision.tongue_detector is deprecated; import from tcm_ai.adapters.vision.tongue_detector",
    DeprecationWarning,
    stacklevel=2,
)
