# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强后的中医诊断功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tcm_ai.services.tcm_agent import TCMAgent

def test_diagnosis():
    """测试诊断功能"""
    print("=== 测试中医诊断功能 ===")
    
    # 初始化TCM代理
    try:
        agent = TCMAgent()
        print("TCM代理初始化成功")
    except Exception as e:
        print(f"TCM代理初始化失败: {e}")
        return
    
    # 测试用的视觉数据 - 气血不足的典型表现
    vision_data = {
        "face": {
            "skin_color": {
                "hue": 10,  # 偏白
                "saturation": 0.3,
                "value": 0.8
            }
        },
        "tongue": {
            "color": {
                "hsv": [15, 0.2, 0.7]  # 舌质淡
            },
            "coating": {
                "coating_ratio": 0.2  # 薄苔
            }
        },
        "eyes": [
            {
                "bloodshot": {
                    "red_ratio": 0.1,
                    "severity": "轻度"
                }
            }
        ]
    }
    
    # 测试用的生理参数
    stm_data = {
        "heart_rate": 75,
        "systolic_pressure": 110,
        "diastolic_pressure": 70
    }
    
    print("\n测试数据:")
    print(f"视觉数据: {vision_data}")
    print(f"生理参数: {stm_data}")
    
    # 执行诊断
    try:
        result = agent.get_tcm_diagnosis(vision_data, stm_data)
        print("\n诊断结果:")
        print(result["diagnosis"])
        print(f"\n诊断来源: {result['source']}")
    except Exception as e:
        print(f"\n诊断执行失败: {e}")
        import traceback
        traceback.print_exc()

def test_tongue_diagnosis():
    """测试舌苔诊断功能"""
    print("\n=== 测试舌苔诊断功能 ===")
    
    agent = TCMAgent()
    
    # 测试用的视觉数据 - 痰湿内阻的典型表现
    vision_data = {
        "face": {
            "skin_color": {
                "hue": 25,  # 正常偏黄
                "saturation": 0.4,
                "value": 0.8
            }
        },
        "tongue": {
            "color": {
                "hsv": [30, 0.3, 0.7]  # 正常舌质
            },
            "coating": {
                "coating_ratio": 0.7  # 厚苔
            }
        },
        "eyes": [
            {
                "bloodshot": {
                    "red_ratio": 0.15,
                    "severity": "轻度"
                }
            }
        ]
    }
    
    stm_data = {
        "heart_rate": 80,
        "systolic_pressure": 120,
        "diastolic_pressure": 80
    }
    
    result = agent.get_tcm_diagnosis(vision_data, stm_data)
    print(result["diagnosis"])

def test_eye_diagnosis():
    """测试眼睛诊断功能"""
    print("\n=== 测试眼睛诊断功能 ===")
    
    agent = TCMAgent()
    
    # 测试用的视觉数据 - 肝火旺盛的典型表现
    vision_data = {
        "face": {
            "skin_color": {
                "hue": 45,  # 正常偏红
                "saturation": 0.5,
                "value": 0.8
            }
        },
        "tongue": {
            "color": {
                "hsv": [45, 0.4, 0.7]  # 舌质红
            },
            "coating": {
                "coating_ratio": 0.3  # 薄苔
            }
        },
        "eyes": [
            {
                "bloodshot": {
                    "red_ratio": 0.4,
                    "severity": "重度"
                }
            }
        ]
    }
    
    stm_data = {
        "heart_rate": 90,
        "systolic_pressure": 130,
        "diastolic_pressure": 85
    }
    
    result = agent.get_tcm_diagnosis(vision_data, stm_data)
    print(result["diagnosis"])

if __name__ == "__main__":
    test_diagnosis()
    test_tongue_diagnosis()
    test_eye_diagnosis()
    print("\n=== 所有测试完成 ===")
