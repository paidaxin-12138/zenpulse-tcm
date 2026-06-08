from typing import Any, Dict, Optional

import base64

import cv2
import numpy as np

from tcm_ai.adapters.vision.eye_detector import EyeDetector
from tcm_ai.adapters.vision.face_detector import FaceDetector
from tcm_ai.adapters.vision.tongue_detector import TongueDetector


class VisionService:
    def __init__(
        self,
        face_detector: Optional[FaceDetector] = None,
        tongue_detector: Optional[TongueDetector] = None,
        eye_detector: Optional[EyeDetector] = None,
    ) -> None:
        self.face_detector = face_detector or FaceDetector()
        self.tongue_detector = tongue_detector or TongueDetector()
        self.eye_detector = eye_detector or EyeDetector()

    @staticmethod
    def decode_image(content: bytes) -> np.ndarray:
        image_np = np.frombuffer(content, np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("无法解码图片")
        return image

    @staticmethod
    def decode_base64_image(data: str) -> np.ndarray:
        payload = data.split(",", 1)[-1]
        content = base64.b64decode(payload)
        return VisionService.decode_image(content)

    def analyze_from_images(
        self,
        face_cv: Optional[np.ndarray] = None,
        tongue_cv: Optional[np.ndarray] = None,
        eye_cv: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        vision_data: Dict[str, Any] = {}

        if face_cv is not None:
            faces = self.face_detector.detect_face(face_cv)
            if faces:
                face = faces[0]
                skin_color = self.face_detector.analyze_skin_color(face["roi"])
                vision_data["face"] = {"skin_color": skin_color}

                eyes = self.face_detector.detect_eyes(face["roi"])
                if eyes:
                    eye_data = []
                    for eye in eyes:
                        eye_roi = eye["roi"]
                        eye_data.append(
                            {
                                "bloodshot": self.eye_detector.detect_eye_血丝(eye_roi),
                                "color": self.eye_detector.analyze_eye_color(eye_roi),
                            }
                        )
                    vision_data["eyes"] = eye_data

        if tongue_cv is not None:
            tongue = self.tongue_detector.detect_tongue(tongue_cv)
            if tongue:
                tongue_roi = tongue["roi"]
                tongue_mask = tongue["mask"]
                color = self.tongue_detector.analyze_tongue_color(tongue_roi)
                vision_data["tongue"] = {
                    "color": {"hsv": list(color["hsv"]), "rgb": color["rgb"]},
                    "coating": self.tongue_detector.analyze_tongue_coating(tongue_roi, tongue_mask),
                }

        if eye_cv is not None:
            bloodshot = self.eye_detector.detect_eye_血丝(eye_cv)
            eye_color = self.eye_detector.analyze_eye_color(eye_cv)
            if "eyes" not in vision_data:
                vision_data["eyes"] = []
            vision_data["eyes"].append({"bloodshot": bloodshot, "color": eye_color})

        return vision_data
