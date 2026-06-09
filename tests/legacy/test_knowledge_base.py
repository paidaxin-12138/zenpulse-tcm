# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库功能测试脚本
验证扩展后的知识库是否能正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from tcm_ai.knowledge.loader import TCMAgentKnowledgeManager

def test_knowledge_base():
    """
    测试知识库的主要功能
    """
    print("=" * 60)
    print("开始测试中医知识库功能")
    print("=" * 60)
    
    try:
        # 1. 初始化知识库管理器
        knowledge_dir = r'c:\Users\lenovo\OneDrive\桌面\中医\tcm_knowledge'
        knowledge_manager = TCMAgentKnowledgeManager(knowledge_dir)
        print(f"\n1. 成功初始化知识库管理器")
        print(f"   知识目录: {knowledge_dir}")
        
        # 2. 加载所有知识
        print("\n2. 开始加载所有知识...")
        all_knowledge = knowledge_manager.load_all_knowledge()
        print(f"   加载完成，共加载 {len(all_knowledge)} 个知识项")
        
        # 3. 检查知识库统计信息
        print("\n3. 知识库统计信息:")
        stats = knowledge_manager.get_knowledge_stats()
        print(f"   总知识项数: {stats['total_items']}")
        print(f"   分类统计: {stats['categories']}")
        print(f"   文件类型: {stats['file_types']}")
        
        # 4. 检查临床案例统计
        print("\n4. 临床案例统计:")
        case_stats = stats['case_stats']
        print(f"   总案例数: {case_stats['total']}")
        print(f"   性别分布: {case_stats['by_gender']}")
        print(f"   主要诊断: {list(case_stats['by_diagnosis'].keys())[:5]}...")
        print(f"   主要证型: {list(case_stats['by_syndrome'].keys())[:5]}...")
        
        # 5. 测试知识搜索功能
        print("\n5. 测试知识搜索功能:")
        # 按分类搜索
        basic_theory_items = knowledge_manager.search_knowledge("", category_filter="基础理论", top_k=3)
        print(f"   基础理论知识项数: {len(basic_theory_items)}")
        
        # 关键词搜索
        treatment_results = knowledge_manager.search_knowledge("中药治疗", category_filter="治疗学", top_k=3)
        print(f"   '中药治疗' 搜索结果数: {len(treatment_results)}")
        if treatment_results:
            print(f"   示例结果: {treatment_results[0]['title'][:50]}...")
        
        # 6. 测试临床案例搜索功能
        print("\n6. 测试临床案例搜索功能:")
        
        # 按诊断搜索
        diarrhea_cases = knowledge_manager.search_cases("泄泻", top_k=3)
        print(f"   '泄泻' 诊断案例数: {len(diarrhea_cases)}")
        if diarrhea_cases:
            print(f"   示例案例: 患者ID={diarrhea_cases[0]['patient_id']}, 证型={diarrhea_cases[0]['syndrome']}")
        
        # 带过滤条件的搜索
        filtered_cases = knowledge_manager.search_cases("", top_k=3, 
                                                       filters={'diagnosis': '感冒', 'gender': '女'})
        print(f"   女性感冒案例数: {len(filtered_cases)}")
        if filtered_cases:
            print(f"   示例案例: 年龄={filtered_cases[0]['age']}, 症状={filtered_cases[0]['symptoms'][:30]}...")
        
        # 7. 测试索引保存和加载
        print("\n7. 测试索引保存和加载:")
        # 保存索引
        knowledge_manager.save_index()
        print("   索引保存成功")
        
        # 创建新的管理器实例，应该会自动加载索引
        new_manager = TCMAgentKnowledgeManager(knowledge_dir)
        print(f"   重新加载后知识项数: {len(new_manager.knowledge_base)}")
        print(f"   重新加载后案例索引数: {len(new_manager.case_index['diagnosis_index']) if 'diagnosis_index' in new_manager.case_index else 0}")
        
        print("\n" + "=" * 60)
        print("知识库功能测试全部通过！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("知识库功能测试失败！")
        print("=" * 60)
        return False

if __name__ == "__main__":
    test_knowledge_base()
