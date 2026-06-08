from tcm_ai.domain.vision_utils import normalize_hsv_channels, normalize_hsv_tuple


def test_normalize_hsv_channels():
    result = normalize_hsv_channels(90, 128, 255)
    assert result["hue"] == 90.0
    assert abs(result["saturation"] - 128 / 255) < 0.001
    assert abs(result["value"] - 1.0) < 0.001


def test_normalize_hsv_tuple():
    result = normalize_hsv_tuple((30, 255, 128))
    assert result[0] == 30.0
    assert abs(result[1] - 1.0) < 0.001
    assert abs(result[2] - 128 / 255) < 0.001
