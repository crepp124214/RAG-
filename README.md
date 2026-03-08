# RAG智能文档检索助手

## 项目概述

这是一个基于Streamlit构建的RAG（检索增强生成）智能文档检索助手，利用阿里云通义千问大模型和Chroma向量数据库，实现高效的知识库问答系统。项目旨在为用户提供快速、准确的文档内容检索与问答服务。

## 核心功能

1. **多格式文档支持**：支持PDF、DOCX、TXT等多种文档格式的上传与解析
2. **智能向量检索**：使用Chroma向量数据库存储文档嵌入向量，实现语义相似度检索
3. **大模型集成**：集成阿里云通义千问大模型，提供自然语言问答能力
4. **对话记忆管理**：实现多轮对话的记忆与摘要功能，保持对话连贯性
5. **性能监控**：实时监控检索时间、LLM生成时间等性能指标
6. **重排优化**：使用BGE重排模型对检索结果进行二次排序，提高准确性
7. **父子文档检索**：支持父子文档检索机制，提供更全面的上下文

## 技术栈

- **前端框架**：Streamlit
- **大模型服务**：阿里云通义千问（Qwen）
- **向量数据库**：Chroma
- **文档解析**：LangChain
- **嵌入模型**：DashScope Embedding
- **重排模型**：BGE Reranker

## 安装说明

1. 克隆项目到本地
```bash
git clone https://github.com/creep124214/RAG智能文档检索助手.git
cd RAG智能文档检索助手
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置API密钥

创建`.streamlit/secrets.toml`文件，添加以下内容：
```toml
DASHSCOPE_API_KEY = "你的API密钥"
```

或者设置环境变量：
```bash
export DASHSCOPE_API_KEY="你的API密钥"
```

## 使用说明

1. 启动应用
```bash
streamlit run app.py
```

2. 在浏览器中打开显示的URL（通常是`http://localhost:8501`）

3. 使用步骤：
   - 在侧边栏上传文档文件
   - 等待文档处理完成
   - 在聊天界面输入问题
   - 查看回答和相关引用来源

## 配置选项

应用提供多种配置选项，可在侧边栏调整：

- **启用父子文档检索**：是否检索相关片段的父文档
- **启用重排优化**：是否使用重排模型提高检索准确性
- **对话摘要频率**：设置每多少轮对话后进行一次摘要

## 项目结构

RAG智能文档检索助手/
├── 📂 core/                     # 核心业务逻辑 (Backend)

│   ├── __init__.py              

│   ├── document_parser.py       # 文档加载、解析与切片逻辑

│   ├── llm_service.py           # 大模型 API 调用 (通义千问及 Embedding)

│   ├── vector_service.py        # Chroma 向量数据库的存取与检索

│   ├── reranker_service.py      # BGE 重排检索服务 (高级 RAG 功能)

│   └── conversation_memory.py   # 对话上下文与记忆管理

│
├── 📂 chroma_db/                # 本地向量数据库 (程序运行时自动生成)

│   ├── chroma.sqlite3           # 关系型元数据

│   └── (其他二进制数据文件)
│
├── 📄 app.py                    # 🌟 Streamlit 主界面 

├── 📄 run.py                    # Python 启动引导脚本 

├── 📄 start.bat                 # Windows 用户一键启动脚本
│
├── 📄 requirements.txt          # 项目依赖包清单

├── 📄 .gitignore                # Git 忽略文件 

├── 📄 README.md                 # 项目详细说明文档 

└── 📄 LICENSE                   # 开源协议

## 注意事项

1. 需要有效的API密钥
2. 首次使用需要上传文档并等待处理完成
3. 大文档处理可能需要较长时间
4. 建议定期清理向量数据库以释放存储空间

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件

## 贡献

欢迎提交Issue和Pull Request来改进本项目！

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件至：Lin1242146531@gmail.com
