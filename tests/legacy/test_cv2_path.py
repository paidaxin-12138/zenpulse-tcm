import cv2
print(f"cv2.data.haarcascades = {cv2.data.haarcascades}")

import os
print(f"实际存在的文件: {os.listdir(cv2.data.haarcascades) if os.path.exists(cv2.data.haarcascades) else '路径不存在'}")

# 检查正确路径
correct_path = r"C:\Users\lenovo\OneDrive\桌面\中医\tcm_ai_env\lib\site-packages\cv2\data"
print(f"正确路径: {correct_path}")
print(f"正确路径下的文件: {os.listdir(correct_path) if os.path.exists(correct_path) else '路径不存在'}")