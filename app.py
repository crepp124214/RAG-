import streamlit as st
from core.llm_service import LLMService
from core.document_parser import DocumentParser
from core.vector_service import VectorService
from core.conversation_memory import ConversationMemory
import os
import time

# ==========================================
# 1. 后端鉴权封装 (核心修改：不再通过 UI 传递 API_KEY)
# ==========================================
def get_backend_api_key():
    """彻底封装在后端，优先读取 secrets，其次读取环境变量"""
    api_key = st.secrets.get("DASHSCOPE_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        st.error("🚨 系统配置错误：未在后端检测到 DASHSCOPE_API_KEY。请检查 .streamlit/secrets.toml。")
        st.stop()
    return api_key


def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'vector_store_ready' not in st.session_state:
        st.session_state.vector_store_ready = False
    if 'vector_service' not in st.session_state:
        st.session_state.vector_service = None
    if 'all_sources' not in st.session_state:
        st.session_state.all_sources = []
    if 'performance_stats' not in st.session_state:
        st.session_state.performance_stats = {
            'retrieval_time': 0,
            'llm_time': 0,
            'total_time': 0,
            'token_count': 0
        }

# ==========================================
# 2. 侧边栏 UI (移除 API 输入框)
# ==========================================
def render_sidebar(api_key):
    st.sidebar.header("⚙️ 检索配置")
    similarity_threshold = st.sidebar.slider("检索相似度阈值", 0.0, 1.0, 0.6, 0.05)
    
    # 高级检索选项
    with st.sidebar.expander("🔧 高级检索选项", expanded=False):
        use_parent_context = st.checkbox(
            "启用父子文档检索",
            value=True,
            help="自动检索相关片段的父文档，提供更全面的上下文"
        )
        
        use_rerank = st.checkbox(
            "启用重排优化",
            value=True,
            help="使用重排模型对检索结果进行二次排序，提高准确性"
        )
        
        memory_frequency = st.slider(
            "对话摘要频率",
            min_value=2,
            max_value=10,
            value=3,
            step=1,
            help="每多少轮对话后进行一次摘要"
        )
    
    st.sidebar.markdown("---")
    st.sidebar.header("🗄️ 知识库管理")
    
    # 加载逻辑
    if st.sidebar.button("🔄 加载本地历史库", use_container_width=True):
        with st.spinner("正在连接数据..."):
            try:
                llm_svc = LLMService(api_key=api_key)
                vec_svc = VectorService(embeddings=llm_svc.get_embeddings())
                if vec_svc.vector_db:
                    st.session_state.vector_service = vec_svc
                    st.session_state.all_sources = vec_svc.get_all_sources()
                    st.session_state.vector_store_ready = True
                    st.sidebar.success(f"已加载 {len(st.session_state.all_sources)} 个文档")
            except Exception as e:
                st.sidebar.error(f"加载失败: {e}")

    # 上传逻辑
    with st.sidebar.expander("➕ 添加新文档", expanded=False):
        uploaded_file = st.file_uploader("选择文件", type=["pdf", "docx", "txt"], label_visibility="collapsed")
        if uploaded_file and st.button("开始解析", type="primary", use_container_width=True):
            with st.status("处理中...") as status:
                try:
                    parser = DocumentParser()
                    chunks = parser.process_uploaded_file(uploaded_file)
                    llm_svc = LLMService(api_key=api_key)
                    vec_svc = VectorService(embeddings=llm_svc.get_embeddings())
                    vec_svc.add_documents(chunks)
                    st.session_state.vector_service = vec_svc
                    st.session_state.all_sources = vec_svc.get_all_sources()
                    st.session_state.vector_store_ready = True
                    status.update(label="解析完成！", state="complete")
                except Exception as e:
                    status.update(label=f"错误: {e}", state="error")

    # 文档过滤
    selected_docs = []
    if st.session_state.vector_store_ready and st.session_state.all_sources:
        st.sidebar.markdown("---")
        selected_docs = st.sidebar.multiselect("🎯 指定提问范围", options=st.session_state.all_sources) or []
        
    return similarity_threshold, selected_docs, use_parent_context, use_rerank, memory_frequency

# ==========================================
# 3. 核心 RAG 响应函数
# ==========================================
def generate_rag_response(prompt, api_key, threshold, selected_docs, placeholder,
                        use_parent_context=True, use_rerank=True):
    """
    生成RAG响应
    :param prompt: 用户查询
    :param api_key: DashScope API密钥
    :param threshold: 相似度阈值
    :param selected_docs: 选中的文档列表
    :param placeholder: 占位符
    :param use_parent_context: 是否使用父子文档检索
    :param use_rerank: 是否使用重排
    """
    full_response = ""
    sources = []
    try:
        print(f"🐛 DEBUG: 开始处理问题: {prompt[:50]}...")
        llm_svc = LLMService(api_key=api_key)
        llm = llm_svc.get_llm(temperature=0.1)
        print(f"🐛 DEBUG: LLM服务初始化完成")

        if st.session_state.vector_store_ready and st.session_state.vector_service:
            print(f"🐛 DEBUG: 向量库已就绪，开始检索")
            # 意图识别与动态 K 值
            is_summary = any(k in prompt for k in ["总结", "概括", "大纲", "核心", "重点"])
            k = 10 if is_summary else 3
            
            # 性能监控：记录检索开始时间
            retrieval_start = time.time()
            
            # 根据用户选择决定使用哪种检索方式
            if use_parent_context:
                # 使用父子文档检索服务
                docs = st.session_state.vector_service.get_retriever_with_parent_context(
                    query=prompt,
                    k=k,
                    threshold=threshold,
                    selected_sources=selected_docs,
                    initial_k=15  # 初始检索15个文档
                ) or []
            elif use_rerank:
                # 使用重排服务进行两阶段检索
                docs = st.session_state.vector_service.get_retriever_with_rerank(
                    query=prompt,
                    k=k,
                    threshold=threshold,
                    selected_sources=selected_docs,
                    initial_k=15  # 初始检索15个文档
                ) or []
            else:
                # 使用基础检索
                retriever = st.session_state.vector_service.get_retriever(
                    k=k, threshold=threshold, selected_sources=selected_docs
                )
                if retriever is None:
                    docs = []
                else:
                    docs = retriever.invoke(prompt) or []
            
            print(f"🐛 DEBUG: 检索到 {len(docs)} 个文档")
            
            # 性能监控：记录检索结束时间
            retrieval_time = time.time() - retrieval_start
            
            # 分离子文档和父文档，构建上下文（仅在使用父子文档检索时）
            child_docs = []
            parent_docs = []
            
            if use_parent_context:
                child_docs = [doc for doc in docs if doc.metadata.get("context_type") == "child"]
                parent_docs = [doc for doc in docs if doc.metadata.get("context_type") == "parent"]
            
            # 构建上下文
            context_parts = []
            
            if child_docs:
                context_parts.append("【相关片段】：\n" + "\n\n".join(
                    [f"片段{i+1}:\n{d.page_content}" for i, d in enumerate(child_docs)]
                ))
                
                # 添加子文档到引用来源
                for doc in child_docs:
                    sources.append({"source": doc.metadata.get("source", "未知"), "content": doc.page_content})
            
            if parent_docs:
                context_parts.append("\n\n【上下文补充】：\n" + "\n\n".join(
                    [f"上下文{i+1}:\n{d.page_content}" for i, d in enumerate(parent_docs)]
                ))
            
            if not child_docs and not parent_docs:
                # 常规检索结果
                context_parts.append("【相关片段】：\n" + "\n\n".join(
                    [f"片段{i+1}:\n{d.page_content}" for i, d in enumerate(docs)]
                ))
                
                for doc in docs:
                    sources.append({"source": doc.metadata.get("source", "未知"), "content": doc.page_content})
            
            context = "".join(context_parts)
            
            # 根据检索类型调整系统提示词
            if use_parent_context and (child_docs or parent_docs):
                sys_prompt = f"""你是一个专业助手。请基于以下参考内容回答用户问题。

参考内容分为两部分：
1. 【相关片段】：与问题直接相关的文档片段
2. 【上下文补充】：相关片段的父文档，提供更全面的上下文

请优先使用【相关片段】中的信息回答，如果信息不足，可以参考【上下文补充】。
严禁凭空捏造信息。

【参考内容】：\n{context}"""
            else:
                sys_prompt = f"""你是一个专业助手。请基于以下参考内容回答用户问题，严禁捏造。

【参考内容】：\n{context}"""
        else:
            sys_prompt = "你是AI助手。请提醒用户先加载知识库。"

        # 构造流式对话
        history = [{"role": "system", "content": sys_prompt}]
        for msg in st.session_state.messages[-6:]: # 保持最近3轮记忆
            history.append({"role": msg["role"], "content": msg["content"]})
        
        # 性能监控：记录LLM生成开始时间
        llm_start = time.time()
        
        print(f"🐛 DEBUG: 开始LLM流式生成，历史消息数: {len(history)}")
        try:
            for chunk in llm.stream(history):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    full_response += content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            print(f"🐛 DEBUG: LLM生成完成，响应长度: {len(full_response)}")
        except (ConnectionResetError, ConnectionError) as conn_err:
            error_msg = "⚠️ 网络连接中断，请检查网络或稍后重试"
            placeholder.markdown(full_response + f"\n\n{error_msg}")
            st.warning(error_msg)
            print(f"🐛 DEBUG: 连接错误: {conn_err}")
            return full_response or error_msg, sources
        
        # 性能监控：记录LLM生成结束时间
        llm_time = time.time() - llm_start
        total_time = time.time() - retrieval_start
        
        # 性能监控：显示各项时间指标
        if retrieval_time > 0:
            st.info(f"⏱️ 检索耗时: {retrieval_time:.2f} 秒")
        if llm_time > 0:
            st.info(f"🤖 LLM生成耗时: {llm_time:.2f} 秒")
        if total_time > 0:
            st.info(f"⏳ 总耗时: {total_time:.2f} 秒")
        
        # 更新性能统计到session_state
        st.session_state.performance_stats['retrieval_time'] = retrieval_time
        st.session_state.performance_stats['llm_time'] = llm_time
        st.session_state.performance_stats['total_time'] = total_time
        
        if sources:
            with st.expander("📄 查看引用来源"):
                for s in sources: st.caption(f"来源: {s['source']}"); st.text(s['content'])
        return full_response, sources
    except ConnectionResetError as conn_err:
        error_msg = f"⚠️ 网络连接中断: {conn_err}"
        print(f"🐛 DEBUG: {error_msg}")
        st.error("网络连接中断，请检查：\n1. 网络连接是否稳定\n2. API Key 是否正确\n3. 稍后重试")
        return "网络连接异常，请重试", []
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"🐛 DEBUG: 发生错误:\n{error_detail}")
        st.error(f"发生错误: {e}")
        return "服务异常", []

# ==========================================
# 4. 主入口
# ==========================================
def main():
    st.set_page_config(page_title="AI 智能文档 Agent", layout="wide")
    init_session_state()
    
    api_key = get_backend_api_key()
    
    threshold, selected_docs, use_parent_context, use_rerank, memory_frequency = render_sidebar(api_key)
    
    st.title("🔍 智能文档问答 Agent")
    if not st.session_state.vector_store_ready:
        st.info("👈 请从左侧加载本地知识库或上传新文档开始。")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("询问关于文档的问题..."):
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            placeholder = st.empty()
            res, src = generate_rag_response(
                prompt, api_key, threshold, selected_docs, placeholder,
                use_parent_context, use_rerank
            )
            st.session_state.messages.append({"role": "assistant", "content": res, "sources": src})

if __name__ == "__main__":
    main()