# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脉搏诊断工具
"""

from tcm_ai.services.tcm_agent import TCMAgent
from tcm_ai.services.pulse_service import PulseDiagnosisTool, PulseDataProcessor
import time

def test_pulse_tool():
    """
    测试脉搏诊断工具
    """
    print("=== 测试脉搏诊断工具 ===")
    
    # 1. 初始化TCM代理
    print("1. 初始化TCM代理...")
    start_time = time.time()
    tcm_agent = TCMAgent()
    end_time = time.time()
    print(f"初始化完成，耗时: {end_time - start_time:.2f}秒")
    
    # 2. 创建脉搏诊断工具
    print("\n2. 创建脉搏诊断工具...")
    pulse_tool = PulseDiagnosisTool(tcm_agent)
    print("工具创建成功")
    
    # 3. 模拟不同类型的脉搏数据
    test_cases = [
        {
            "name": "平和脉",
            "data": {
                "heart_rate": 75.0,
                "spo2": 98.5,
                "pulse_characteristics": {
                    "pulse_shape": "正常",
                    "pulse_strength": "适中",
                    "pulse_rate": "正常",
                    "tcm_interpretation": "平和脉"
                },
                "pulse_waveform": [100, 120, 150, 180, 200, 180, 150, 120, 100] * 10
            }
        },
        {
            "name": "迟脉",
            "data": {
                "heart_rate": 55.0,
                "spo2": 97.0,
                "pulse_characteristics": {
                    "pulse_shape": "正常",
                    "pulse_strength": "虚弱",
                    "pulse_rate": "过缓",
                    "tcm_interpretation": "迟脉"
                },
                "pulse_waveform": [80, 100, 120, 140, 160, 140, 120, 100, 80] * 8
            }
        },
        {
            "name": "数脉",
            "data": {
                "heart_rate": 105.0,
                "spo2": 96.0,
                "pulse_characteristics": {
                    "pulse_shape": "正常",
                    "pulse_strength": "强劲",
                    "pulse_rate": "过速",
                    "tcm_interpretation": "数脉"
                },
                "pulse_waveform": [120, 140, 170, 200, 220, 200, 170, 140, 120] * 12
            }
        },
        {
            "name": "虚脉",
            "data": {
                "heart_rate": 70.0,
                "spo2": 95.0,
                "pulse_characteristics": {
                    "pulse_shape": "细弱",
                    "pulse_strength": "虚弱",
                    "pulse_rate": "正常",
                    "tcm_interpretation": "虚脉"
                },
                "pulse_waveform": [50, 70, 90, 110, 120, 110, 90, 70, 50] * 10
            }
        },
        {
            "name": "实脉",
            "data": {
                "heart_rate": 80.0,
                "spo2": 99.0,
                "pulse_characteristics": {
                    "pulse_shape": "洪大",
                    "pulse_strength": "强劲",
                    "pulse_rate": "正常",
                    "tcm_interpretation": "实脉"
                },
                "pulse_waveform": [150, 180, 220, 260, 280, 260, 220, 180, 150] * 10
            }
        }
    ]
    
    # 4. 测试每个案例
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== 测试案例 {i}: {test_case['name']} ===")
        
        # 准备数据
        print("准备数据...")
        pulse_data = test_case['data']
        
        # 使用工具进行诊断
        print("使用工具进行诊断...")
        start_time = time.time()
        result = pulse_tool.run(pulse_data)
        end_time = time.time()
        print(f"诊断完成，耗时: {end_time - start_time:.2f}秒")
        
        # 打印结果
        print("\n诊断结果:")
        print(f"脉搏类型: {result.get('pulse_type', 'N/A')}")
        print(f"心率: {result.get('heart_rate', 'N/A')}")
        print(f"血氧: {result.get('spo2', 'N/A')}")
        print(f"脉搏特征: {result.get('pulse_characteristics', 'N/A')}")
        print(f"波形统计: {result.get('waveform_stats', 'N/A')}")
        
        # 打印脉象信息和调理方式
        pulse_info = result.get('pulse_info', {})
        print("\n脉象信息:")
        print(f"描述: {pulse_info.get('description', 'N/A')}")
        print(f"中医解读: {pulse_info.get('interpretation', 'N/A')}")
        print("\n调理方式:")
        print(f"生活建议: {pulse_info.get('suggestion', 'N/A')}")
        print(f"饮食建议: {pulse_info.get('food', 'N/A')}")
        print(f"推荐方剂: {pulse_info.get('formula', 'N/A')}")
        
        # 打印相关知识
        print("\n相关中医知识:")
        related_knowledge = result.get('related_knowledge', [])
        if related_knowledge:
            for j, knowledge in enumerate(related_knowledge, 1):
                print(f"{j}. {knowledge.get('title', '未知标题')}")
                content = knowledge.get('content', '')
                if len(content) > 100:
                    content = content[:100] + "..."
                print(f"   {content}")
        else:
            print("无相关知识")
        
        print("-" * 50)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_pulse_tool()
