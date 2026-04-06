Set-Location 'D:\agent开发项目\RAG智能文档检索助手'
$env:DATABASE_URL='postgresql+psycopg://postgres:postgres@127.0.0.1:5433/rag_assistant_prod'
Remove-Item Env:LLM_MODE -ErrorAction SilentlyContinue
Write-Output "DATABASE_URL=$env:DATABASE_URL" | Out-File -FilePath 'data\backend-production.log' -Encoding utf8
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 *>> 'data\backend-production.log'
