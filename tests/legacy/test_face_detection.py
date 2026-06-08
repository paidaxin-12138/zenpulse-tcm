import cv2
import numpy as np
from tcm_ai.adapters.vision.face_detector import FaceDetector

# 创建一个空白图像
img = np.ones((480, 640, 3), dtype=np.uint8) * 255

# 绘制一个简单的人脸示意图
cv2.circle(img, (320, 240), 100, (255, 200, 150), -1)
cv2.circle(img, (280, 200), 15, (0, 0, 0), -1)
cv2.circle(img, (360, 200), 15, (0, 0, 0), -1)
cv2.line(img, (320, 240), (320, 270), (0, 0, 0), 2)
cv2.ellipse(img, (320, 290), (30, 20), 0, 0, 180, (0, 0, 0), 2)

print("创建测试图像成功")

# 初始化面部检测器
try:
    face_detector = FaceDetector()
    print("面部检测器初始化成功")
    
    # 测试面部检测
    faces = face_detector.detect_face(img)
    print(f"检测到 {len(faces)} 个人脸")
    
    if faces:
        # 测试眼睛检测
        eyes = face_detector.detect_eyes(faces[0]['roi'])
        print(f"检测到 {len(eyes)} 只眼睛")
        
    print("面部检测功能测试通过")
except Exception as e:
    print(f"面部检测功能测试失败: {e}")