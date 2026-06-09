from typing import TYPE_CHECKING, Any, Dict, List

import numpy as np

if TYPE_CHECKING:
    from tcm_ai.services.tcm_agent import TCMAgent


class PulseDiagnosisTool:
    """
    脉搏诊断工具，用于分析脉搏特征并查询相关中医知识
    """
    
    def __init__(self, tcm_agent: "TCMAgent"):
        """
        初始化脉搏诊断工具
        
        Args:
            tcm_agent: 中医智能诊断代理实例，用于访问知识库
        """
        self.tcm_agent = tcm_agent
        self.name = "pulse_diagnosis_tool"
        self.description = "分析脉搏特征并查询相关中医知识，返回与脉搏类型对应的证型和方剂"
    
    def run(self, pulse_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行脉搏诊断工具
        
        Args:
            pulse_data: 脉搏数据，包含脉搏特征和波形数据
            {
                "heart_rate": float,           # 心率
                "spo2": float,                # 血氧饱和度
                "pulse_characteristics": {    # 脉搏特征
                    "pulse_shape": str,        # 脉搏形态
                    "pulse_strength": str,     # 脉搏强度
                    "pulse_rate": str,         # 脉搏速率
                    "tcm_interpretation": str  # 中医解读
                },
                "pulse_waveform": List[float]  # 脉搏波形
            }
        
        Returns:
            包含中医诊断信息和相关知识的字典
        """
        try:
            # 1. 提取脉搏特征
            pulse_characteristics = pulse_data.get("pulse_characteristics", {})
            tcm_interpretation = pulse_characteristics.get("tcm_interpretation", "平和脉")
            heart_rate = pulse_data.get("heart_rate", 75.0)
            spo2 = pulse_data.get("spo2", 98.0)
            
            # 2. 处理脉搏波形数据，提取统计特征
            waveform_stats = self._extract_waveform_stats(pulse_data.get("pulse_waveform", []))
            if pulse_data.get("waveform_stats"):
                waveform_stats = {**waveform_stats, **pulse_data.get("waveform_stats", {})}
            
            # 3. 生成知识库查询
            query = f"{tcm_interpretation} 证型 方剂"
            
            # 4. 搜索相关知识
            related_knowledge = self.tcm_agent._search_related_knowledge(query, top_k=5)
            
            # 5. 构建诊断结果
            diagnosis_result = {
                "pulse_type": tcm_interpretation,
                "heart_rate": heart_rate,
                "spo2": spo2,
                "pulse_characteristics": pulse_characteristics,
                "waveform_stats": waveform_stats,
                "related_knowledge": related_knowledge,
                "pulse_info": self._generate_diagnosis_suggestion(tcm_interpretation, related_knowledge)
            }
            
            return diagnosis_result
        except Exception as e:
            return {
                "error": str(e),
                "message": "脉搏诊断工具执行失败"
            }
    
    def _extract_waveform_stats(self, waveform: List[float]) -> Dict[str, float]:
        """
        提取脉搏波形的统计特征
        
        Args:
            waveform: 脉搏波形数据
            
        Returns:
            波形统计特征
        """
        if not waveform:
            return {
                "mean": 0.0,
                "std": 0.0,
                "max": 0.0,
                "min": 0.0,
                "amplitude": 0.0
            }
        
        waveform_np = np.array(waveform)
        
        return {
            "mean": float(np.mean(waveform_np)),
            "std": float(np.std(waveform_np)),
            "max": float(np.max(waveform_np)),
            "min": float(np.min(waveform_np)),
            "amplitude": float(np.max(waveform_np) - np.min(waveform_np))
        }
    
    def _generate_diagnosis_suggestion(self, pulse_type: str, related_knowledge: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        生成诊断建议
        
        Args:
            pulse_type: 脉搏类型
            related_knowledge: 相关知识
            
        Returns:
            包含脉象信息和调理方式的字典
        """
        # 脉象信息和调理建议
        pulse_info = {
            "平和脉": {
                "description": "脉率正常，节律均匀（基于容积脉搏波，不含浮沉）。",
                "interpretation": "气血调和，阴阳平衡，健康状态良好。",
                "suggestion": "保持良好的生活习惯，均衡饮食，适量运动，保持心情舒畅。",
                "food": "宜食多样化食物，保持营养均衡。",
                "formula": "无需特殊方剂"
            },
            "不齐脉": {
                "description": "脉律不齐，至数间隔变异增大。",
                "interpretation": "可能提示心律不齐或气血运行不畅，建议进一步检查。",
                "suggestion": "避免过度劳累，保持情绪稳定，必要时就医检查心电图。",
                "food": "宜清淡易消化，避免浓茶、咖啡、酒精。",
                "formula": "请咨询专业中医师辨证施治"
            },
            "迟脉": {
                "description": "脉象迟缓，一息不足四至（每分钟少于60次）。",
                "interpretation": "可能提示心阳不足、气血两虚或寒证。",
                "suggestion": "温补心阳，益气养血，保暖防寒。",
                "food": "宜食温热食物，如生姜、桂圆、红枣、羊肉等；忌食生冷食物。",
                "formula": "四逆汤、理中丸、归脾汤"
            },
            "数脉": {
                "description": "脉象数急，一息五至以上（每分钟超过90次）。",
                "interpretation": "可能提示心火旺、阴虚阳亢或热证。",
                "suggestion": "清心泻火，滋阴潜阳，避免辛辣刺激。",
                "food": "宜食清凉食物，如绿豆、苦瓜、西瓜、梨等；忌食辛辣、油腻食物。",
                "formula": "黄连解毒汤、知柏地黄丸、天王补心丹"
            },
            "虚脉": {
                "description": "脉象虚弱，轻取不应，重按空虚。",
                "interpretation": "可能提示气血不足、脏腑虚弱。",
                "suggestion": "益气养血，健脾补心，增强体质。",
                "food": "宜食补益食物，如红枣、桂圆、黑芝麻、鸡肉、鱼肉等；忌食生冷、苦寒食物。",
                "formula": "四君子汤、四物汤、八珍汤"
            },
            "实脉": {
                "description": "脉象强劲有力，来去俱盛。",
                "interpretation": "可能提示实证、热证或气滞血瘀。",
                "suggestion": "根据具体证型辨证施治，如清热、理气、活血化瘀等。",
                "food": "根据具体证型调整饮食，热证宜清凉，气滞宜理气，血瘀宜活血化瘀。",
                "formula": "大承气汤、龙胆泻肝汤、血府逐瘀汤"
            }
        }
        
        # 获取基础信息
        info = pulse_info.get(pulse_type, {
            "description": "脉象异常",
            "interpretation": "建议结合其他症状进行综合诊断。",
            "suggestion": "请咨询专业中医师进行详细诊断。",
            "food": "保持均衡饮食",
            "formula": "请遵医嘱"
        })
        
        # 如果有相关知识，添加方剂建议
        if related_knowledge:
            formula_suggestions = []
            for knowledge in related_knowledge:
                if "方剂" in knowledge.get("title", "") or "方" in knowledge.get("title", ""):
                    formula_suggestions.append(knowledge.get("title", ""))
            
            if formula_suggestions:
                info["formula"] = ", ".join(formula_suggestions[:3])
        
        return info

class PulseDataProcessor:
    """
    脉搏数据处理器，用于准备脉搏数据以供工具使用
    """
    
    @staticmethod
    def prepare_pulse_data(stm_processor_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备脉搏数据
        
        Args:
            stm_processor_result: STM处理器的结果
            
        Returns:
            格式化的脉搏数据
        """
        return {
            "heart_rate": stm_processor_result.get("heart_rate", 75.0),
            "spo2": stm_processor_result.get("spo2", 98.0),
            "pulse_characteristics": stm_processor_result.get("pulse_characteristics", {}),
            "pulse_waveform": stm_processor_result.get("pulse_waveform", [])
        }
