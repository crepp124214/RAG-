# 多模型 API 配置指南

本项目现已支持多种大模型 API，您可以根据需要选择使用。

## 配置方法

在 `.streamlit/secrets.toml` 文件中配置（如果没有此文件，复制 `secrets.toml.example` 并重命名）：

### 方式1: 阿里云 DashScope (通义千问)
```toml
LLM_PROVIDER = "dashscope"
API_KEY = "sk-your-dashscope-api-key"
```

### 方式2: OpenAI
```toml
LLM_PROVIDER = "openai"
API_KEY = "sk-your-openai-api-key"
# LLM_BASE_URL = "https://api.openai.com/v1"  # 可选，使用代理时修改
```

### 方式3: 智谱 AI (GLM)
```toml
LLM_PROVIDER = "zhipu"
API_KEY = "your-zhipu-api-key"
```

### 方式4: DeepSeek
```toml
LLM_PROVIDER = "deepseek"
API_KEY = "sk-your-deepseek-api-key"
```

### 方式5: 兼容旧配置
```toml
DASHSCOPE_API_KEY = "sk-your-dashscope-api-key"
```

## 支持的模型

- **DashScope**: qwen-plus, qwen-turbo, qwen-max
- **OpenAI**: gpt-3.5-turbo, gpt-4, gpt-4-turbo
- **智谱**: glm-4, glm-3-turbo
- **DeepSeek**: deepseek-chat, deepseek-coder

## 注意事项

1. 不同模型的 API 调用费用不同，请查看各平台的定价
2. 网络连接问题可能导致 ConnectionResetError，请检查网络稳定性
3. 确保 API Key 有足够的额度
