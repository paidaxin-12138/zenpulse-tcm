# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import os

print('检查vector_store目录:')
vector_store_path = 'vector_store'
print(f'vector_store目录存在: {os.path.exists(vector_store_path)}')

if os.path.exists(vector_store_path):
    print(f'目录内容: {os.listdir(vector_store_path)}')
    
    index_path = os.path.join(vector_store_path, 'tcm_knowledge_index')
    print(f'索引目录存在: {os.path.exists(index_path)}')
    
    if os.path.exists(index_path):
        print(f'索引目录内容: {os.listdir(index_path)}')
        # 检查目录权限
        print(f'目录可写: {os.access(index_path, os.W_OK)}')
        print(f'目录可读: {os.access(index_path, os.R_OK)}')
