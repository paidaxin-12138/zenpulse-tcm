# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import os
import shutil

vector_store_path = 'vector_store/tcm_knowledge_index'

if os.path.exists(vector_store_path):
    print(f'删除索引目录: {vector_store_path}')
    shutil.rmtree(vector_store_path)
    print('索引目录已删除')
    
os.makedirs(vector_store_path, exist_ok=True)
print('重新创建索引目录成功')
print(f'索引目录存在: {os.path.exists(vector_store_path)}')
print(f'索引目录可写: {os.access(vector_store_path, os.W_OK)}')
