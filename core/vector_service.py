import os
from langchain_community.vectorstores import Chroma
from typing import List
from .reranker_service import RerankerService

class VectorService:
    def __init__(self, embeddings, persist_directory: str = "./chroma_db"):
        """
        初始化向量数据库服务
        :param embeddings: 来自 llm_service 的 embedding 模型实例
        :param persist_directory: 持久化保存的本地文件夹路径
        """
        self.embeddings = embeddings
        self.persist_directory = persist_directory
        self.vector_db = None
        
        # 初始化重排服务
        self.reranker = RerankerService()
        
        # 核心逻辑：如果在本地找到了这个文件夹，说明之前存过，直接读取！
        if os.path.exists(self.persist_directory):
            self.vector_db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

    def add_documents(self, chunks: List):
        """
        将文档块存入本地 Chroma 数据库（支持首次创建与增量添加）
        """
        if self.vector_db is None:
            # 首次运行，文件夹还不存在，从头创建并持久化
            self.vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
        else:
            # 文件夹已经存在了，我们在原有的基础上"增量添加"新文档
            self.vector_db.add_documents(chunks)
            
        return self.vector_db

    def get_all_sources(self) -> List[str]:
        """
        ✨ 新增：从 Chroma 数据库底层获取所有已加载的去重文档名称
        """
        if not self.vector_db:
            return []
        
        # 直接读取底层的集合数据，提取所有的 metadatas
        collection_data = self.vector_db._collection.get(include=["metadatas"])
        metadatas = collection_data.get("metadatas", [])
        
        # 使用 set 去重
        sources = set()
        for meta in metadatas:
            if meta and "source" in meta:
                sources.add(meta["source"])
                
        return list(sources)

    def get_retriever(self, k: int = 3, threshold: float = 0.0, selected_sources: List[str] = None):
        """
        ✨ 修改：获取检索器，并支持按指定文档进行过滤
        :param selected_sources: 用户在界面上选中的文档名列表
        """
        if not self.vector_db:
            return None
            
        search_kwargs = {"k": k}
        
        # 核心逻辑：如果用户选择了指定的文档，则加入元数据过滤条件
        if selected_sources and len(selected_sources) > 0:
            if len(selected_sources) == 1:
                search_kwargs["filter"] = {"source": selected_sources[0]}
            else:
                # 多个文件时，使用 Chroma 的 $in 语法匹配多个值
                search_kwargs["filter"] = {"source": {"$in": selected_sources}}

        # 总是使用 similarity 搜索类型，这样可以确保 filter 条件始终生效
        # 然后在获取结果后手动过滤低于阈值的结果
        return self.vector_db.as_retriever(
            search_type="similarity",
                search_kwargs=search_kwargs
            )
    
    def get_parent_documents(self, child_docs: List) -> List:
        """
        根据子文档获取对应的父文档
        :param child_docs: 子文档列表
        :return: 对应的父文档列表
        """
        if not self.vector_db or not child_docs:
            return []
            
        parent_ids = set()
        for doc in child_docs:
            if doc.metadata.get("is_child") and "parent_id" in doc.metadata:
                parent_ids.add(doc.metadata["parent_id"])
        
        # 构建过滤条件，获取所有父文档
        if parent_ids:
            filter_condition = {
                "is_child": False,
                "parent_id": {"$in": list(parent_ids)}
            }
            
            # 获取父文档
            parent_retriever = self.vector_db.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 10, "filter": filter_condition}
            )
            
            # 使用一个虚拟查询来获取所有匹配的父文档
            parent_docs = parent_retriever.invoke("查询") or []
            return parent_docs
        
        return []
    
    def get_retriever_with_parent_context(self, query: str, k: int = 3, 
                                      threshold: float = 0.0, selected_sources: List[str] = None,
                                      initial_k: int = 15) -> List:
        """
        获取带有父文档上下文的检索结果
        :param query: 用户查询
        :param k: 最终返回的文档数量
        :param threshold: 相似度阈值
        :param selected_sources: 选中的文档列表
        :param initial_k: 初始检索的文档数量
        :return: 包含父子上下文的文档列表
        """
        # 第一阶段：使用重排服务获取子文档
        child_docs = self.get_retriever_with_rerank(
            query, k, threshold, selected_sources, initial_k
        ) or []
        
        # 第二阶段：获取对应的父文档
        parent_docs = self.get_parent_documents(child_docs) or []
        
        # 第三阶段：合并结果，子文档在前，父文档在后
        # 为每个文档添加上下文标识
        for doc in child_docs:
            doc.metadata["context_type"] = "child"
            
        for doc in parent_docs:
            doc.metadata["context_type"] = "parent"
            
        # 合并并返回
        return child_docs + parent_docs
    
    def get_retriever_with_rerank(self, query: str, k: int = 3, 
                              threshold: float = 0.0, selected_sources: List[str] = None,
                              initial_k: int = 15) -> List:
        """
        执行两阶段检索：先向量检索，再重排
        :param query: 用户查询
        :param k: 最终返回的文档数量
        :param threshold: 相似度阈值
        :param selected_sources: 选中的文档列表
        :param initial_k: 初始检索的文档数量
        :return: 重排序后的文档列表
        """
        return self.reranker.get_retriever_with_rerank(
            self, query, k, threshold, selected_sources, initial_k
        )