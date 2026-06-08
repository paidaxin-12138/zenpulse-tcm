import os
import sys
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_vector_db():
    """测试向量数据库功能"""
    try:
        # 1. 加载模型
        print("开始加载嵌入模型...")
        # 获取项目根目录
        project_root = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(project_root, "models", "bge-small-zh-v1.5")
        embeddings = HuggingFaceEmbeddings(
            model_name=model_path,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("嵌入模型加载成功")
        
        # 2. 检查向量数据库路径
        vector_store_path = os.path.join(project_root, "vector_store")
        index_path = os.path.join(vector_store_path, "tcm_knowledge_index")
        print(f"向量数据库路径: {index_path}")
        
        # 3. 加载向量数据库
        if os.path.exists(index_path):
            print("开始加载向量数据库...")
            vector_store = Chroma(
                persist_directory=index_path,
                embedding_function=embeddings
            )
            print("向量数据库加载成功")
            
            # 4. 测试查询功能
            print("\n测试向量数据库查询功能...")
            queries = [
                "中医如何诊断感冒",
                "什么是阴阳五行学说",
                "针灸的原理是什么"
            ]
            
            for query in queries:
                print(f"\n查询: {query}")
                results = vector_store.similarity_search(query, k=3)
                print(f"找到 {len(results)} 个相关结果")
                
                for i, result in enumerate(results, 1):
                    print(f"\n结果 {i}: {result.page_content[:100]}...")
            
            print("\n向量数据库功能测试通过!")
            return True
        else:
            print(f"向量数据库目录不存在: {index_path}")
            return False
            
    except Exception as e:
        print(f"向量数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_vector_db()