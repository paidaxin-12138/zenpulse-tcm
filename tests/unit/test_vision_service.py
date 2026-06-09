# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import pytest

from tcm_ai.services.vision_service import VisionService
from tests.fixtures.vision_samples import TINY_PNG_B64


def test_decode_base64_image_returns_color_array():
    service = VisionService()
    image = service.decode_base64_image(f"data:image/png;base64,{TINY_PNG_B64}")
    assert image is not None
    assert image.ndim == 3
    assert image.shape[0] >= 1 and image.shape[1] >= 1


def test_decode_image_rejects_invalid_bytes():
    service = VisionService()
    with pytest.raises(ValueError, match="无法解码"):
        service.decode_image(b"not-an-image")
