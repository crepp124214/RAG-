import os
from typing import Optional

class LLMService:
    def __init__(self, api_key: str = None, provider: str = None, base_url: str = None):
        """
        初始化大模型服务，支持多种 API 提供商
        :param api_key: API Key
        :param provider: 提供商 (dashscope/openai/zhipu/deepseek 等)
        :param base_url: 自定义 API 地址
        """
        self.provider = provider or os.environ.get("LLM_PROVIDER", "dashscope")
        self.api_key = api_key or os.environ.get("API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
        self.base_url = base_url or os.environ.get("LLM_BASE_URL")
        
        if not self.api_key:
            raise ValueError("未找到 API_KEY，请配置环境变量或在初始化时传入")

    def get_llm(self, model_name: str = None, temperature: float = 0.1):
        """获取聊天模型实例"""
        if self.provider == "dashscope":
            from langchain_community.chat_models import ChatTongyi
            os.environ["DASHSCOPE_API_KEY"] = self.api_key
            return ChatTongyi(model_name=model_name or "qwen-plus", temperature=temperature, streaming=True)
        
        elif self.provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(api_key=self.api_key, model=model_name or "gpt-3.5-turbo",
                            temperature=temperature, streaming=True, base_url=self.base_url)
        
        elif self.provider == "zhipu":
            from langchain_community.chat_models import ChatZhipuAI
            return ChatZhipuAI(api_key=self.api_key, model=model_name or "glm-4",
                             temperature=temperature, streaming=True)
        
        elif self.provider == "deepseek":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(api_key=self.api_key, model=model_name or "deepseek-chat",
                            base_url=self.base_url or "https://api.deepseek.com",
                            temperature=temperature, streaming=True)
        
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")

    def get_embeddings(self):
        """获取向量化模型实例"""
        if self.provider == "dashscope":
            from langchain_community.embeddings import DashScopeEmbeddings
            os.environ["DASHSCOPE_API_KEY"] = self.api_key
            return DashScopeEmbeddings(model="text-embedding-v1")
        
        elif self.provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(api_key=self.api_key, base_url=self.base_url)
        
        elif self.provider == "zhipu":
            from langchain_community.embeddings import ZhipuAIEmbeddings
            return ZhipuAIEmbeddings(api_key=self.api_key)
        
        elif self.provider == "deepseek":
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(api_key=self.api_key,
                                  base_url=self.base_url or "https://api.deepseek.com")
        
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")

# 测试代码
#if __name__ == "__main__":
    # 请替换为你的真实 API Key 进行测试
    # os.environ["DASHSCOPE_API_KEY"] = "sk-xxxxxxxx" 
    
    # llm_service = LLMService()
    # llm = llm_service.get_llm()
    # print(llm.invoke("你好，你是谁？").content)