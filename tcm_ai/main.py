import cv2
import time

import numpy as np

from tcm_ai.api.deps import get_diagnosis_service, get_vision_service
from tcm_ai.adapters.stm.processor import STMDataProcessor


def map_pulse_to_stm_data(pulse_result):
    if not pulse_result:
        return None
    heart_rate = pulse_result.get("heart_rate", 75)
    return {
        "heart_rate": heart_rate,
        "pulse": heart_rate,
        "systolic_pressure": 120,
        "diastolic_pressure": 80,
        "temperature": 36.5,
    }


def main():
    print("中医AI诊断系统启动中...")

    vision_service = get_vision_service()
    diagnosis_service = get_diagnosis_service()
    stm_processor = STMDataProcessor()

    camera_found = False
    cap = None
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"成功打开摄像头 {i}")
            camera_found = True
            break
        cap.release()

    if not camera_found:
        print("无法打开任何摄像头，将使用模拟数据进行演示")
        cap = None

    print("系统已启动，按 'q' 键退出，按 'd' 键诊断")

    while True:
        vision_data = {}
        display_frame = None

        if cap:
            ret, frame = cap.read()
            if not ret:
                print("无法获取图像")
                break

            display_frame = frame.copy()
            vision_data = vision_service.analyze_from_images(
                face_cv=frame,
                tongue_cv=frame,
            )
            cv2.imshow("中医AI诊断系统", display_frame)
        else:
            display_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                display_frame,
                "使用模拟数据演示",
                (150, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                display_frame,
                "按 'd' 键查看诊断结果",
                (150, 250),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )
            vision_data = {
                "face": {"skin_color": {"hue": 25.0, "saturation": 0.2, "value": 0.31}},
                "eyes": [
                    {
                        "bloodshot": {"severity": "轻度", "red_ratio": 0.15},
                        "color": {"hue": 10.0, "saturation": 0.08, "value": 0.35},
                    }
                ],
                "tongue": {
                    "color": {"hsv": [25.0, 0.24, 0.27]},
                    "coating": {"coating_ratio": 0.3},
                },
            }
            cv2.imshow("中医AI诊断系统", display_frame)

        pulse_result = stm_processor.read_pulse_data()
        stm_data = map_pulse_to_stm_data(pulse_result)

        if stm_data and display_frame is not None:
            cv2.putText(
                display_frame,
                f"心率: {stm_data['heart_rate']:.0f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )

        key = cv2.waitKey(1)
        if key == ord("q"):
            break
        if key == ord("d"):
            if vision_data and stm_data:
                print("\n正在进行中医诊断...")
                result = diagnosis_service.run(vision_data, stm_data)
                print("\n=== 中医诊断结果 ===")
                print(result["diagnosis"])
                print(f"\n{result.get('disclaimer', '')}\n")
            else:
                print("无法获取完整的诊断数据")

    if cap:
        cap.release()
    cv2.destroyAllWindows()
    stm_processor.disconnect()
    print("系统已关闭")


if __name__ == "__main__":
    main()
