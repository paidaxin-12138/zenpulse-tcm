# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import cv2
import os
import shutil
import tempfile

import numpy as np

from tcm_ai.domain.vision_utils import normalize_hsv_channels


class FaceDetector:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        cascade_files = [
            "haarcascade_frontalface_default.xml",
            "haarcascade_eye.xml",
        ]
        for file_name in cascade_files:
            source_path = cv2.data.haarcascades + file_name
            dest_path = os.path.join(self.temp_dir, file_name)
            shutil.copy(source_path, dest_path)

        self.face_cascade = cv2.CascadeClassifier(
            os.path.join(self.temp_dir, "haarcascade_frontalface_default.xml")
        )
        self.eye_cascade = cv2.CascadeClassifier(
            os.path.join(self.temp_dir, "haarcascade_eye.xml")
        )

    def detect_face(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        results = []
        for (x, y, w, h) in faces:
            face_roi = image[y : y + h, x : x + w]
            results.append({"bbox": (x, y, w, h), "roi": face_roi, "confidence": 0.9})
        return results

    def detect_eyes(self, face_roi):
        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(gray_face, 1.3, 5)

        results = []
        for (x, y, w, h) in eyes:
            eye_roi = face_roi[y : y + h, x : x + w]
            results.append({"bbox": (x, y, w, h), "roi": eye_roi})
        return results

    def analyze_skin_color(self, face_roi):
        hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
        return normalize_hsv_channels(
            np.mean(hsv[:, :, 0]),
            np.mean(hsv[:, :, 1]),
            np.mean(hsv[:, :, 2]),
        )
