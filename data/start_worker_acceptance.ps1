Set-Location 'D:\agent开发项目\RAG智能文档检索助手'
$env:DATABASE_URL='sqlite:///./data/phase29-final.db'
$env:LLM_MODE='acceptance'
python -c "from worker.main import main; main()" *> 'data\worker-acceptance.log'
