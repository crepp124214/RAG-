# RAG智能文档检索助手 - 项目结构说明


```
RAG智能文档检索助手/
├── 📂 core/                     # 核心业务逻辑 (Backend)
│   ├── __init__.py              # 🌟 标识这是一个 Python 包
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
├── 📄 app.py                    # 🌟 Streamlit 主界面 (UI 视图层)
├── 📄 run.py                    # Python 启动引导脚本 (如用于定制启动参数)
├── 📄 start.bat                 # Windows 用户一键启动脚本
│
├── 📄 requirements.txt          # 项目依赖包清单
├── 📄 .gitignore                # Git 忽略文件 (已包含 __pycache__ 和 chroma_db 等)
├── 📄 README.md                 # 项目详细说明文档 (给面试官看的门面)
└── 📄 LICENSE                   # 开源协议
```
