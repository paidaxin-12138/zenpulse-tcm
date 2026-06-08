# 知识库索引结构优化方案

## 1. 当前索引结构分析

### 1.1 现有结构
```json
{
  "knowledge_count": 133,
  "knowledge_items": [
    {
      "title": "默认章节_第1节_段落1",
      "content": "中医基础理论",
      "source": "文件路径",
      "type": "text",
      "category": "基础理论",
      "section": "默认章节",
      "file_path": "文件路径",
      "section_number": 1,
      "paragraph_number": 1
    }
  ]
}
```

### 1.2 存在的问题
- **查询效率低**：只能遍历所有条目进行查询
- **内存占用大**：大规模数据时会占用大量内存
- **功能单一**：缺乏分类、关键词等高级查询功能
- **扩展性差**：难以适应新增的知识类型和查询需求
- **维护困难**：索引更新需要重新生成整个文件

## 2. 优化目标

- 支持**快速查询**：平均查询时间<100ms
- 减少**内存占用**：索引内存占用降低50%
- 提供**多维度查询**：分类、关键词、全文搜索等
- 支持**增量更新**：避免每次更新都重新生成索引
- 确保**可扩展性**：适应未来知识库的增长

## 3. 优化后索引结构设计

### 3.1 主索引结构
```json
{
  "version": "2.0",
  "total_items": 10000,
  "total_size": "10MB",
  "last_updated": "2025-12-23T10:00:00",
  "categories": [
    {
      "name": "基础理论",
      "count": 3000,
      "subcategories": [
        {"name": "经典著作", "count": 2000},
        {"name": "现代理论", "count": 1000}
      ]
    }
  ],
  "indexes": {
    "category_index": "indexes/category_index.json",
    "keyword_index": "indexes/keyword_index.json",
    "fulltext_index": "indexes/fulltext_index.json",
    "case_index": "indexes/case_index.json",
    "authority_index": "indexes/authority_index.json"
  }
}
```

### 3.2 分类索引 (category_index.json)
```json
{
  "version": "2.0",
  "categories": {
    "基础理论": {
      "total": 3000,
      "items": [
        {"id": "kt_00001", "title": "黄帝内经素问-上古天真论篇第一", "file_path": "basic_theory/黄帝内经素问.txt", "position": 1},
        {"id": "kt_00002", "title": "黄帝内经素问-四气调神大论篇第二", "file_path": "basic_theory/黄帝内经素问.txt", "position": 100}
      ],
      "subcategories": {
        "经典著作": {
          "total": 2000,
          "items": [
            {"id": "kt_00001", "title": "黄帝内经素问-上古天真论篇第一", "file_path": "basic_theory/黄帝内经素问.txt", "position": 1}
          ]
        }
      }
    }
  }
}
```

### 3.3 关键词索引 (keyword_index.json)
```json
{
  "version": "2.0",
  "keywords": {
    "头痛": [
      {"id": "kt_00150", "category": "诊断学", "file_path": "diagnosis/中医诊断学.txt", "position": 500},
      {"id": "case_00001", "category": "临床案例", "file_path": "cases/clinical_cases_001.json", "position": 1}
    ],
    "肝火上扰证": [
      {"id": "kt_00200", "category": "诊断学", "file_path": "diagnosis/中医诊断学.txt", "position": 800},
      {"id": "case_00001", "category": "临床案例", "file_path": "cases/clinical_cases_001.json", "position": 1}
    ]
  },
  "total_keywords": 5000
}
```

### 3.4 全文倒排索引 (fulltext_index.json)
```json
{
  "version": "2.0",
  "inverted_index": {
    "中医": [
      {"id": "kt_00001", "tf": 5, "positions": [1, 5, 10, 15, 20]},
      {"id": "kt_00002", "tf": 3, "positions": [2, 8, 12]}
    ],
    "理论": [
      {"id": "kt_00001", "tf": 2, "positions": [3, 7]},
      {"id": "kt_00003", "tf": 4, "positions": [1, 5, 9, 13]}
    ]
  },
  "tokenizer": "jieba",
  "stop_words": ["的", "了", "是", "在"]
}
```

### 3.5 案例专用索引 (case_index.json)
```json
{
  "version": "2.0",
  "total_cases": 5000,
  "by_diagnosis": {
    "头痛": [
      {"id": "case_00001", "syndrome": "肝火上扰证", "file_path": "cases/clinical_cases_001.json", "position": 1},
      {"id": "case_00002", "syndrome": "风寒头痛证", "file_path": "cases/clinical_cases_001.json", "position": 2}
    ]
  },
  "by_syndrome": {
    "肝火上扰证": [
      {"id": "case_00001", "diagnosis": "头痛", "file_path": "cases/clinical_cases_001.json", "position": 1},
      {"id": "case_00010", "diagnosis": "眩晕", "file_path": "cases/clinical_cases_001.json", "position": 10}
    ]
  },
  "by_treatment": {
    "龙胆泻肝汤": [
      {"id": "case_00001", "diagnosis": "头痛", "file_path": "cases/clinical_cases_001.json", "position": 1}
    ]
  }
}
```

