# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import warnings

import pytest


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_legacy_tcm_agent_shim_exports_agent():
    from tcm_ai.ai.tcm_agent import TCMAgent
    from tcm_ai.services.tcm_agent import TCMAgent as CanonicalAgent

    assert TCMAgent is CanonicalAgent


def test_legacy_tcm_agent_shim_warns():
    with pytest.warns(DeprecationWarning, match="tcm_ai.ai.tcm_agent"):
        import importlib

        import tcm_ai.ai.tcm_agent as mod

        importlib.reload(mod)
        from tcm_ai.ai.tcm_agent import TCMAgent  # noqa: F401


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_legacy_vision_shim_reexports_face_detector():
    from tcm_ai.adapters.vision.face_detector import FaceDetector
    from tcm_ai.vision.face_detector import FaceDetector as LegacyFaceDetector

    assert LegacyFaceDetector is FaceDetector
