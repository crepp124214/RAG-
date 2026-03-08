import os
import requests
from typing import List, Tuple
from langchain_core.documents import Document


class RerankerService:
    """
    重排服务类，实现两阶段检索架构
    第一阶段：向量检索召回前10-20个片段
    第二阶段：使用重排模型对召回片段进行二次打分，取分值最高的3个
    """
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        """
        初始化重排服务
        :param model_name: 重排模型名称，默认使用 BGE-Reranker
        """
        self.model_name = model_name
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/rerank/models"
        
    def rerank(self, query: str, documents: List[Document], top_k: int = 3) -> List[Document]:
        """
        对检索到的文档进行重排序
        :param query: 用户查询
        :param documents: 向量检索返回的文档列表
        :param top_k: 返回的文档数量
        :return: 重排序后的文档列表
        """
        if not documents:
            return []
            
        # 如果只有少量文档，直接返回
        if len(documents) <= top_k:
            return documents
            
        try:
            # 准备API请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 提取文档内容
            doc_contents = [doc.page_content for doc in documents]
            
            # 构建请求体
            data = {
                "model": self.model_name,
                "query": {
                    "text": query
                },
                "documents": [
                    {"text": content} for content in doc_contents
                ],
                "top_n": top_k
            }
            
            # 发送请求
            response = requests.post(self.api_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                
                # 获取重排序结果
                if "results" in result and result["results"]:
                    reranked_indices = [item["index"] for item in result["results"]]
                    # 根据重排序结果重新排列文档
                    reranked_docs = [documents[i] for i in reranked_indices if i < len(documents)]
                    return reranked_docs[:top_k]
            
            # 如果API调用失败，返回原始文档
            return documents[:top_k]
            
        except Exception as e:
            print(f"重排服务出错: {str(e)}")
            # 出错时返回原始文档的前top_k个
            return documents[:top_k]
            
    def get_retriever_with_rerank(self, vector_service, query: str, k: int = 3, 
                              threshold: float = 0.0, selected_sources: List[str] = None,
                              initial_k: int = 15) -> List[Document]:
        """
        执行两阶段检索：先向量检索，再重排
        :param vector_service: 向量服务实例
        :param query: 用户查询
        :param k: 最终返回的文档数量
        :param threshold: 相似度阈值
        :param selected_sources: 选中的文档列表
        :param initial_k: 初始检索的文档数量
        :return: 重排序后的文档列表
        """
        # 第一阶段：向量检索，获取更多候选文档
        retriever = vector_service.get_retriever(
            k=initial_k, 
            threshold=threshold, 
            selected_sources=selected_sources
        )
        
        if not retriever:
            return []
            
        initial_docs = retriever.invoke(query) or []
        
        # 第二阶段：重排
        reranked_docs = self.rerank(query, initial_docs, top_k=k)
        
        return reranked_docs or []