## 4. 索引优化技术

### 4.1 倒排索引技术
- **定义**：将文档中的每个词语映射到包含该词语的文档列表
- **优势**：大幅提高全文搜索效率
- **实现**：使用Jieba分词对中文文本进行分词，建立词语到文档的映射

### 4.2 分层索引
- **定义**：将索引分为多个层级，按需加载
- **优势**：减少内存占用，提高加载速度
- **实现**：主索引→分类索引→文档索引的三级结构

### 4.3 缓存机制
- **定义**：将常用查询结果存储在缓存中
- **优势**：提高常用查询的响应速度
- **实现**：使用LRU（最近最少使用）算法管理缓存

### 4.4 增量更新
- **定义**：只更新新增或修改的内容
- **优势**：减少索引更新时间
- **实现**：记录索引版本和更新时间，只处理变更的文件

### 4.5 压缩技术
- **定义**：对索引数据进行压缩存储
- **优势**：减少磁盘占用
- **实现**：使用JSON压缩或专门的索引压缩算法

## 5. 索引生成与维护工具

### 5.1 索引生成工具
```python
# index_generator.py
import json
import jieba
import os
from collections import defaultdict

class TCMIndexGenerator:
    def __init__(self, knowledge_base_path):
        self.knowledge_base_path = knowledge_base_path
        self.indexes = {
            "category_index": {},
            "keyword_index": defaultdict(list),
            "fulltext_index": defaultdict(list)
        }
    
    def generate_indexes(self):
        # 遍历知识库文件
        for root, dirs, files in os.walk(self.knowledge_base_path):
            for file in files:
                if file.endswith(".txt") or file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    self.process_file(file_path)
        
        # 保存索引
        self.save_indexes()
    
    def process_file(self, file_path):
        # 处理文件内容，生成索引
        pass
    
    def save_indexes(self):
        # 保存索引到文件
        pass

if __name__ == "__main__":
    generator = TCMIndexGenerator("tcm_knowledge")
    generator.generate_indexes()
```

### 5.2 索引查询工具
```python
# index_query.py
import json
import os

class TCMIndexQuery:
    def __init__(self, index_path):
        self.index_path = index_path
        self.load_indexes()
    
    def load_indexes(self):
        # 加载索引文件
        self.category_index = json.load(open(os.path.join(self.index_path, "category_index.json")))
        self.keyword_index = json.load(open(os.path.join(self.index_path, "keyword_index.json")))
        self.fulltext_index = json.load(open(os.path.join(self.index_path, "fulltext_index.json")))
    
    def query_by_category(self, category, subcategory=None):
        # 按类别查询
        pass
    
    def query_by_keyword(self, keyword):
        # 按关键词查询
        pass
    
    def fulltext_search(self, query):
        # 全文搜索
        pass
```

## 6. 性能优化效果预测

### 6.1 查询效率提升
- **分类查询**：从O(n)→O(1)
- **关键词查询**：从O(n)→O(1)
- **全文搜索**：从O(n*m)→O(k) (k为查询词语的文档数)

### 6.2 内存占用减少
- **分层加载**：内存占用减少50%
- **按需加载**：只加载需要的索引部分

### 6.3 扩展性增强
- **支持新增类别**：无需修改核心索引结构
- **支持新增查询类型**：可扩展的查询接口

## 7. 实施计划

### 7.1 第一阶段：索引结构设计 (1周)
- 完成索引结构详细设计
- 确定索引字段和格式
- 设计索引生成算法

### 7.2 第二阶段：工具开发 (2周)
- 开发索引生成工具
- 开发索引查询工具
- 实现倒排索引和分词功能

### 7.3 第三阶段：索引生成 (1周)
- 生成初始索引
- 测试索引质量和完整性
- 优化索引生成速度

### 7.4 第四阶段：性能测试 (1周)
- 测试各种查询的响应时间
- 测试大规模数据下的性能
- 进行压力测试和稳定性测试

### 7.5 第五阶段：部署与维护 (持续)
- 部署索引系统
- 建立索引维护流程
- 定期更新和优化索引

## 8. 维护与更新策略

### 8.1 定期更新
- **每日增量更新**：更新当天新增或修改的内容
- **每周全量更新**：重建整个索引确保完整性

### 8.2 质量监控
- 监控索引的完整性
- 监控查询响应时间
- 监控索引文件大小和内存占用

### 8.3 优化调整
- 根据查询日志调整索引结构
- 优化分词和倒排索引算法
- 调整缓存策略提高常用查询效率

---

设计日期：2025-12-23
版本：1.0