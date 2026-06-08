import cv2
import numpy as np

from tcm_ai.domain.vision_utils import normalize_hsv_tuple


class TongueDetector:
    def detect_tongue(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = mask1 | mask2

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        if w * h < 10000:
            return None

        tongue_roi = image[y : y + h, x : x + w]
        return {"bbox": (x, y, w, h), "roi": tongue_roi, "mask": mask[y : y + h, x : x + w]}

    def analyze_tongue_color(self, tongue_roi):
        hsv = cv2.cvtColor(tongue_roi, cv2.COLOR_BGR2HSV)
        rgb = cv2.cvtColor(tongue_roi, cv2.COLOR_BGR2RGB)
        h, s, v = np.mean(hsv[:, :, 0]), np.mean(hsv[:, :, 1]), np.mean(hsv[:, :, 2])
        return {
            "hsv": tuple(normalize_hsv_tuple((h, s, v))),
            "rgb": (np.mean(rgb[:, :, 0]), np.mean(rgb[:, :, 1]), np.mean(rgb[:, :, 2])),
        }

    def analyze_tongue_coating(self, tongue_roi, mask):
        hsv = cv2.cvtColor(tongue_roi, cv2.COLOR_BGR2HSV)
        saturation_channel = hsv[:, :, 1]
        value_channel = hsv[:, :, 2]
        coating_ratio = np.sum(saturation_channel < 100) / mask.size
        return {
            "coating_ratio": coating_ratio,
            "coating_intensity": np.mean(value_channel[saturation_channel < 100])
            if coating_ratio > 0
            else 0,
        }
