# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

# 测试多模态融合算法
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from tcm_ai.services.tcm_agent import TCMAgent

# 创建测试数据
def create_test_vision_data():
    return {
        "face": {
            "skin_color": {
                "hue": 15.0,
                "saturation": 0.25,
                "value": 0.65
            },
            "facial_features": []
        },
        "tongue": {
            "color": {
                "hsv": [18.0, 0.4, 0.5],
                "rgb": [200, 100, 100]
            },
            "coating": {
                "coating_ratio": 0.2,
                "color": [20.0, 0.2, 0.8]
            }
        },
        "eyes": [
            {
                "bloodshot": {
                    "red_ratio": 0.2,
                    "severity": "中等"
                },
                "redness": 0.3
            }
        ]
    }

def create_test_stm_data():
    return {
        "heart_rate": 105.0,
        "systolic_pressure": 135.0,
        "diastolic_pressure": 85.0,
        "temperature": 37.0
    }

# 测试多模态融合算法
def test_fusion_algorithm():
    print("=== 测试多模态融合算法 ===")
    
    # 初始化TCMAgent
    agent = TCMAgent()
    
    # 创建测试数据
    vision_data = create_test_vision_data()
    stm_data = create_test_stm_data()
    
    print("1. 原始视觉数据:")
    print(f"   面部肤色: {vision_data['face']['skin_color']}")
    print(f"   舌质HSV: {vision_data['tongue']['color']['hsv']}")
    print(f"   舌苔比例: {vision_data['tongue']['coating']['coating_ratio']}")
    print(f"   眼睛血丝: {vision_data['eyes'][0]['bloodshot']}")
    
    print("\n2. 原始生理数据:")
    print(f"   心率: {stm_data['heart_rate']}")
    print(f"   血压: {stm_data['systolic_pressure']}/{stm_data['diastolic_pressure']}")
    print(f"   体温: {stm_data['temperature']}")
    
    # 测试数据处理方法
    print("\n3. 数据处理结果:")
    processed_vision = agent._process_vision_data(vision_data)
    processed_stm = agent._process_stm_data(stm_data)
    print(f"   视觉数据质量: {processed_vision['quality']}")
    print(f"   生理数据质量: {processed_stm['quality']}")
    
    # 测试加权融合方法
    print("\n4. 加权融合结果:")
    fusion_data = agent._weighted_fusion(processed_vision, processed_stm)
    print(f"   整体置信度: {fusion_data['overall_confidence']:.2f}")
    print(f"   加权特征: {fusion_data['weighted_features']}")
    print("   诊断依据:")
    for i, basis in enumerate(fusion_data['diagnosis_basis']):
        print(f"     {i+1}. {basis['feature']}：{basis['description']}（权重：{basis['weight']:.2f}）")
    
    # 测试融合数据摘要方法
    print("\n5. 融合数据摘要:")
    fusion_summary = agent._summarize_fusion_data(fusion_data)
    print(f"   {fusion_summary}")
    
    # 测试诊断提示生成方法
    print("\n6. 诊断提示生成:")
    prompt = agent._create_fusion_diagnosis_prompt(fusion_data)
    print(f"   提示前200字符: {prompt[:200]}...")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_fusion_algorithm()
