# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""基于规则的中医诊断备选方案。"""

from collections import Counter
from typing import Any, Dict

from tcm_ai.domain.diagnosis_parser import _lines_to_bullets


class RuleEngine:
    @staticmethod
    def diagnose(vision_data: Dict[str, Any], stm_data: Dict[str, float]) -> Dict[str, Any]:
        """基于规则的简单中医诊断"""
        diagnosis = []
        # 存储各部位的详细分析
        face_analysis = []
        tongue_analysis = []
        eye_analysis = []
        
        # 分析面色
        if "face" in vision_data and "skin_color" in vision_data["face"]:
            sc = vision_data["face"]["skin_color"]
            h, s, v = sc["hue"], sc["saturation"], sc["value"]
            if h < 20:  # 偏白
                face_analysis.append("面色苍白无华，提示气血不足，气血不能上荣于面")
                diagnosis.append("气血不足")
            elif h > 50:  # 偏红
                face_analysis.append("面色潮红，提示体内有热证")
                diagnosis.append("热证")
            elif 20 <= h < 30:  # 偏黄
                face_analysis.append("面色萎黄，提示脾胃虚弱或气血不足")
                diagnosis.append("脾胃虚弱")
            else:
                face_analysis.append("面色正常")
        
        # 分析舌苔
        if "tongue" in vision_data:
            tongue = vision_data["tongue"]
            
            # 分析舌苔颜色
            if "color" in tongue and "hsv" in tongue["color"]:
                hsv = tongue["color"]["hsv"]
                if hsv[0] > 50:  # 舌质红
                    tongue_analysis.append("舌质红，提示体内有热证")
                    diagnosis.append("热证")
                elif hsv[0] < 20:  # 舌质淡
                    tongue_analysis.append("舌质淡嫩，提示气血不足")
                    diagnosis.append("气血不足")
                else:
                    tongue_analysis.append("舌质颜色正常")
            
            # 分析舌苔
            if "coating" in tongue:
                coating_ratio = tongue["coating"]["coating_ratio"]
                if coating_ratio > 0.6:  # 厚苔
                    tongue_analysis.append("舌苔厚腻，提示痰湿内阻")
                    diagnosis.append("痰湿内阻")
                elif coating_ratio < 0.1:  # 少苔
                    tongue_analysis.append("舌苔少，提示阴液不足")
                    diagnosis.append("阴虚")
                elif 0.1 <= coating_ratio < 0.3:  # 薄苔
                    tongue_analysis.append("舌苔薄白，提示正常或表证")
                else:
                    tongue_analysis.append("舌苔正常")
        
        # 分析眼球血丝
        if "eyes" in vision_data:
            for eye in vision_data["eyes"]:
                if "bloodshot" in eye:
                    red_ratio = eye["bloodshot"]["red_ratio"]
                    severity = eye["bloodshot"]["severity"]
                    if red_ratio > 0.3:  # 血丝较多
                        eye_analysis.append(f"眼球血丝严重({severity})，提示肝火旺盛")
                        diagnosis.append("肝火旺盛")
                    elif red_ratio > 0.1:  # 血丝中等
                        eye_analysis.append(f"眼球血丝中等({severity})，提示肝火旺或用眼过度")
                        diagnosis.append("肝火旺盛")
                    else:
                        eye_analysis.append("眼球血丝正常")
                    break
        
        # 分析生理参数
        if "heart_rate" in stm_data:
            hr = stm_data["heart_rate"]
            if hr > 100:
                diagnosis.append("心火旺")
            elif hr < 60:
                diagnosis.append("心阳不足")
        
        if "systolic_pressure" in stm_data and "diastolic_pressure" in stm_data:
            systolic = stm_data["systolic_pressure"]
            diastolic = stm_data["diastolic_pressure"]
            if systolic >= 140 or diastolic >= 90:
                diagnosis.append("肝阳上亢")
            elif systolic < 90 or diastolic < 60:
                diagnosis.append("气血不足")
        
        # 总结诊断结果
        if not diagnosis:
            main_diagnosis = "平和质"
            analysis = "患者各项指标基本正常，中医体质平和，无明显偏颇。"
        else:
            # 统计各诊断出现的次数
            diagnosis_counts = Counter(diagnosis)
            # 获取最常见的诊断
            main_diagnosis = diagnosis_counts.most_common(1)[0][0] if diagnosis_counts else "平和质"
            
            analysis = f"根据望诊和生理参数分析，患者主要表现为{main_diagnosis}。"
            
            # 添加具体症状分析
            if "气血不足" in diagnosis:
                analysis += " 气血不足是指人体气血生化不足或消耗过度，导致脏腑功能减退的一种病理状态。"
                analysis += " 患者面色苍白无华，是由于气血不能上荣于面；舌质淡嫩，是气血亏虚的典型表现；"
                analysis += " 心悸气短，是心气血不足，心失所养的表现；神疲乏力，则是全身气血亏虚，肢体失养的结果。"
                analysis += " 气血不足多由久病体虚、饮食不节、情志失调或过度劳累等因素引起，可影响人体各脏腑功能，导致免疫力下降、容易感冒等问题。"
            if "热证" in diagnosis:
                analysis += " 体内有热，多表现为舌质红、面色潮红等症状。"
            if "痰湿内阻" in diagnosis:
                analysis += " 痰湿阻滞体内，多表现为舌苔厚腻、身体困重等症状。"
            if "肝火旺盛" in diagnosis:
                analysis += " 肝火旺盛，多表现为眼球血丝多、烦躁易怒等症状。"
            if "肝阳上亢" in diagnosis:
                analysis += " 肝阳上亢，多表现为血压偏高、头痛眩晕等症状。"
            if "阴虚" in diagnosis:
                analysis += " 阴液不足，多表现为舌苔少、口干咽燥等症状。"
            if "心火旺" in diagnosis:
                analysis += " 心火旺，多表现为心率偏快、失眠多梦等症状。"
            if "心阳不足" in diagnosis:
                analysis += " 心阳不足，多表现为心率偏慢、畏寒肢冷等症状。"
            if "脾胃虚弱" in diagnosis:
                analysis += " 脾胃虚弱，多表现为面色萎黄、食欲不振等症状。"
        
        # 生成详细的建议
        suggestions = """
建议：保持良好的生活作息，均衡饮食，适量运动，保持心情舒畅。
"""
        
        # 生成中药药方
        prescriptions = """
中药药方：
"""
        
        if "气血不足" in diagnosis:
            suggestions += """
生活调理：
- 避免过度劳累，保证充足睡眠，每晚11点前入睡
- 适度运动，可选择太极拳、八段锦等温和的运动方式，避免剧烈运动耗伤气血
- 保持心情舒畅，避免长期处于紧张或焦虑状态

饮食建议：
- 宜多食用具有益气养血作用的食物，如红枣、桂圆、黑芝麻、红豆、花生、核桃、当归、黄芪等
- 可常喝红枣桂圆茶、当归黄芪鸡汤等
- 避免食用生冷、油腻、刺激性食物
"""
            prescriptions += """
1. 八珍汤加减（补益气血）
   组成：人参10g、白术10g、茯苓10g、甘草5g、当归10g、川芎6g、白芍10g、熟地黄15g
   用法：水煎服，每日1剂，分2次服用
   功效：气血双补，适用于气血不足证

2. 归脾汤加减（益气补血，健脾养心）
   组成：黄芪15g、龙眼肉10g、白术10g、茯神10g、酸枣仁10g、人参10g、木香5g、甘草5g、当归10g、远志10g
   用法：水煎服，每日1剂，分2次服用
   功效：益气补血，健脾养心，适用于心脾两虚、气血不足证

3. 中成药推荐：
   - 归脾丸：益气健脾，养血安神
   - 补中益气丸：补中益气，升阳举陷
   - 八珍颗粒：补气益血
"""
        
        if "热证" in diagnosis:
            suggestions += """
生活调理：
- 保持居住环境凉爽通风
- 避免过度劳累和情绪激动
- 保证充足睡眠，避免熬夜

饮食建议：
- 饮食宜清淡，多食用清热降火的食物，如绿豆、苦瓜、黄瓜、西瓜、梨等
- 避免食用辛辣、油腻、刺激性食物，如辣椒、花椒、油炸食品等
- 戒烟限酒
"""
            prescriptions += """
1. 白虎汤加减（清热生津）
   组成：石膏30g、知母15g、粳米10g、甘草5g
   用法：水煎服，每日1剂，分2次服用
   功效：清热生津，适用于气分热盛证

2. 银翘散加减（辛凉解表，清热解毒）
   组成：金银花15g、连翘15g、薄荷6g、荆芥6g、淡豆豉10g、牛蒡子10g、桔梗10g、淡竹叶10g、甘草5g
   用法：水煎服，每日1剂，分2次服用
   功效：辛凉解表，清热解毒，适用于外感风热证

3. 中成药推荐：
   - 牛黄解毒片：清热解毒
   - 三黄片：清热解毒，泻火通便
   - 板蓝根颗粒：清热解毒，凉血利咽
"""
        
        if "痰湿内阻" in diagnosis:
            suggestions += """
生活调理：
- 适当增加运动，促进痰湿排出，可选择快走、慢跑、游泳等运动
- 避免长期处于潮湿环境
- 保持规律作息，避免熬夜

饮食建议：
- 宜食用健脾利湿的食物，如薏米、茯苓、赤小豆、冬瓜、山药等
- 可常喝薏米红豆粥、茯苓粥等
- 避免食用油腻、甜腻、生冷食物，如肥肉、糖果、冷饮等
"""
            prescriptions += """
1. 二陈汤加减（燥湿化痰，理气和中）
   组成：陈皮10g、半夏10g、茯苓15g、甘草5g、生姜3片、乌梅1枚
   用法：水煎服，每日1剂，分2次服用
   功效：燥湿化痰，理气和中，适用于痰湿内阻证

2. 平胃散加减（燥湿运脾，行气和胃）
   组成：苍术10g、厚朴10g、陈皮10g、甘草5g、生姜3片、大枣2枚
   用法：水煎服，每日1剂，分2次服用
   功效：燥湿运脾，行气和胃，适用于湿滞脾胃证

3. 中成药推荐：
   - 参苓白术散：补脾胃，益肺气
   - 二陈丸：燥湿化痰，理气和胃
   - 香砂六君丸：益气健脾，和胃
"""
        
        if "肝火旺盛" in diagnosis:
            suggestions += """
生活调理：
- 保持心情平和，避免情绪激动和暴怒
- 适当进行放松训练，如冥想、深呼吸等
- 保证充足睡眠，避免熬夜

饮食建议：
- 宜食用清肝泻火的食物，如菊花、芹菜、苦瓜、黄瓜、梨等
- 可常喝菊花茶、决明子茶等
- 避免食用辛辣、油腻、刺激性食物，如辣椒、花椒、油炸食品等
"""
            prescriptions += """
1. 龙胆泻肝汤加减（清泻肝胆实火，清利肝经湿热）
   组成：龙胆草6g、黄芩10g、栀子10g、泽泻10g、木通5g、车前子10g、当归10g、生地黄15g、柴胡10g、甘草5g
   用法：水煎服，每日1剂，分2次服用
   功效：清泻肝胆实火，清利肝经湿热，适用于肝火旺盛证

2. 丹栀逍遥散加减（疏肝解郁，清热调经）
   组成：牡丹皮10g、栀子10g、柴胡10g、白芍10g、当归10g、白术10g、茯苓10g、甘草5g、薄荷6g、生姜3片
   用法：水煎服，每日1剂，分2次服用
   功效：疏肝解郁，清热调经，适用于肝郁化火证

3. 中成药推荐：
   - 龙胆泻肝丸：清肝胆，利湿热
   - 丹栀逍遥丸：疏肝解郁，清热调经
   - 菊花地黄丸：滋肾养肝
"""
        
        if "阴虚" in diagnosis:
            suggestions += """
生活调理：
- 避免过度劳累，保证充足睡眠
- 适度运动，避免剧烈运动耗伤阴液
- 保持心情舒畅，避免长期处于紧张或焦虑状态

饮食建议：
- 宜食用滋阴润燥的食物，如百合、银耳、枸杞、桑葚、黑芝麻等
- 可常喝百合银耳汤、枸杞茶等
- 避免食用辛辣、温燥食物，如辣椒、花椒、羊肉等
"""
            prescriptions += """
1. 六味地黄丸加减（滋阴补肾）
   组成：熟地黄24g、山茱萸12g、山药12g、泽泻9g、茯苓9g、牡丹皮9g
   用法：水煎服，每日1剂，分2次服用
   功效：滋阴补肾，适用于肾阴虚证

2. 沙参麦冬汤加减（清养肺胃，生津润燥）
   组成：沙参15g、麦冬15g、玉竹10g、生甘草5g、冬桑叶10g、生扁豆10g、天花粉10g
   用法：水煎服，每日1剂，分2次服用
   功效：清养肺胃，生津润燥，适用于肺胃阴虚证

3. 中成药推荐：
   - 六味地黄丸：滋阴补肾
   - 知柏地黄丸：滋阴降火
   - 杞菊地黄丸：滋肾养肝
"""
        
        if "脾胃虚弱" in diagnosis:
            suggestions += """
生活调理：
- 保持规律作息，避免熬夜
- 适度运动，可选择散步、太极拳等温和的运动方式
- 注意腹部保暖，避免受凉

饮食建议：
- 宜食用健脾养胃的食物，如山药、小米、南瓜、红枣、桂圆等
- 可常喝小米粥、山药粥等
- 避免食用生冷、油腻、刺激性食物，如冷饮、肥肉、辣椒等
"""
            prescriptions += """
1. 四君子汤加减（益气健脾）
   组成：人参10g、白术10g、茯苓10g、甘草5g
   用法：水煎服，每日1剂，分2次服用
   功效：益气健脾，适用于脾胃气虚证

2. 参苓白术散加减（补脾胃，益肺气）
   组成：人参10g、白术10g、茯苓10g、山药10g、莲子10g、白扁豆10g、薏苡仁10g、砂仁5g、桔梗10g、甘草5g
   用法：水煎服，每日1剂，分2次服用
   功效：补脾胃，益肺气，适用于脾胃虚弱证

3. 中成药推荐：
   - 四君子丸：益气健脾
   - 参苓白术散：补脾胃，益肺气
   - 香砂养胃丸：温中和胃
"""
        
        # 构建完整的诊断结果
        full_diagnosis = f"1. 中医辨证：{main_diagnosis}\n"
        full_diagnosis += "2. 望诊部位分析：\n"
        if face_analysis:
            full_diagnosis += f"   面部分析：{'；'.join(face_analysis)}\n"
        if tongue_analysis:
            full_diagnosis += f"   舌苔分析：{'；'.join(tongue_analysis)}\n"
        if eye_analysis:
            full_diagnosis += f"   眼睛分析：{'；'.join(eye_analysis)}\n"
        full_diagnosis += f"3. 证候分析：{analysis}\n"
        full_diagnosis += f"4. 调理建议：{suggestions}\n"
        full_diagnosis += f"5. 中药药方：{prescriptions}\n"
        
        return {
            "diagnosis": full_diagnosis,
            "source": "中医智能诊断系统(基于规则模式)",
            "structured": {
                "syndrome": main_diagnosis,
                "analysis": analysis.strip(),
                "face_analysis": face_analysis,
                "tongue_analysis": tongue_analysis,
                "eye_analysis": eye_analysis,
                "suggestions": _lines_to_bullets(suggestions),
                "prescriptions": _lines_to_bullets(prescriptions),
            },
        }
