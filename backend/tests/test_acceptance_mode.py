from __future__ import annotations

from sqlalchemy import select

from backend.app.models import Chunk, Document, Task
from backend.app.orchestrators.document_ingestion import DocumentIngestionOrchestrator
from backend.app.services.chunking_service import DocumentChunkingService
from backend.app.services.parser_service import DocumentParserService
from backend.app.services.qa_service import KnowledgeBaseQAService
from backend.app.services.retrieval_service import RetrievalService
from backend.infrastructure.database import create_database_engine, create_session_factory, initialize_database
from backend.infrastructure.llm import create_chat_client, create_embedding_client, create_reranker_client
from backend.tests.support import build_test_settings, create_workspace_temp_dir


def _create_document_with_task(session_factory, storage_path):
    with session_factory() as db_session:
        document = Document(
            name=storage_path.name,
            file_type='txt',
            status='UPLOADED',
            storage_path=str(storage_path),
        )
        db_session.add(document)
        db_session.flush()

        task = Task(
            document_id=document.id,
            task_type='INGESTION',
            status='UPLOADED',
        )
        db_session.add(task)
        db_session.commit()
        return document.id, task.id


def test_acceptance_mode_clients_support_ingestion_and_query() -> None:
    temp_dir = create_workspace_temp_dir('acceptance-mode')
    storage_path = temp_dir / 'demo.txt'
    storage_path.write_text('第一段：系统支持上传文档。\n第二段：系统支持引用回答。\n第三段：系统支持任务状态查询。', encoding='utf-8')

    settings = build_test_settings(temp_dir, overrides={'LLM_MODE': 'acceptance'})
    engine = create_database_engine(settings.database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    document_id, task_id = _create_document_with_task(session_factory, storage_path)

    orchestrator = DocumentIngestionOrchestrator(
        session_factory=session_factory,
        parser_service=DocumentParserService(),
        chunking_service=DocumentChunkingService(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        ),
        embedding_client=create_embedding_client(settings),
    )
    result = orchestrator.process(document_id=document_id, task_id=task_id)

    retrieval_service = RetrievalService(
        embedding_client=create_embedding_client(settings),
        reranker_client=create_reranker_client(settings),
        vector_top_k=settings.vector_top_k,
        rerank_top_n=settings.rerank_top_n,
    )
    qa_service = KnowledgeBaseQAService(
        retrieval_service=retrieval_service,
        chat_client=create_chat_client(settings),
    )

    with session_factory() as db_session:
        chunks = db_session.scalars(select(Chunk).where(Chunk.document_id == document_id)).all()
        qa_result = qa_service.ask(db_session, query='系统支持什么能力')

    engine.dispose()

    assert result['status'] == 'READY'
    assert len(chunks) >= 1
    assert all(chunk.embedding is not None for chunk in chunks)
    assert qa_result.citations
    assert '验收模式' in qa_result.answer
