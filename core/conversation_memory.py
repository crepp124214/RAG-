import os
from typing import List, Dict
from .llm_service import LLMService


class ConversationMemory:
    """
    对话摘要记忆服务，实现多轮对话的摘要与记忆管理
    """
    
    def __init__(self, api_key: str = None, max_turns: int = 5, summary_frequency: int = 3):
        """
        初始化对话记忆服务
        :param api_key: LLM API Key
        :param max_turns: 最大保留的对话轮数
        :param summary_frequency: 每多少轮对话进行一次摘要
        """
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        self.max_turns = max_turns
        self.summary_frequency = summary_frequency
        self.llm_service = LLMService(api_key=self.api_key)
        
    def should_summarize(self, conversation_history: List[Dict]) -> bool:
        """
        判断是否需要进行对话摘要
        :param conversation_history: 对话历史
        :return: 是否需要摘要
        """
        # 只计算用户和助手的对话轮数
        user_assistant_turns = [msg for msg in conversation_history 
                              if msg["role"] in ["user", "assistant"]]
        
        return len(user_assistant_turns) >= self.summary_frequency
    
    def summarize_conversation(self, conversation_history: List[Dict]) -> str:
        """
        对对话历史进行摘要
        :param conversation_history: 对话历史
        :return: 对话摘要
        """
        if not conversation_history:
            return ""
            
        try:
            # 构建摘要提示
            summary_prompt = f"""请将以下对话历史进行简洁摘要，保留关键信息和上下文：
            
            对话历史：
            {self._format_conversation(conversation_history)}
            
            摘要要求：
            1. 保留用户的主要问题和助手的关键回答
            2. 突出重要的技术细节和数据
            3. 摘要长度控制在200字以内
            4. 使用中文输出
            """
            
            # 调用LLM进行摘要
            llm = self.llm_service.get_llm(temperature=0.3)
            messages = [{"role": "user", "content": summary_prompt}]
            
            response = llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            print(f"对话摘要失败: {str(e)}")
            return "对话摘要生成失败"
    
    def manage_conversation_memory(self, conversation_history: List[Dict]) -> List[Dict]:
        """
        管理对话记忆，根据需要进行摘要和截断
        :param conversation_history: 原始对话历史
        :return: 处理后的对话历史
        """
        if not conversation_history:
            return []
        
        if not self.should_summarize(conversation_history):
            return conversation_history
            
        # 分离系统消息和对话消息
        system_messages = [msg for msg in conversation_history if msg["role"] == "system"]
        conversation_messages = [msg for msg in conversation_history if msg["role"] != "system"]
        
        # 生成摘要
        summary = self.summarize_conversation(conversation_messages)
        
        # 保留最近的对话轮数
        recent_messages = conversation_messages[-(self.max_turns-1):] if len(conversation_messages) > self.max_turns else conversation_messages
        
        # 构建新的对话历史
        new_history = system_messages.copy()
        
        # 添加摘要作为上下文
        if summary:
            new_history.append({
                "role": "system",
                "content": f"以下是之前对话的摘要：\n{summary}"
            })
        
        # 添加最近的对话
        new_history.extend(recent_messages)
        
        return new_history
    
    def _format_conversation(self, conversation_history: List[Dict]) -> str:
        """
        格式化对话历史为字符串
        :param conversation_history: 对话历史
        :return: 格式化后的对话字符串
        """
        formatted = ""
        for msg in conversation_history:
            role_name = "用户" if msg["role"] == "user" else "助手"
            formatted += f"{role_name}: {msg['content']}\n\n"
        return formatted