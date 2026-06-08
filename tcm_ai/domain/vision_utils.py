"""OpenCV HSV 归一化：Hue 保持 0–180，Saturation/Value 归一化到 0–1。"""

from typing import Dict, List, Tuple, Union


def normalize_hsv_channels(hue: float, saturation: float, value: float) -> Dict[str, float]:
    return {
        "hue": float(hue),
        "saturation": float(saturation) / 255.0,
        "value": float(value) / 255.0,
    }


def normalize_hsv_tuple(hsv: Union[Tuple[float, float, float], List[float]]) -> List[float]:
    return [float(hsv[0]), float(hsv[1]) / 255.0, float(hsv[2]) / 255.0]
