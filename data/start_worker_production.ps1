Set-Location 'D:\agent开发项目\RAG智能文档检索助手'
$env:DATABASE_URL='postgresql+psycopg://postgres:postgres@127.0.0.1:5433/rag_assistant_prod'
Remove-Item Env:LLM_MODE -ErrorAction SilentlyContinue
python -c "from worker.main import main; main()" *> 'data\worker-production.log'
