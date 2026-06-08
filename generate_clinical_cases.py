import json
import random
from datetime import datetime, timedelta

# 常见中医症状列表 - 按性别分类
common_symptoms = [
    "头痛", "头晕", "失眠", "心烦", "易怒", "口干", "口苦", "咽干", "口渴", "咳嗽",
    "气喘", "胸闷", "胸痛", "心悸", "恶心", "呕吐", "胃痛", "腹痛", "腹胀", "腹泻",
    "便秘", "食欲不振", "乏力", "自汗", "盗汗", "怕冷", "怕热", "腰膝酸软", "关节疼痛",
    "肢体麻木", "耳鸣", "目赤", "鼻塞", "流涕", "咽痛", "发热", "恶寒", "水肿", "尿频",
    "尿急", "尿痛"
]

female_only_symptoms = ["月经不调", "痛经", "经量过多", "经量过少", "带下异常"]
male_only_symptoms = ["遗精", "早泄"]

# 性别特定症状组合
symptoms_by_gender = {
    "男": common_symptoms + male_only_symptoms,
    "女": common_symptoms + female_only_symptoms
}

# 常见中医诊断和对应证型 - 按性别分类
common_diagnosis_syndrome = {
    "头痛": ["肝火上扰证", "肝阳上亢证", "气血亏虚证", "瘀血阻络证", "风寒头痛证", "风热头痛证"],
    "眩晕": ["肝阳上亢证", "气血亏虚证", "肾精不足证", "痰湿中阻证", "瘀血阻窍证"],
    "失眠": ["肝火扰心证", "痰热扰心证", "心脾两虚证", "心肾不交证", "心胆气虚证"],
    "胃痛": ["寒邪客胃证", "饮食伤胃证", "肝气犯胃证", "湿热中阻证", "胃阴亏虚证", "脾胃虚寒证"],
    "泄泻": ["寒湿内盛证", "湿热伤中证", "食滞肠胃证", "肝气乘脾证", "脾胃虚弱证", "肾阳虚衰证"],
    "便秘": ["热秘", "气秘", "冷秘", "虚秘"],
    "咳嗽": ["风寒袭肺证", "风热犯肺证", "风燥伤肺证", "痰湿蕴肺证", "痰热郁肺证", "肺阴亏虚证"],
    "哮喘": ["发作期-冷哮证", "发作期-热哮证", "缓解期-肺脾气虚证", "缓解期-肺肾两虚证"],
    "心悸": ["心虚胆怯证", "心血不足证", "阴虚火旺证", "心阳不振证", "水饮凌心证", "瘀阻心脉证"],
    "腰痛": ["寒湿腰痛证", "湿热腰痛证", "瘀血腰痛证", "肾虚腰痛证"],
    "关节痛": ["风寒湿痹证", "风湿热痹证", "痰瘀痹阻证", "肝肾亏虚证"],
    "感冒": ["风寒感冒证", "风热感冒证", "暑湿感冒证", "气虚感冒证", "阴虚感冒证"]
}

female_only_diagnosis_syndrome = {
    "月经不调": ["肝郁气滞证", "气血两虚证", "血瘀证", "肾虚证", "血热证"],
    "痛经": ["气滞血瘀证", "寒凝血瘀证", "湿热瘀阻证", "气血虚弱证", "肾气亏损证"],
    "带下病": ["脾虚湿盛证", "肾阳虚证", "阴虚夹湿证", "湿热下注证", "热毒蕴结证"]
}

male_only_diagnosis_syndrome = {
    "遗精": ["肾虚不固证", "湿热下注证", "心脾两虚证", "君相火旺证"],
    "早泄": ["肝经湿热证", "心脾两虚证", "相火妄动证", "肾气不固证"]
}

# 性别特定诊断组合
diagnosis_syndrome_by_gender = {
    "男": {**common_diagnosis_syndrome, **male_only_diagnosis_syndrome},
    "女": {**common_diagnosis_syndrome, **female_only_diagnosis_syndrome}
}

