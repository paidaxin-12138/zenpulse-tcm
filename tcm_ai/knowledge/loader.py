# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import os
import json
from typing import List, Dict, Any

from tcm_ai.core.paths import normalize_knowledge_path


class TCMKnowledgeLoader:
    """
    中医知识文件加载器，支持多种格式的知识文件加载
    """
    
    def __init__(self, knowledge_dir: str):
        """
        初始化知识加载器
        
        Args:
            knowledge_dir: 知识文件目录
        """
        self.knowledge_dir = knowledge_dir
        self.supported_formats = ['.txt', '.pdf', '.docx', '.json']

    def _storage_path(self, file_path: str) -> str:
        return normalize_knowledge_path(file_path, self.knowledge_dir)

    def load_knowledge_files(self, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        加载指定目录下的所有知识文件
        
        Args:
            recursive: 是否递归加载子目录
        
        Returns:
            加载的知识列表
        """
        knowledge_items = []
        
        if recursive:
            for root, dirs, files in os.walk(self.knowledge_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_supported_file(file_path):
                        try:
                            items = self._load_file(file_path)
                            knowledge_items.extend(items)
                        except Exception as e:
                            print(f"加载文件失败 {file_path}: {e}")
        else:
            for file in os.listdir(self.knowledge_dir):
                file_path = os.path.join(self.knowledge_dir, file)
                if os.path.isfile(file_path) and self._is_supported_file(file_path):
                    try:
                        items = self._load_file(file_path)
                        knowledge_items.extend(items)
                    except Exception as e:
                        print(f"加载文件失败 {file_path}: {e}")
        
        return knowledge_items
    
    def _is_supported_file(self, file_path: str) -> bool:
        """
        检查文件是否为支持的格式
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否支持该文件格式
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_formats
    
    def _load_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        根据文件格式加载文件内容
        
        Args:
            file_path: 文件路径
        
        Returns:
            加载的知识列表
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.txt':
            return self._load_txt_file(file_path)
        elif ext == '.pdf':
            return self._load_pdf_file(file_path)
        elif ext == '.docx':
            return self._load_docx_file(file_path)
        elif ext == '.json':
            return self._load_json_file(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def _load_txt_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        加载TXT文件，优化了大文件处理和分块策略
        
        Args:
            file_path: TXT文件路径
        
        Returns:
            加载的知识列表
        """
        knowledge_items = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 更智能的文本分割策略，适合处理大文件
        # 1. 首先按章节或大标题分割
        major_sections = self._split_by_major_sections(content)
        
        section_count = 1
        for section_title, section_content in major_sections:
            # 2. 然后在每个大章节内按段落分割
            paragraphs = [p.strip() for p in section_content.split('\n\n') if p.strip()]
            
            paragraph_count = 1
            for paragraph in paragraphs:
                # 3. 对于特别长的段落，进行更细粒度的分割（超过1000字符）
                if len(paragraph) > 1000:
                    sub_paragraphs = self._split_long_paragraph(paragraph)
                    for sub_p in sub_paragraphs:
                        if sub_p.strip():
                            item_title = f"{section_title}_第{section_count}节_段落{paragraph_count}"
                            knowledge_items.append({
                                'title': item_title,
                                'content': sub_p.strip(),
                                'source': self._storage_path(file_path),
                                'type': 'text',
                                'category': self._get_file_category(file_path),
                                'section': section_title,
                                'file_path': self._storage_path(file_path),
                                'section_number': section_count,
                                'paragraph_number': paragraph_count
                            })
                            paragraph_count += 1
                else:
                    item_title = f"{section_title}_第{section_count}节_段落{paragraph_count}"
                    knowledge_items.append({
                        'title': item_title,
                        'content': paragraph,
                        'source': self._storage_path(file_path),
                        'type': 'text',
                        'category': self._get_file_category(file_path),
                        'section': section_title,
                        'file_path': self._storage_path(file_path),
                        'section_number': section_count,
                        'paragraph_number': paragraph_count
                    })
                    paragraph_count += 1
            section_count += 1
        
        return knowledge_items
    
    def _split_by_major_sections(self, content: str) -> List[tuple]:
        """
        按主要章节分割文本
        
        Args:
            content: 要分割的文本
        
        Returns:
            分割后的章节列表，每个元素为(title, content)
        """
        import re
        
        # 定义主要章节的正则表达式模式
        # 支持：1. 第一章、2. 第一节、一、、（一）等格式
        major_patterns = [
            r'^(?:第[一二三四五六七八九十百千万]+[章节]|第\d+[章节]|[一二三四五六七八九十百千万]+、|\d+\.)\s*',
            r'^\(一\)|\(二\)|\(三\)|\(\d+\)\s*'
        ]
        
        sections = []
        current_section = "默认章节"
        current_content = []
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是新章节
            new_section = None
            for pattern in major_patterns:
                match = re.match(pattern, line)
                if match:
                    new_section = line
                    break
            
            if new_section:
                # 保存当前章节
                if current_content:
                    sections.append((current_section, '\n'.join(current_content)))
                # 开始新章节
                current_section = new_section
                current_content = [line[match.end():].strip()] if len(line) > match.end() else []
            else:
                # 添加到当前章节
                current_content.append(line)
        
        # 保存最后一个章节
        if current_content:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections
    
    def _split_long_paragraph(self, paragraph: str, max_length: int = 800) -> List[str]:
        """
        分割长段落
        
        Args:
            paragraph: 要分割的长段落
            max_length: 每个子段落的最大长度
        
        Returns:
            分割后的子段落列表
        """
        import re
        
        sub_paragraphs = []
        current_pos = 0
        paragraph_length = len(paragraph)
        
        while current_pos < paragraph_length:
            # 找到合适的分割点
            end_pos = min(current_pos + max_length, paragraph_length)
            
            # 如果不是段落结尾，尝试找到合适的标点符号作为分割点
            if end_pos < paragraph_length:
                # 查找中文标点符号作为分割点（使用字符串切片实现反向搜索）
                # 取当前位置到end_pos的字符串并反转，搜索标点符号
                reversed_segment = paragraph[:end_pos][::-1]
                split_pos = re.search(r'[。！？；，、]', reversed_segment)
                if split_pos:
                    # 计算原始字符串中的实际位置
                    end_pos = end_pos - split_pos.start()
            
            # 添加子段落
            sub_paragraphs.append(paragraph[current_pos:end_pos].strip())
            current_pos = end_pos
        
        return sub_paragraphs
    
    def _load_pdf_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        加载PDF文件
        
        Args:
            file_path: PDF文件路径
        
        Returns:
            加载的知识列表
        """
        knowledge_items = []
        
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                if text:
                    # 简单的文本分割策略
                    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                    
                    for i, paragraph in enumerate(paragraphs):
                        knowledge_items.append({
                            'title': f"{os.path.basename(file_path)}_第{page_num+1}页_段落{i+1}",
                            'content': paragraph,
                            'source': self._storage_path(file_path),
                            'type': 'pdf',
                            'page': page_num + 1,
                            'category': self._get_file_category(file_path),
                            'file_path': self._storage_path(file_path),
                        })
        except ImportError:
            print("未安装PyPDF2，请使用pip install pypdf2安装")
        
        return knowledge_items
    
    def _load_docx_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        加载DOCX文件
        
        Args:
            file_path: DOCX文件路径
        
        Returns:
            加载的知识列表
        """
        knowledge_items = []
        
        try:
            from docx import Document
            
            doc = Document(file_path)
            
            for i, para in enumerate(doc.paragraphs):
                text = para.text.strip()
                
                if text:
                    knowledge_items.append({
                        'title': f"{os.path.basename(file_path)}_段落{i+1}",
                        'content': text,
                        'source': self._storage_path(file_path),
                        'type': 'docx',
                        'category': self._get_file_category(file_path),
                        'file_path': self._storage_path(file_path),
                    })
        except ImportError:
            print("未安装python-docx，请使用pip install python-docx安装")
        
        return knowledge_items
    
    def _load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        加载JSON文件
        
        Args:
            file_path: JSON文件路径
        
        Returns:
            加载的知识列表
        """
        knowledge_items = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 支持单条知识和知识列表两种格式
        if isinstance(data, list):
            for item in data:
                # 对于临床案例，不需要content字段
                is_case_file = 'cases' in file_path.lower()
                if 'content' in item or is_case_file:
                    # 确保每个知识项都有必要的字段
                    rel = self._storage_path(file_path)
                    item.setdefault('title', item.get('title', os.path.basename(file_path)))
                    item.setdefault('source', rel)
                    item.setdefault('type', item.get('type', 'json'))
                    item.setdefault('category', item.get('category', self._get_file_category(file_path)))
                    item.setdefault('file_path', rel)
                    item['source'] = normalize_knowledge_path(item.get('source', rel), self.knowledge_dir)
                    item['file_path'] = normalize_knowledge_path(item.get('file_path', rel), self.knowledge_dir)
                    knowledge_items.append(item)
        elif isinstance(data, dict):
            # 对于临床案例，不需要content字段
            is_case_file = 'cases' in file_path.lower()
            if 'content' in data or is_case_file:
                rel = self._storage_path(file_path)
                data.setdefault('title', data.get('title', os.path.basename(file_path)))
                data.setdefault('source', rel)
                data.setdefault('type', data.get('type', 'json'))
                data.setdefault('category', data.get('category', self._get_file_category(file_path)))
                data.setdefault('file_path', rel)
                data['source'] = normalize_knowledge_path(data.get('source', rel), self.knowledge_dir)
                data['file_path'] = normalize_knowledge_path(data.get('file_path', rel), self.knowledge_dir)
                knowledge_items.append(data)
        
        return knowledge_items
    
    def _get_file_category(self, file_path: str) -> str:
        """
        根据文件路径获取知识分类
        
        Args:
            file_path: 文件路径
        
        Returns:
            知识分类
        """
        # 根据目录结构推断分类
        relative_path = os.path.relpath(file_path, self.knowledge_dir)
        
        if 'basic_theory' in relative_path:
            return '基础理论'
        elif 'diagnosis' in relative_path:
            return '诊断学'
        elif 'treatment' in relative_path:
            return '治疗学'
        elif 'constitution' in relative_path:
            return '体质学'
        elif 'cases' in relative_path:
            return '临床案例'
        else:
            return '其他'

class TCMAgentKnowledgeManager:
    """
    中医知识库管理器，用于管理和维护中医知识库，优化后支持大量知识和案例的高效管理
    """
    
    def __init__(self, knowledge_dir: str, index_path: str = None):
        """
        初始化知识库管理器
        
        Args:
            knowledge_dir: 知识文件目录
            index_path: 索引文件路径
        """
        self.knowledge_dir = knowledge_dir
        self.index_path = index_path or os.path.join(knowledge_dir, 'tcm_knowledge_index.json')
        self.loader = TCMKnowledgeLoader(knowledge_dir)
        self.knowledge_base = []
        self.knowledge_index = {}
        self.case_index = {}
        
        # 如果索引文件存在，加载索引
        if os.path.exists(self.index_path):
            self.load_index()
        else:
            # 初始化索引
            self.build_index()
    
    def load_all_knowledge(self) -> List[Dict[str, Any]]:
        """
        加载所有知识，支持批量处理和进度显示
        
        Returns:
            所有知识列表
        """
        self.knowledge_base = self.loader.load_knowledge_files()
        self.build_index()
        self.save_index()
        return self.knowledge_base
    
    def load_knowledge_batch(self, batch_size: int = 1000) -> List[Dict[str, Any]]:
        """
        批量加载知识，适合处理大量知识文件
        
        Args:
            batch_size: 每次加载的知识文件数量
            
        Returns:
            所有知识列表
        """
        import os
        import time
        
        knowledge_files = []
        
        # 收集所有知识文件
        for root, dirs, files in os.walk(self.knowledge_dir):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.loader.supported_formats:
                    knowledge_files.append(file_path)
        
        # 批量加载
        total_files = len(knowledge_files)
        print(f"开始加载 {total_files} 个知识文件")
        
        self.knowledge_base = []
        start_time = time.time()
        
        for i in range(0, len(knowledge_files), batch_size):
            batch_files = knowledge_files[i:i+batch_size]
            batch_start = time.time()
            
            batch_items = []
            for file_path in batch_files:
                try:
                    knowledge_items = self.loader._load_file(file_path)
                    batch_items.extend(knowledge_items)
                except Exception as e:
                    print(f"加载文件失败 {file_path}: {e}")
            
            # 批量添加知识项，延迟保存索引
            for item in batch_items:
                self.add_knowledge_item(item, save_index=False)
            
            batch_time = time.time() - batch_start
            progress = min((i + batch_size), total_files)
            print(f"已加载 {progress}/{total_files} 个文件，本批耗时 {batch_time:.2f} 秒")
        
        # 最终一次性保存索引
        self.build_index()
        self.save_index()
        
        total_time = time.time() - start_time
        print(f"所有知识加载完成，共加载 {len(self.knowledge_base)} 个知识项，耗时 {total_time:.2f} 秒")
        return self.knowledge_base
    
    def build_index(self):
        """
        构建知识索引，提高搜索效率
        """
        import time
        start_time = time.time()
        
        # 构建知识分类索引
        self.knowledge_index = {}
        for item in self.knowledge_base:
            category = item.get('category', '其他')
            if category not in self.knowledge_index:
                self.knowledge_index[category] = []
            self.knowledge_index[category].append(item)
        
        # 构建临床案例索引，支持快速检索
        self.case_index = {
            'symptom_index': {},
            'syndrome_index': {},
            'age_index': {},
            'gender_index': {},
            'diagnosis_index': {}  # 添加诊断索引
        }
        
        # 缓存案例字典，避免多次查询
        self.cases_dict = {}
        
        for case in [item for item in self.knowledge_base if item.get('category') == '临床案例']:
            case_id = case.get('patient_id', '')
            self.cases_dict[case_id] = case
            
            # 症状索引
            symptoms = case.get('symptoms', '').split('，')
            for symptom in symptoms:
                symptom = symptom.strip()
                if symptom:
                    if symptom not in self.case_index['symptom_index']:
                        self.case_index['symptom_index'][symptom] = []
                    self.case_index['symptom_index'][symptom].append(case_id)
            
            # 证型索引
            syndrome = case.get('syndrome', '')
            if syndrome:
                if syndrome not in self.case_index['syndrome_index']:
                    self.case_index['syndrome_index'][syndrome] = []
                self.case_index['syndrome_index'][syndrome].append(case_id)
            
            # 年龄索引
            age = case.get('age', 0)
            age_group = f"{age//10*10}-{age//10*10+9}"
            if age_group not in self.case_index['age_index']:
                self.case_index['age_index'][age_group] = []
            self.case_index['age_index'][age_group].append(case_id)
            
            # 性别索引
            gender = case.get('gender', '')
            if gender:
                if gender not in self.case_index['gender_index']:
                    self.case_index['gender_index'][gender] = []
                self.case_index['gender_index'][gender].append(case_id)
            
            # 诊断索引
            diagnosis = case.get('diagnosis', '')
            if diagnosis:
                if diagnosis not in self.case_index['diagnosis_index']:
                    self.case_index['diagnosis_index'][diagnosis] = []
                self.case_index['diagnosis_index'][diagnosis].append(case_id)
        
        print(f"索引构建完成，耗时 {time.time() - start_time:.2f} 秒")
    
    def save_index(self):
        """
        保存知识库索引，优化后使用更高效的存储格式
        """
        import json
        import time
        
        start_time = time.time()
        
        index_data = {
            'knowledge_count': len(self.knowledge_base),
            'knowledge_items': self.knowledge_base,
            'knowledge_index': self.knowledge_index,
            'case_index': self.case_index,
            'index_version': '1.2'
        }
        
        # 使用更高效的JSON存储方式，减少缩进以提高存储效率
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, separators=(',', ':'))
        
        print(f"索引保存完成，耗时 {time.time() - start_time:.2f} 秒，索引大小 {os.path.getsize(self.index_path)/1024:.2f} KB")
    
    def load_index(self):
        """
        加载知识库索引
        """
        import json
        
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                self.knowledge_base = index_data.get('knowledge_items', [])
                self.knowledge_index = index_data.get('knowledge_index', {})
                self.case_index = index_data.get('case_index', {
                    'symptom_index': {},
                    'syndrome_index': {},
                    'age_index': {},
                    'gender_index': {},
                    'diagnosis_index': {}  # 包含诊断索引
                })
                
                # 确保cases_dict已构建
                self.cases_dict = {}
                for case in [item for item in self.knowledge_base if item.get('category') == '临床案例']:
                    case_id = case.get('patient_id', '')
                    self.cases_dict[case_id] = case
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"加载索引失败: {e}，正在重建索引...")
            self.build_index()
            self.save_index()
    
    def search_knowledge(self, query: str, top_k: int = 10, category_filter: str = None, content_only: bool = False) -> List[Dict[str, Any]]:
        """
        搜索知识（支持分类过滤、关键词匹配和相关性排序）
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            category_filter: 分类过滤（如"临床案例"）
            content_only: 是否只搜索内容（不搜索标题）
            
        Returns:
            相关知识列表
        """
        import re
        
        # 根据分类过滤知识
        if category_filter:
            knowledge_items = self.knowledge_index.get(category_filter, [])
        else:
            knowledge_items = self.knowledge_base
        
        results = []
        
        # 改进的关键词匹配，支持多关键词和相关性评分
        for item in knowledge_items:
            # 关键词匹配
            search_text = item['content']
            if not content_only:
                search_text += ' ' + item['title']
            
            # 计算匹配得分
            score = 0
            for keyword in query.split(' '):
                keyword = keyword.strip()
                if not keyword:
                    continue
                
                # 完全匹配
                if keyword in search_text:
                    score += 2
                
                # 部分匹配
                if re.search(keyword, search_text):
                    score += 1
            
            if score > 0:
                results.append((score, item))
        
        # 按相关性得分排序
        results.sort(key=lambda x: x[0], reverse=True)
        
        # 返回结果
        return [item for score, item in results[:top_k]]
    
    def search_cases(self, diagnosis_query: str, top_k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        搜索中医临床案例，使用索引提高检索效率
        
        Args:
            diagnosis_query: 诊断查询（症状、证型等）
            top_k: 返回结果数量
            filters: 过滤条件（如年龄、性别、证型等）
            
        Returns:
            相关案例列表
        """
        import re
        from collections import defaultdict
        
        filters = filters or {}
        candidate_cases = []
        
        # 确保cases_dict已构建
        if not hasattr(self, 'cases_dict') or not self.cases_dict:
            self.cases_dict = {}
            for case in [item for item in self.knowledge_base if item.get('category') == '临床案例']:
                case_id = case.get('patient_id', '')
                self.cases_dict[case_id] = case
        
        # 使用索引进行快速过滤
        if filters:
            filtered_case_ids = set(self.cases_dict.keys())
            
            # 诊断过滤
            if 'diagnosis' in filters:
                diagnosis = filters['diagnosis']
                if diagnosis in self.case_index['diagnosis_index']:
                    diagnosis_case_ids = set(self.case_index['diagnosis_index'][diagnosis])
                    filtered_case_ids.intersection_update(diagnosis_case_ids)
            
            # 证型过滤
            if 'syndrome' in filters:
                syndrome = filters['syndrome']
                if syndrome in self.case_index['syndrome_index']:
                    syndrome_case_ids = set(self.case_index['syndrome_index'][syndrome])
                    filtered_case_ids.intersection_update(syndrome_case_ids)
            
            # 性别过滤
            if 'gender' in filters:
                gender = filters['gender']
                if gender in self.case_index['gender_index']:
                    gender_case_ids = set(self.case_index['gender_index'][gender])
                    filtered_case_ids.intersection_update(gender_case_ids)
            
            # 年龄过滤
            if 'age' in filters:
                age = filters['age']
                age_group = f"{age//10*10}-{age//10*10+9}"
                if age_group in self.case_index['age_index']:
                    age_case_ids = set(self.case_index['age_index'][age_group])
                    filtered_case_ids.intersection_update(age_case_ids)
            
            # 症状过滤
            if 'symptom' in filters:
                symptom = filters['symptom']
                if symptom in self.case_index['symptom_index']:
                    symptom_case_ids = set(self.case_index['symptom_index'][symptom])
                    filtered_case_ids.intersection_update(symptom_case_ids)
            
            # 获取过滤后的案例
            candidate_cases = [self.cases_dict[case_id] for case_id in filtered_case_ids if case_id in self.cases_dict]
        else:
            # 没有过滤条件，使用所有案例
            candidate_cases = list(self.cases_dict.values())
        
        # 对候选案例进行诊断查询匹配
        results = []
        for case in candidate_cases:
            # 构建案例文本
            case_text = f"{case.get('symptoms', '')} {case.get('diagnosis', '')} {case.get('syndrome', '')} {case.get('treatment', '')}"
            
            # 计算匹配得分
            score = 0
            for keyword in diagnosis_query.split(' '):
                keyword = keyword.strip()
                if not keyword:
                    continue
                
                # 完全匹配
                if keyword in case_text:
                    score += 3
                
                # 部分匹配
                if re.search(keyword, case_text):
                    score += 1
            
            if score > 0:
                results.append((score, case))
        
        # 按相关性得分排序
        results.sort(key=lambda x: x[0], reverse=True)
        
        # 返回结果
        return [case for score, case in results[:top_k]]
    
    def add_case(self, case: Dict[str, Any]):
        """
        添加临床案例，并更新索引
        
        Args:
            case: 案例数据，应包含以下字段：
                - patient_id: 患者ID
                - age: 年龄
                - gender: 性别
                - symptoms: 症状
                - diagnosis: 诊断
                - syndrome: 中医证型
                - treatment: 治疗方案
                - efficacy: 疗效
                - date: 日期
        """
        # 确保案例包含必要的字段
        required_fields = ['patient_id', 'age', 'gender', 'symptoms', 'diagnosis', 'syndrome', 'treatment', 'efficacy', 'date']
        for field in required_fields:
            if field not in case:
                raise ValueError(f"案例缺少必要字段: {field}")
        
        # 设置案例分类
        case['category'] = '临床案例'
        case['type'] = 'json'
        case['source'] = '临床案例数据库'
        
        # 添加到知识库
        self.add_knowledge_item(case)
    
    def add_knowledge_item(self, item: Dict[str, Any], save_index: bool = True):
        """
        添加知识项，并更新索引
        
        Args:
            item: 知识项
            save_index: 是否立即保存索引，批量添加时可设置为False以提高性能
        """
        self.knowledge_base.append(item)
        
        # 更新分类索引
        category = item.get('category', '其他')
        if category not in self.knowledge_index:
            self.knowledge_index[category] = []
        self.knowledge_index[category].append(item)
        
        # 如果是临床案例，更新案例索引
        if category == '临床案例':
            case_id = item.get('patient_id', '')
            
            # 更新症状索引
            symptoms = item.get('symptoms', '').split('，')
            for symptom in symptoms:
                symptom = symptom.strip()
                if symptom:
                    if symptom not in self.case_index['symptom_index']:
                        self.case_index['symptom_index'][symptom] = []
                    self.case_index['symptom_index'][symptom].append(case_id)
            
            # 更新证型索引
            syndrome = item.get('syndrome', '')
            if syndrome:
                if syndrome not in self.case_index['syndrome_index']:
                    self.case_index['syndrome_index'][syndrome] = []
                self.case_index['syndrome_index'][syndrome].append(case_id)
            
            # 更新年龄索引
            age = item.get('age', 0)
            age_group = f"{age//10*10}-{age//10*10+9}"
            if age_group not in self.case_index['age_index']:
                self.case_index['age_index'][age_group] = []
            self.case_index['age_index'][age_group].append(case_id)
            
            # 更新性别索引
            gender = item.get('gender', '')
            if gender:
                if gender not in self.case_index['gender_index']:
                    self.case_index['gender_index'][gender] = []
                self.case_index['gender_index'][gender].append(case_id)
            
            # 更新诊断索引
            diagnosis = item.get('diagnosis', '')
            if diagnosis:
                if diagnosis not in self.case_index['diagnosis_index']:
                    self.case_index['diagnosis_index'][diagnosis] = []
                self.case_index['diagnosis_index'][diagnosis].append(case_id)
        
        # 保存更新后的索引
        if save_index:
            self.save_index()
    
    def remove_knowledge_item(self, item_id: str):
        """
        删除知识项
        
        Args:
            item_id: 知识项ID
        """
        self.knowledge_base = [item for item in self.knowledge_base if item.get('id') != item_id]
        self.save_index()
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            统计信息
        """
        categories = {}
        file_types = {}
        sources = {}
        
        # 临床案例统计
        case_stats = {
            'total': 0,
            'by_gender': {'男': 0, '女': 0},
            'by_age_group': {},
            'by_diagnosis': {},
            'by_syndrome': {}
        }
        
        for item in self.knowledge_base:
            # 分类统计
            category = item.get('category', '其他')
            categories[category] = categories.get(category, 0) + 1
            
            # 文件类型统计
            file_type = item.get('type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # 来源统计
            source = item.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
            
            # 临床案例统计
            if category == '临床案例':
                case_stats['total'] += 1
                
                # 性别统计
                gender = item.get('gender', 'unknown')
                if gender in case_stats['by_gender']:
                    case_stats['by_gender'][gender] += 1
                
                # 年龄组统计
                age = item.get('age', 0)
                age_group = f"{age//10*10}-{age//10*10+9}"
                case_stats['by_age_group'][age_group] = case_stats['by_age_group'].get(age_group, 0) + 1
                
                # 诊断统计
                diagnosis = item.get('diagnosis', 'unknown')
                case_stats['by_diagnosis'][diagnosis] = case_stats['by_diagnosis'].get(diagnosis, 0) + 1
                
                # 证型统计
                syndrome = item.get('syndrome', 'unknown')
                case_stats['by_syndrome'][syndrome] = case_stats['by_syndrome'].get(syndrome, 0) + 1
        
        return {
            'total_items': len(self.knowledge_base),
            'categories': categories,
            'file_types': file_types,
            'sources': sources,
            'case_stats': case_stats
        }
