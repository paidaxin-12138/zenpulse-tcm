import cv2
import numpy as np

from tcm_ai.domain.vision_utils import normalize_hsv_channels


class EyeDetector:
    def detect_eye_血丝(self, eye_roi):
        gray = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        hsv = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 | mask2
        red_edges = cv2.bitwise_and(edges, red_mask)

        contours, _ = cv2.findContours(red_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        blood_vessel_length = sum(cv2.arcLength(contour, False) for contour in contours)
        red_pixel_count = int(np.sum(red_mask > 0))
        red_ratio = red_pixel_count / red_mask.size

        return {
            "blood_vessel_length": blood_vessel_length,
            "red_pixel_count": red_pixel_count,
            "red_ratio": red_ratio,
            "severity": self._calculate_severity(blood_vessel_length, red_ratio),
        }

    def _calculate_severity(self, vessel_length, red_ratio):
        if vessel_length < 100 and red_ratio < 0.05:
            return "轻度"
        if vessel_length < 300 and red_ratio < 0.15:
            return "中度"
        return "重度"

    def analyze_eye_color(self, eye_roi):
        hsv = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2HSV)
        return normalize_hsv_channels(
            np.mean(hsv[:, :, 0]),
            np.mean(hsv[:, :, 1]),
            np.mean(hsv[:, :, 2]),
        )
