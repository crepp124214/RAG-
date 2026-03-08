import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentParser:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化文档解析与分割器
        :param chunk_size: 每个文本块的最大字符数。500是一个适中的值，能保证语义相对完整。
        :param chunk_overlap: 相邻文本块之间的重叠字符数。重叠能防止把一句话从中间截断，导致上下文丢失。
        """
        # 使用递归字符分割器，它会优先按段落切分，然后再按句子切分，非常适合中文和英文 RAG
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # 定义切分优先级：优先按双换行切分，其次是单换行，然后是句号等标点
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )
        # 父文档分割器，使用更大的块大小
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 4,  # 父文档块大小是子文档的4倍
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )

    def process_uploaded_file(self, uploaded_file) -> list:
        """
        处理 Streamlit 上传的文件，将其解析并分割为 Document 对象列表
        :param uploaded_file: Streamlit 的 UploadedFile 对象
        :return: LangChain 的 Document 对象列表（即切分好的 chunks）
        """
        # 获取文件后缀
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # 1. 创建临时文件保存上传的内容
        # 由于 Streamlit 的文件在内存中，LangChain loader 需要本地路径，因此写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        try:
            # 2. 根据文件类型选择对应的 LangChain 加载器
            if file_extension == '.pdf':
                loader = PyPDFLoader(temp_file_path)
            elif file_extension == '.docx':
                loader = Docx2txtLoader(temp_file_path)
            elif file_extension == '.txt':
                # 尝试用 utf-8 读取 txt
                loader = TextLoader(temp_file_path, encoding='utf-8')
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")

            # 3. 加载完整文档
            documents = loader.load()

            # 4. 更新元数据 (Metadata)
            # 这一步极其重要，我们要确保切分后的每一个 chunk 都记录了它来自哪个源文件
            for doc in documents:
                doc.metadata["source"] = uploaded_file.name

            # 5. 分割文档为一个个的 chunk
            chunks = self.text_splitter.split_documents(documents)
            return chunks

        finally:
            # 6. 无论成功与否，最后都要清理掉临时文件，避免占用磁盘空间
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def process_uploaded_file_with_parent(self, uploaded_file) -> list:
        """
        处理上传文件，创建父子文档关系
        :param uploaded_file: Streamlit 的 UploadedFile 对象
        :return: 包含父子关系的 Document 对象列表
        """
        # 获取文件后缀
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # 1. 创建临时文件保存上传的内容
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        try:
            # 2. 根据文件类型选择对应的 LangChain 加载器
            if file_extension == '.pdf':
                loader = PyPDFLoader(temp_file_path)
            elif file_extension == '.docx':
                loader = Docx2txtLoader(temp_file_path)
            elif file_extension == '.txt':
                loader = TextLoader(temp_file_path, encoding='utf-8')
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")

            # 3. 加载完整文档
            documents = loader.load()

            # 4. 更新元数据
            for doc in documents:
                doc.metadata["source"] = uploaded_file.name

            # 5. 创建父文档
            parent_docs = self.parent_splitter.split_documents(documents)
            
            # 6. 创建子文档
            child_docs = self.text_splitter.split_documents(documents)
            
            # 7. 建立父子关系
            # 为每个子文档找到最相似的父文档
            for i, child_doc in enumerate(child_docs):
                # 简单策略：根据位置匹配父文档
                # 实际项目中可以使用更复杂的相似度匹配
                parent_idx = min(i // 4, len(parent_docs) - 1)  # 每个父文档对应4个子文档
                child_doc.metadata["parent_id"] = parent_idx
                child_doc.metadata["is_child"] = True
                child_doc.metadata["child_id"] = i
                
            # 为父文档添加标记
            for i, parent_doc in enumerate(parent_docs):
                parent_doc.metadata["parent_id"] = i
                parent_doc.metadata["is_child"] = False
                parent_doc.metadata["child_ids"] = list(range(i*4, min((i+1)*4, len(child_docs))))
            
            # 8. 合并父子文档，子文档在前，父文档在后
            all_docs = child_docs + parent_docs
            return all_docs

        finally:
            # 9. 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            # 6. 无论成功与否，最后都要清理掉临时文件，避免占用磁盘空间
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

# 测试代码 (这部分在集成到主项目时可以注释掉)
#if __name__ == "__main__":
    #print("文档解析工具准备就绪！")
    # 你可以在这里模拟传入一个对象进行测试
import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentParser:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化文档解析与分割器
        :param chunk_size: 每个文本块的最大字符数。500是一个适中的值，能保证语义相对完整。
        :param chunk_overlap: 相邻文本块之间的重叠字符数。重叠能防止把一句话从中间截断，导致上下文丢失。
        """
        # 使用递归字符分割器，它会优先按段落切分，然后再按句子切分，非常适合中文和英文 RAG
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # 定义切分优先级：优先按双换行切分，其次是单换行，然后是句号等标点
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )
        # 父文档分割器，使用更大的块大小
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 4,  # 父文档块大小是子文档的4倍
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )

    def process_uploaded_file(self, uploaded_file) -> list:
        """
        处理 Streamlit 上传的文件，将其解析并分割为 Document 对象列表
        :param uploaded_file: Streamlit 的 UploadedFile 对象
        :return: LangChain 的 Document 对象列表（即切分好的 chunks）
        """
        # 获取文件后缀
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # 1. 创建临时文件保存上传的内容
        # 由于 Streamlit 的文件在内存中，LangChain loader 需要本地路径，因此写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        try:
            # 2. 根据文件类型选择对应的 LangChain 加载器
            if file_extension == '.pdf':
                loader = PyPDFLoader(temp_file_path)
            elif file_extension == '.docx':
                loader = Docx2txtLoader(temp_file_path)
            elif file_extension == '.txt':
                # 尝试用 utf-8 读取 txt
                loader = TextLoader(temp_file_path, encoding='utf-8')
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")

            # 3. 加载完整文档
            documents = loader.load()

            # 4. 更新元数据 (Metadata)
            # 这一步极其重要，我们要确保切分后的每一个 chunk 都记录了它来自哪个源文件
            for doc in documents:
                doc.metadata["source"] = uploaded_file.name

            # 5. 分割文档为一个个的 chunk
            chunks = self.text_splitter.split_documents(documents)
            return chunks

        finally:
            # 6. 无论成功与否，最后都要清理掉临时文件，避免占用磁盘空间
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def process_uploaded_file_with_parent(self, uploaded_file) -> list:
        """
        处理上传文件，创建父子文档关系
        :param uploaded_file: Streamlit 的 UploadedFile 对象
        :return: 包含父子关系的 Document 对象列表
        """
        # 获取文件后缀
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # 1. 创建临时文件保存上传的内容
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        try:
            # 2. 根据文件类型选择对应的 LangChain 加载器
            if file_extension == '.pdf':
                loader = PyPDFLoader(temp_file_path)
            elif file_extension == '.docx':
                loader = Docx2txtLoader(temp_file_path)
            elif file_extension == '.txt':
                loader = TextLoader(temp_file_path, encoding='utf-8')
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")

            # 3. 加载完整文档
            documents = loader.load()

            # 4. 更新元数据
            for doc in documents:
                doc.metadata["source"] = uploaded_file.name

            # 5. 创建父文档
            parent_docs = self.parent_splitter.split_documents(documents)
            
            # 6. 创建子文档
            child_docs = self.text_splitter.split_documents(documents)
            
            # 7. 建立父子关系
            # 为每个子文档找到最相似的父文档
            for i, child_doc in enumerate(child_docs):
                # 简单策略：根据位置匹配父文档
                # 实际项目中可以使用更复杂的相似度匹配
                parent_idx = min(i // 4, len(parent_docs) - 1)  # 每个父文档对应4个子文档
                child_doc.metadata["parent_id"] = parent_idx
                child_doc.metadata["is_child"] = True
                child_doc.metadata["child_id"] = i
                
            # 为父文档添加标记
            for i, parent_doc in enumerate(parent_docs):
                parent_doc.metadata["parent_id"] = i
                parent_doc.metadata["is_child"] = False
                parent_doc.metadata["child_ids"] = list(range(i*4, min((i+1)*4, len(child_docs))))
            
            # 8. 合并父子文档，子文档在前，父文档在后
            all_docs = child_docs + parent_docs
            return all_docs

        finally:
            # 9. 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            # 6. 无论成功与否，最后都要清理掉临时文件，避免占用磁盘空间
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

# 测试代码 (这部分在集成到主项目时可以注释掉)
#if __name__ == "__main__":
    #print("文档解析工具准备就绪！")
    # 你可以在这里模拟传入一个对象进行测试