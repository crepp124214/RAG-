Set-Location 'D:\agent开发项目\RAG智能文档检索助手'
$env:DATABASE_URL='sqlite:///./data/phase29-final.db'
$env:LLM_MODE='acceptance'
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 *> 'data\backend-acceptance.log'
