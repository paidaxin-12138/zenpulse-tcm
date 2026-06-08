"""多模态数据预处理、融合与 Prompt 生成。"""

from typing import Any, Dict


class FusionEngine:
    @staticmethod
    def process_vision_data( vision_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理视觉数据，统一格式并评估数据质量
        
        Args:
            vision_data: 原始视觉数据，包含face、tongue、eyes等信息
            
        Returns:
            处理后的视觉数据，包含质量评分和标准化格式
        """
        processed_data = {
            "face": None,
            "tongue": None,
            "eyes": None,
            "quality": {
                "face_quality": 0.0,
                "tongue_quality": 0.0,
                "eyes_quality": 0.0,
                "overall_quality": 0.0
            }
        }
        
        # 处理面部数据
        if "face" in vision_data and vision_data["face"]:
            face_data = vision_data["face"]
            processed_face = {
                "skin_color": face_data.get("skin_color", {"hue": 25.0, "saturation": 0.3, "value": 0.7}),
                "facial_features": face_data.get("facial_features", [])
            }
            processed_data["face"] = processed_face
            
            # 评估面部数据质量
            face_quality = 0.5
            if "skin_color" in face_data:
                face_quality += 0.3
            if "facial_features" in face_data and face_data["facial_features"]:
                face_quality += 0.2
            processed_data["quality"]["face_quality"] = min(1.0, face_quality)
        
        # 处理舌头数据
        if "tongue" in vision_data and vision_data["tongue"]:
            tongue_data = vision_data["tongue"]
            processed_tongue = {
                "color": tongue_data.get("color", {"hsv": [20.0, 0.5, 0.6], "rgb": [220, 100, 100]}),
                "coating": tongue_data.get("coating", {"coating_ratio": 0.3, "color": [20.0, 0.2, 0.8]})
            }
            processed_data["tongue"] = processed_tongue
            
            # 评估舌头数据质量
            tongue_quality = 0.5
            if "color" in tongue_data:
                tongue_quality += 0.3
            if "coating" in tongue_data:
                tongue_quality += 0.2
            processed_data["quality"]["tongue_quality"] = min(1.0, tongue_quality)
        
        # 处理眼睛数据
        if "eyes" in vision_data and vision_data["eyes"]:
            eyes_data = vision_data["eyes"]
            processed_eyes = []
            for eye in eyes_data:
                processed_eye = {
                    "bloodshot": eye.get("bloodshot", {"red_ratio": 0.1, "severity": "轻微"}),
                    "redness": eye.get("redness", 0.2)
                }
                processed_eyes.append(processed_eye)
            processed_data["eyes"] = processed_eyes
            
            # 评估眼睛数据质量
            eyes_quality = 0.5
            if eyes_data:
                eyes_quality += 0.5
            processed_data["quality"]["eyes_quality"] = min(1.0, eyes_quality)
        
        # 计算整体质量
        total_quality = (
            processed_data["quality"]["face_quality"] +
            processed_data["quality"]["tongue_quality"] +
            processed_data["quality"]["eyes_quality"]
        ) / 3.0
        processed_data["quality"]["overall_quality"] = total_quality
        
        return processed_data
    
    @staticmethod
    def process_stm_data( stm_data: Dict[str, float]) -> Dict[str, Any]:
        """处理STM生理数据，统一格式并评估数据质量
        
        Args:
            stm_data: 原始生理数据，包含心率、血压、体温、年龄、性别等信息
            
        Returns:
            处理后的生理数据，包含质量评分和标准化格式
        """
        processed_data = {
            "age": None,
            "gender": None,
            "heart_rate": None,
            "blood_pressure": None,
            "temperature": None,
            "quality": {
                "heart_rate_quality": 0.0,
                "blood_pressure_quality": 0.0,
                "temperature_quality": 0.0,
                "overall_quality": 0.0
            }
        }
        
        # 处理年龄数据
        if "age" in stm_data and stm_data["age"] is not None:
            processed_data["age"] = stm_data["age"]
        
        # 处理性别数据
        if "gender" in stm_data and stm_data["gender"] is not None:
            processed_data["gender"] = stm_data["gender"]
        
        # 处理心率数据
        if "heart_rate" in stm_data:
            heart_rate = stm_data["heart_rate"]
            # 心率正常范围：60-100次/分
            heart_rate_status = "正常"
            if heart_rate < 60:
                heart_rate_status = "过缓"
            elif heart_rate > 100:
                heart_rate_status = "过速"
            
            processed_data["heart_rate"] = {
                "value": heart_rate,
                "status": heart_rate_status
            }
            processed_data["quality"]["heart_rate_quality"] = 1.0
        
        # 处理血压数据
        if "systolic_pressure" in stm_data and "diastolic_pressure" in stm_data:
            systolic = stm_data["systolic_pressure"]
            diastolic = stm_data["diastolic_pressure"]
            
            # 血压状态评估
            bp_status = "正常"
            if systolic >= 140 or diastolic >= 90:
                bp_status = "高血压"
            elif systolic < 90 or diastolic < 60:
                bp_status = "低血压"
            elif systolic >= 120 or diastolic >= 80:
                bp_status = "血压偏高"
            
            processed_data["blood_pressure"] = {
                "systolic": systolic,
                "diastolic": diastolic,
                "status": bp_status
            }
            processed_data["quality"]["blood_pressure_quality"] = 1.0
        
        # 处理体温数据
        if "temperature" in stm_data:
            temperature = stm_data["temperature"]
            
            # 体温状态评估
            temp_status = "正常"
            if temperature > 37.3:
                temp_status = "发热"
            elif temperature < 36.0:
                temp_status = "体温偏低"
            
            processed_data["temperature"] = {
                "value": temperature,
                "status": temp_status
            }
            processed_data["quality"]["temperature_quality"] = 1.0
        
        # 计算整体质量
        total_quality = (
            processed_data["quality"]["heart_rate_quality"] +
            processed_data["quality"]["blood_pressure_quality"] +
            processed_data["quality"]["temperature_quality"]
        ) / 3.0
        processed_data["quality"]["overall_quality"] = total_quality
        
        return processed_data
    
    @staticmethod
    def fuse( vision_data: Dict[str, Any], stm_data: Dict[str, Any]) -> Dict[str, Any]:
        """实现多模态数据的加权融合机制
        
        Args:
            vision_data: 处理后的视觉数据
            stm_data: 处理后的生理数据
            
        Returns:
            融合后的数据，包含各模态的加权结果和整体诊断依据
        """
        # 定义各模态的基础权重（基于中医诊断的重要性）
        weights = {
            "tongue": 0.35,  # 舌诊在中医诊断中最重要
            "face": 0.25,    # 面诊次之
            "heart_rate": 0.15, # 心率是重要的生理指标
            "blood_pressure": 0.15, # 血压同样重要
            "temperature": 0.05, # 体温相对次要
            "eyes": 0.05      # 眼诊提供辅助信息
        }
        
        fusion_result = {
            "weighted_features": {},
            "diagnosis_basis": [],
            "overall_confidence": 0.0
        }
        
        # 计算加权特征和诊断依据
        total_weight = 0.0
        weighted_sum = 0.0
        
        # 处理年龄和性别信息
        age_weight = 0.1
        gender_weight = 0.1
        
        if stm_data["age"] is not None:
            fusion_result["weighted_features"]["age"] = stm_data["age"]
            fusion_result["diagnosis_basis"].append({
                "feature": f"年龄{stm_data['age']}岁",
                "description": "年龄是中医诊断的重要参考因素，不同年龄段的生理特点和易发病症有所不同",
                "weight": age_weight
            })
            total_weight += age_weight
            weighted_sum += age_weight * 0.5  # 给年龄一个中等的加权值
        
        if stm_data["gender"] is not None:
            fusion_result["weighted_features"]["gender"] = stm_data["gender"]
            fusion_result["diagnosis_basis"].append({
                "feature": f"性别{stm_data['gender']}",
                "description": "性别在中医诊断中具有重要意义，男女在生理结构、气血运行和易发病症方面存在差异",
                "weight": gender_weight
            })
            total_weight += gender_weight
            weighted_sum += gender_weight * 0.5  # 给性别一个中等的加权值
        
        # 处理舌头数据（权重最高）
        if vision_data["tongue"]:
            tongue = vision_data["tongue"]
            weight = weights["tongue"] * vision_data["quality"]["tongue_quality"]
            total_weight += weight
            
            # 提取舌头颜色特征
            hsv = tongue["color"]["hsv"]
            if hsv[0] < 20:  # 舌质淡
                fusion_result["weighted_features"]["tongue_color"] = "淡白"
                fusion_result["diagnosis_basis"].append({
                    "feature": "舌质淡白",
                    "description": "提示气血不足",
                    "weight": weight
                })
                weighted_sum += weight * 1.0  # 气血不足指标
            elif hsv[0] > 50:  # 舌质红
                fusion_result["weighted_features"]["tongue_color"] = "红"
                fusion_result["diagnosis_basis"].append({
                    "feature": "舌质红",
                    "description": "提示体内有热证",
                    "weight": weight
                })
                weighted_sum += weight * 2.0  # 热证指标
            else:
                fusion_result["weighted_features"]["tongue_color"] = "淡红"
            
            # 提取舌苔特征
            coating_ratio = tongue["coating"]["coating_ratio"]
            if coating_ratio > 0.6:  # 厚苔
                fusion_result["weighted_features"]["tongue_coating"] = "厚腻"
                fusion_result["diagnosis_basis"].append({
                    "feature": "舌苔厚腻",
                    "description": "提示痰湿内阻",
                    "weight": weight
                })
                weighted_sum += weight * 3.0  # 痰湿内阻指标
            elif coating_ratio < 0.1:  # 少苔
                fusion_result["weighted_features"]["tongue_coating"] = "少苔"
                fusion_result["diagnosis_basis"].append({
                    "feature": "舌苔少",
                    "description": "提示阴液不足",
                    "weight": weight
                })
                weighted_sum += weight * 4.0  # 阴虚指标
            else:
                fusion_result["weighted_features"]["tongue_coating"] = "薄白"
        
        # 处理面部数据
        if vision_data["face"]:
            face = vision_data["face"]
            weight = weights["face"] * vision_data["quality"]["face_quality"]
            total_weight += weight
            
            hsv = face["skin_color"]
            if hsv["hue"] < 20:  # 偏白
                fusion_result["weighted_features"]["face_color"] = "苍白"
                fusion_result["diagnosis_basis"].append({
                    "feature": "面色苍白",
                    "description": "提示气血不足",
                    "weight": weight
                })
                weighted_sum += weight * 1.0  # 气血不足指标
            elif hsv["hue"] > 50:  # 偏红
                fusion_result["weighted_features"]["face_color"] = "潮红"
                fusion_result["diagnosis_basis"].append({
                    "feature": "面色潮红",
                    "description": "提示体内有热证",
                    "weight": weight
                })
                weighted_sum += weight * 2.0  # 热证指标
            elif 20 <= hsv["hue"] < 30:  # 偏黄
                fusion_result["weighted_features"]["face_color"] = "萎黄"
                fusion_result["diagnosis_basis"].append({
                    "feature": "面色萎黄",
                    "description": "提示脾胃虚弱",
                    "weight": weight
                })
                weighted_sum += weight * 5.0  # 脾胃虚弱指标
            else:
                fusion_result["weighted_features"]["face_color"] = "正常"
        
        # 处理心率数据
        if stm_data["heart_rate"]:
            hr = stm_data["heart_rate"]
            weight = weights["heart_rate"] * stm_data["quality"]["heart_rate_quality"]
            total_weight += weight
            
            if hr["value"] > 100:
                fusion_result["weighted_features"]["heart_rate"] = "过速"
                fusion_result["diagnosis_basis"].append({
                    "feature": "心率过速",
                    "description": "提示心火旺",
                    "weight": weight
                })
                weighted_sum += weight * 6.0  # 心火旺指标
            elif hr["value"] < 60:
                fusion_result["weighted_features"]["heart_rate"] = "过缓"
                fusion_result["diagnosis_basis"].append({
                    "feature": "心率过缓",
                    "description": "提示心阳不足",
                    "weight": weight
                })
                weighted_sum += weight * 7.0  # 心阳不足指标
            else:
                fusion_result["weighted_features"]["heart_rate"] = "正常"
        
        # 处理血压数据
        if stm_data["blood_pressure"]:
            bp = stm_data["blood_pressure"]
            weight = weights["blood_pressure"] * stm_data["quality"]["blood_pressure_quality"]
            total_weight += weight
            
            if bp["systolic"] >= 140 or bp["diastolic"] >= 90:
                fusion_result["weighted_features"]["blood_pressure"] = "高血压"
                fusion_result["diagnosis_basis"].append({
                    "feature": "高血压",
                    "description": "提示肝阳上亢",
                    "weight": weight
                })
                weighted_sum += weight * 8.0  # 肝阳上亢指标
            elif bp["systolic"] < 90 or bp["diastolic"] < 60:
                fusion_result["weighted_features"]["blood_pressure"] = "低血压"
                fusion_result["diagnosis_basis"].append({
                    "feature": "低血压",
                    "description": "提示气血不足",
                    "weight": weight
                })
                weighted_sum += weight * 1.0  # 气血不足指标
            else:
                fusion_result["weighted_features"]["blood_pressure"] = "正常"
        
        # 处理体温数据
        if stm_data["temperature"]:
            temp = stm_data["temperature"]
            weight = weights["temperature"] * stm_data["quality"]["temperature_quality"]
            total_weight += weight
            
            if temp["value"] > 37.3:
                fusion_result["weighted_features"]["temperature"] = "发热"
                fusion_result["diagnosis_basis"].append({
                    "feature": "发热",
                    "description": "提示体内有热证",
                    "weight": weight
                })
                weighted_sum += weight * 2.0  # 热证指标
            elif temp["value"] < 36.0:
                fusion_result["weighted_features"]["temperature"] = "体温偏低"
                fusion_result["diagnosis_basis"].append({
                    "feature": "体温偏低",
                    "description": "提示阳气不足",
                    "weight": weight
                })
                weighted_sum += weight * 9.0  # 阳气不足指标
            else:
                fusion_result["weighted_features"]["temperature"] = "正常"
        
        # 处理眼睛数据
        if vision_data["eyes"] and vision_data["eyes"]:
            eyes = vision_data["eyes"][0]
            weight = weights["eyes"] * vision_data["quality"]["eyes_quality"]
            total_weight += weight
            
            if eyes["bloodshot"]["red_ratio"] > 0.3:
                fusion_result["weighted_features"]["eye_redness"] = "严重血丝"
                fusion_result["diagnosis_basis"].append({
                    "feature": "眼球严重血丝",
                    "description": "提示肝火旺盛",
                    "weight": weight
                })
                weighted_sum += weight * 10.0  # 肝火旺盛指标
            elif eyes["bloodshot"]["red_ratio"] > 0.1:
                fusion_result["weighted_features"]["eye_redness"] = "中等血丝"
                fusion_result["diagnosis_basis"].append({
                    "feature": "眼球中等血丝",
                    "description": "提示肝火旺或用眼过度",
                    "weight": weight
                })
                weighted_sum += weight * 10.0  # 肝火旺盛指标
            else:
                fusion_result["weighted_features"]["eye_redness"] = "正常"
        
        # 计算整体置信度
        if total_weight > 0:
            fusion_result["overall_confidence"] = weighted_sum / total_weight
        
        # 按照权重对诊断依据进行排序
        fusion_result["diagnosis_basis"].sort(key=lambda x: x["weight"], reverse=True)
        
        return fusion_result
    
    @staticmethod
    def summarize_fusion_data( fusion_data: Dict[str, Any]) -> str:
        """生成融合数据的摘要，用于诊断查询
        
        Args:
            fusion_data: 融合后的数据
            
        Returns:
            融合数据的摘要字符串
        """
        summary = []
        
        # 添加关键特征
        if "weighted_features" in fusion_data:
            features = fusion_data["weighted_features"]
            
            # 首先添加年龄和性别信息
            if "age" in features:
                summary.append(f"年龄{features['age']}岁")
            if "gender" in features:
                summary.append(f"性别{features['gender']}")
            
            if "tongue_color" in features:
                summary.append(f"舌质{features['tongue_color']}")
            if "tongue_coating" in features:
                summary.append(f"舌苔{features['tongue_coating']}")
            if "face_color" in features:
                summary.append(f"面色{features['face_color']}")
            if "heart_rate" in features and features["heart_rate"] != "正常":
                summary.append(f"心率{features['heart_rate']}")
            if "blood_pressure" in features and features["blood_pressure"] != "正常":
                summary.append(f"血压{features['blood_pressure']}")
            if "temperature" in features and features["temperature"] != "正常":
                summary.append(f"体温{features['temperature']}")
            if "eye_redness" in features and features["eye_redness"] != "正常":
                summary.append(features['eye_redness'])
        
        # 如果没有异常特征，说明基本正常
        if not summary:
            return "患者各项检查基本正常"
        
        return "，".join(summary)
    
    @staticmethod
    def create_fusion_diagnosis_prompt( fusion_data: Dict[str, Any], knowledge_context: str = "") -> str:
        """基于融合数据创建中医诊断提示
        
        Args:
            fusion_data: 融合后的数据，包含加权特征和诊断依据
            knowledge_context: 相关中医知识上下文
            
        Returns:
            中医诊断提示字符串
        """
        prompt_template = """
        你是一位资深的中医专家，请根据以下患者的多模态融合诊断数据和相关中医知识进行综合分析并给出中医诊断结果。
        
        患者的多模态融合诊断数据：
        {fusion_data_summary}
        
        诊断依据（按权重排序）：
        {diagnosis_basis}
        
        {knowledge_context}
        
        请按照以下格式给出诊断结果：
        1. 中医辨证：（例如：气血不足证、肝火旺盛证等）
        2. 望诊部位分析：
           面部分析：（详细分析面部特征与中医理论的对应关系）
           舌苔分析：（详细分析舌苔特征与中医理论的对应关系）
           眼睛分析：（详细分析眼睛特征与中医理论的对应关系）
        3. 生理参数分析：
           心率分析：（详细分析心率特征与中医理论的对应关系）
           血压分析：（详细分析血压特征与中医理论的对应关系）
           体温分析：（详细分析体温特征与中医理论的对应关系）
        4. 证候分析：（详细分析各症状与中医理论的对应关系）
        5. 调理建议：
           生活调理：（包括作息、运动、情绪等方面的建议）
           饮食建议：（包括宜食、忌食的食物）
        6. 中药药方：
           （提供2-3个适合的中药方剂，包括组成、用法和功效）
           中成药推荐：（提供2-3个适合的中成药，包括功效）
        7. 参考来源：
           请列出诊断过程中参考的主要中医知识来源，包括书名、章节或文件名称。
        
        请用通俗易懂的语言进行描述，避免过于专业的术语。
        """
        
        # 生成融合数据摘要
        fusion_summary = FusionEngine.summarize_fusion_data(fusion_data)
        
        # 生成诊断依据
        diagnosis_basis = ""
        if "diagnosis_basis" in fusion_data:
            for i, basis in enumerate(fusion_data["diagnosis_basis"], 1):
                diagnosis_basis += f"{i}. {basis['feature']}：{basis['description']}（权重：{basis['weight']:.2f}）\n"
        
        return prompt_template.format(
            fusion_data_summary=fusion_summary,
            diagnosis_basis=diagnosis_basis,
            knowledge_context=knowledge_context
        )
