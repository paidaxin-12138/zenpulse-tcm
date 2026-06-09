# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from tcm_ai.services.tcm_agent import TCMAgent

# 测试TCMAgent的基本功能
def test_tcm_agent():
    print("测试中医AI诊断系统...")
    
    # 创建TCMAgent实例
    agent = TCMAgent()
    
    # 生成模拟的视觉数据
    vision_data = {
        'face': {
            'bbox': (100, 100, 200, 200),
            'skin_color': {'hue': 25.0, 'saturation': 50.0, 'value': 80.0}
        },
        'eyes': [
            {
                'bbox': (50, 50, 80, 60),
                'bloodshot': {'severity': '轻度', 'red_ratio': 0.15},
                'color': {'hue': 10.0, 'saturation': 20.0, 'value': 90.0}
            },
            {
                'bbox': (120, 50, 80, 60),
                'bloodshot': {'severity': '轻度', 'red_ratio': 0.12},
                'color': {'hue': 10.0, 'saturation': 20.0, 'value': 90.0}
            }
        ],
        'tongue': {
            'bbox': (150, 250, 100, 120),
            'color': {'hsv': (25.0, 60.0, 70.0)},
            'coating': {'coating_ratio': 0.3, 'color': {'hsv': (30.0, 40.0, 90.0)}}
        }
    }
    
    # 生成模拟的生理参数数据
    stm_data = {
        'heart_rate': 75.0,
        'systolic_pressure': 120.0,
        'diastolic_pressure': 80.0,
        'temperature': 36.5
    }
    
    # 测试诊断功能
    print("\n正在进行中医诊断...")
    diagnosis = agent.get_tcm_diagnosis(vision_data, stm_data)
    print("\n=== 中医诊断结果 ===")
    print(diagnosis['diagnosis'])
    
    # 测试建议功能
    print("\n正在生成调理建议...")
    suggestions = agent.get_tcm_suggestions(diagnosis['diagnosis'])
    print("\n=== 调理建议 ===")
    print(suggestions['suggestions'])

if __name__ == "__main__":
    test_tcm_agent()