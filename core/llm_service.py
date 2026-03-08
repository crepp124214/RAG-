import os
from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings

class LLMService:
    def __init__(self, api_key: str = None):
        """
        初始化大模型服务
        :param api_key: 阿里云 DashScope API Key。如果不传，则默认从环境变量 DASHSCOPE_API_KEY 中读取
        """
        # 如果传入了 api_key，则设置环境变量
        if api_key:
            os.environ["DASHSCOPE_API_KEY"] = api_key
            
        # 确保环境变量中存在 API Key
        if not os.environ.get("DASHSCOPE_API_KEY"):
            raise ValueError("未找到 DASHSCOPE_API_KEY，请配置环境变量或在初始化时传入。")

    def get_llm(self, model_name: str = "qwen-plus", temperature: float = 0.1):
        """
        获取 Qwen 聊天模型实例
        :param model_name: 模型名称，可选 qwen-turbo, qwen-plus, qwen-max 等
        :param temperature: 温度值，越低回答越严谨（适合 RAG 场景，默认 0.1 防止编造）
        """
        return ChatTongyi(
            model_name= model_name,
            temperature= temperature,
            streaming=True # 开启流式输出，提升页面响应体验
        )

    def get_embeddings(self):
        """
        获取 Qwen 向量化模型实例 (Embedding)
        用于将文档文本转化为向量存入 Chroma
        """
        return DashScopeEmbeddings(
            model="text-embedding-v1"
        )

# 测试代码
#if __name__ == "__main__":
    # 请替换为你的真实 API Key 进行测试
    # os.environ["DASHSCOPE_API_KEY"] = "sk-xxxxxxxx" 
    
    # llm_service = LLMService()
    # llm = llm_service.get_llm()
    # print(llm.invoke("你好，你是谁？").content)