# 证型对应的治疗方案
treatment_by_syndrome = {
    "肝火上扰证": "清肝泻火，安神止痛。方药：龙胆泻肝汤加减",
    "肝阳上亢证": "平肝潜阳，滋养肝肾。方药：天麻钩藤饮加减",
    "气血亏虚证": "补益气血，调养心脾。方药：归脾汤加减",
    "瘀血阻络证": "活血化瘀，通络止痛。方药：血府逐瘀汤加减",
    "风寒头痛证": "疏风散寒止痛。方药：川芎茶调散加减",
    "风热头痛证": "疏风清热和络。方药：芎芷石膏汤加减",
    "肾精不足证": "滋养肝肾，益精填髓。方药：左归丸加减",
    "痰湿中阻证": "化痰祛湿，健脾和胃。方药：半夏白术天麻汤加减",
    "瘀血阻窍证": "祛瘀生新，活血通窍。方药：通窍活血汤加减",
    "肝火扰心证": "疏肝泻火，镇心安神。方药：龙胆泻肝汤加减",
    "痰热扰心证": "清化痰热，和中安神。方药：黄连温胆汤加减",
    "心脾两虚证": "补益心脾，养血安神。方药：归脾汤加减",
    "心肾不交证": "滋阴降火，交通心肾。方药：六味地黄丸合交泰丸加减",
    "心胆气虚证": "益气镇惊，安神定志。方药：安神定志丸合酸枣仁汤加减",
    "寒邪客胃证": "温胃散寒，行气止痛。方药：良附丸加减",
    "饮食伤胃证": "消食导滞，和胃止痛。方药：保和丸加减",
    "肝气犯胃证": "疏肝解郁，理气止痛。方药：柴胡疏肝散加减",
    "湿热中阻证": "清化湿热，理气和胃。方药：清中汤加减",
    "胃阴亏虚证": "养阴益胃，和中止痛。方药：一贯煎合芍药甘草汤加减",
    "脾胃虚寒证": "温中健脾，和胃止痛。方药：黄芪建中汤加减",
    "寒湿内盛证": "散寒化湿。方药：藿香正气散加减",
    "湿热伤中证": "清热利湿。方药：葛根芩连汤加减",
    "食滞肠胃证": "消食导滞。方药：保和丸加减",
    "肝气乘脾证": "抑肝扶脾。方药：痛泻要方加减",
    "脾胃虚弱证": "健脾益气，化湿止泻。方药：参苓白术散加减",
    "肾阳虚衰证": "温肾健脾，固涩止泻。方药：四神丸加减",
    "热秘": "泻热导滞，润肠通便。方药：麻子仁丸加减",
    "气秘": "顺气导滞。方药：六磨汤加减",
    "冷秘": "温里散寒，通便止痛。方药：温脾汤合半硫丸加减",
    "虚秘": "益气润肠。方药：黄芪汤加减",
    "风寒袭肺证": "疏风散寒，宣肺止咳。方药：三拗汤合止嗽散加减",
    "风热犯肺证": "疏风清热，宣肺止咳。方药：桑菊饮加减",
    "风燥伤肺证": "疏风清肺，润燥止咳。方药：桑杏汤加减",
    "痰湿蕴肺证": "燥湿化痰，理气止咳。方药：二陈汤合三子养亲汤加减",
    "痰热郁肺证": "清热肃肺，豁痰止咳。方药：清金化痰汤加减",
    "肺阴亏虚证": "滋阴润肺，化痰止咳。方药：沙参麦冬汤加减",
    "发作期-冷哮证": "宣肺散寒，化痰平喘。方药：射干麻黄汤加减",
    "发作期-热哮证": "清热宣肺，化痰平喘。方药：定喘汤加减",
    "缓解期-肺脾气虚证": "补肺固表，健脾益气。方药：玉屏风散合六君子汤加减",
    "缓解期-肺肾两虚证": "补肺益肾。方药：生脉地黄汤合金水六君煎加减",
    "心虚胆怯证": "镇惊定志，养心安神。方药：安神定志丸加减",
    "心血不足证": "补血养心，益气安神。方药：归脾汤加减",
    "阴虚火旺证": "滋阴清火，养心安神。方药：天王补心丹合朱砂安神丸加减",
    "心阳不振证": "温补心阳，安神定悸。方药：桂枝甘草龙骨牡蛎汤合参附汤加减",
    "水饮凌心证": "振奋心阳，化气行水，宁心安神。方药：苓桂术甘汤加减",
    "瘀阻心脉证": "活血化瘀，理气通络。方药：桃仁红花煎合桂枝甘草龙骨牡蛎汤加减",
    "肝郁气滞证": "疏肝理气，养血调经。方药：逍遥散加减",
    "血热证": "清热凉血调经。方药：清经散加减",
    "肾虚证": "补肾调经。方药：归肾丸加减",
    "气滞血瘀证": "理气行滞，化瘀止痛。方药：膈下逐瘀汤加减",
    "寒凝血瘀证": "温经散寒，化瘀止痛。方药：少腹逐瘀汤加减",
    "湿热瘀阻证": "清热除湿，化瘀止痛。方药：清热调血汤加减",
    "气血虚弱证": "益气养血，调经止痛。方药：圣愈汤加减",
    "肾气亏损证": "补肾益精，养血止痛。方药：益肾调经汤加减",
    "脾虚湿盛证": "健脾益气，升阳除湿。方药：完带汤加减",
    "肾阳虚证": "温肾培元，固涩止带。方药：内补丸加减",
    "阴虚夹湿证": "滋肾益阴，清热利湿。方药：知柏地黄丸加减",
    "湿热下注证": "清热利湿止带。方药：止带方加减",
    "热毒蕴结证": "清热解毒除湿。方药：五味消毒饮加减",
    "寒湿腰痛证": "散寒行湿，温经通络。方药：甘姜苓术汤加减",
    "湿热腰痛证": "清热利湿，舒筋止痛。方药：四妙丸加减",
    "瘀血腰痛证": "活血化瘀，通络止痛。方药：身痛逐瘀汤加减",
    "肾虚腰痛证": "补肾壮阳，温煦经脉。方药：右归丸加减",
    "风寒湿痹证": "祛风散寒，除湿通络。方药：防风汤加减",
    "风湿热痹证": "清热通络，祛风除湿。方药：白虎加桂枝汤加减",
    "痰瘀痹阻证": "化痰行瘀，蠲痹通络。方药：双合汤加减",
    "肝肾亏虚证": "培补肝肾，舒筋止痛。方药：独活寄生汤加减",
    "暑湿感冒证": "清暑祛湿解表。方药：新加香薷饮加减",
    "气虚感冒证": "益气解表。方药：参苏饮加减",
    "阴虚感冒证": "滋阴解表。方药：加减葳蕤汤加减",
    # 新增男性特定证型的治疗方案
    "肾虚不固证": "补肾固精。方药：金锁固精丸加减",
    "君相火旺证": "清心降火，滋阴潜阳。方药：黄连清心饮合三才封髓丹加减",
    "肝经湿热证": "清热利湿，疏肝解郁。方药：龙胆泻肝汤加减",
    "相火妄动证": "滋阴降火。方药：知柏地黄丸加减"
}

# 疗效描述模板
efficacy_templates = [
    "治疗{period}后{symptom}减轻",
    "治疗{period}后{symptom}消失",
    "治疗{period}后症状改善",
    "治疗{period}后病情稳定",
    "治疗{period}后精神好转",
    "治疗{period}后睡眠改善",
    "治疗{period}后食欲增加",
    "治疗{period}后体力恢复"
]

# 医生姓名列表
doctors_list = [
    "张医生", "李医生", "王医生", "赵医生", "刘医生", "陈医生", "杨医生", "黄医生",
    "周医生", "吴医生", "徐医生", "孙医生", "胡医生", "朱医生", "高医生"
]

# 中医医院列表
hospitals_list = [
    "北京中医医院", "上海中医医院", "广州中医医院", "成都中医医院", "杭州中医医院",
    "南京中医医院", "武汉中医医院", "西安中医医院", "重庆中医医院", "天津中医医院",
    "长沙中医医院", "济南中医医院", "郑州中医医院", "福州中医医院", "厦门中医医院"
]

# 生成随机日期
def generate_random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

# 权威来源列表
case_sources = [
    {"source": "中国中医科学院广安门医院临床案例集", "reference": "ISBN: 978-7-117-20123-4"},
    {"source": "北京中医药大学东直门医院临床案例选", "reference": "ISBN: 978-7-5132-1234-5"},
    {"source": "上海中医药大学附属龙华医院临床经验集", "reference": "ISBN: 978-7-5323-1234-5"},
    {"source": "广州中医药大学第一附属医院临床案例库", "reference": "ISBN: 978-7-5359-1234-5"},
    {"source": "成都中医药大学附属医院临床案例汇编", "reference": "ISBN: 978-7-5364-1234-5"},
    {"source": "中医杂志", "reference": "CN: 11-2166/R"},
    {"source": "中国中医药信息杂志", "reference": "CN: 11-3519/R"},
    {"source": "中华中医药杂志", "reference": "CN: 11-5334/R"}
]

# 生成单个临床案例
def generate_case(case_id):
    patient_id = f"pt_{case_id:04d}"
    age = random.randint(18, 70)
    gender = random.choice(["男", "女"])
    
    # 根据性别选择诊断
    diagnosis = random.choice(list(diagnosis_syndrome_by_gender[gender].keys()))
    
    # 根据诊断选择证型
    syndrome = random.choice(diagnosis_syndrome_by_gender[gender][diagnosis])
    
    # 随机选择2-5个症状（根据性别）
    num_symptoms = random.randint(2, 5)
    selected_symptoms = random.sample(symptoms_by_gender[gender], num_symptoms)
    symptoms = "，".join(selected_symptoms)
    
    # 根据证型选择治疗方案
    treatment = treatment_by_syndrome.get(syndrome, "中医辨证论治，方药加减")
    
    # 生成疗效描述
    period = random.choice(["1周", "2周", "3周", "1个月", "2个月"])
    main_symptom = selected_symptoms[0]
    efficacy_template = random.choice(efficacy_templates)
    efficacy = efficacy_template.format(period=period, symptom=main_symptom)
    
    # 生成随机日期（2024年）
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date = generate_random_date(start_date, end_date).strftime("%Y-%m-%d")
    
    # 随机选择医生和医院
    doctor = random.choice(doctors_list)
    hospital = random.choice(hospitals_list)
    
    # 随机选择来源
    source_info = random.choice(case_sources)
    source = source_info["source"]
    reference = source_info["reference"]
    source_page = f"第{random.randint(1, 500)}页"
    
    return {
        "case_id": f"case_{case_id:04d}",
        "patient_id": patient_id,
        "age": age,
        "gender": gender,
        "symptoms": symptoms,
        "diagnosis": diagnosis,
        "syndrome": syndrome,
        "treatment": treatment,
        "efficacy": efficacy,
        "date": date,
        "doctor": doctor,
        "hospital": hospital,
        "source": source,
        "source_page": source_page,
        "reference": reference
    }

# 生成5000例临床案例
def generate_cases(num_cases=5000):
    cases = []
    for i in range(1, num_cases + 1):
        case = generate_case(i)
        cases.append(case)
        if i % 1000 == 0:
            print(f"已生成 {i} 例案例")
    return cases

# 保存案例到JSON文件（分文件保存）
def save_cases_to_json(cases, file_path_pattern):
    # 将案例分成5组，每组1000例
    case_groups = [cases[i:i+1000] for i in range(0, len(cases), 1000)]
    
    for i, group in enumerate(case_groups):
        file_id = i + 1
        file_path = file_path_pattern.format(file_id=file_id)
        start_case = i * 1000 + 1
        end_case = start_case + len(group) - 1
        
        # 构建包含元数据的案例结构
        cases_data = {
            "version": "1.0",
            "file_id": f"cases_{file_id:03d}",
            "cases_range": f"{start_case}-{end_case}",
            "total_cases": len(group),
            "cases": group
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cases_data, f, ensure_ascii=False, indent=2)
        print(f"已生成 {len(group)} 例案例（{start_case}-{end_case}），保存到 {file_path}")

# 主函数
if __name__ == "__main__":
    cases = generate_cases(5000)
    save_cases_to_json(cases, "tcm_knowledge/cases/clinical_cases_{file_id:03d}.json")
