#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：将项目从扁平结构迁移到模块化结构
此脚本将自动执行以下操作：
1. 创建 core 目录
2. 移动服务文件到 core 目录
3. 更新导入语句
4. 创建必要的 __init__.py 文件
"""

import os
import shutil
import fileinput
from pathlib import Path


def create_core_directory():
    """创建core目录"""
    core_dir = Path("core")
    core_dir.mkdir(exist_ok=True)
    print(f"✅ 创建目录: {core_dir}")
    
    # 创建 __init__.py 文件
    init_file = core_dir / "__init__.py"
    init_file.touch(exist_ok=True)
    print(f"✅ 创建文件: {init_file}")
    
    return core_dir


def move_service_files(core_dir):
    """移动服务文件到core目录"""
    service_files = [
        "document_parser.py",
        "llm_service.py",
        "vector_service.py",
        "reranker_service.py",
        "conversation_memory.py"
    ]
    
    moved_files = []
    for file in service_files:
        src = Path(file)
        dst = core_dir / file
        
        if src.exists():
            shutil.move(str(src), str(dst))
            print(f"✅ 移动文件: {src} -> {dst}")
            moved_files.append(dst)
        else:
            print(f"⚠️  文件不存在: {src}")
    
    return moved_files


def update_imports_in_app():
    """更新app.py中的导入语句"""
    app_file = Path("app.py")
    
    if not app_file.exists():
        print(f"❌ 文件不存在: {app_file}")
        return False
    
    # 读取原文件内容
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换导入语句
    replacements = [
        ("from llm_service import LLMService", "from core.llm_service import LLMService"),
        ("from document_parser import DocumentParser", "from core.document_parser import DocumentParser"),
        ("from vector_service import VectorService", "from core.vector_service import VectorService"),
        ("from conversation_memory import ConversationMemory", "from core.conversation_memory import ConversationMemory"),
        ("from reranker_service import RerankerService", "from core.reranker_service import RerankerService"),
    ]
    
    for old_import, new_import in replacements:
        content = content.replace(old_import, new_import)
    
    # 写回文件
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 更新导入语句: {app_file}")
    return True


def update_internal_imports():
    """更新core内部文件的相互引用"""
    core_dir = Path("core")
    
    # 更新vector_service.py中的导入
    vector_service_file = core_dir / "vector_service.py"
    if vector_service_file.exists():
        with open(vector_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from reranker_service import RerankerService",
            "from .reranker_service import RerankerService"
        )
        
        with open(vector_service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {vector_service_file}")
    
    # 更新conversation_memory.py中的导入
    conv_memory_file = core_dir / "conversation_memory.py"
    if conv_memory_file.exists():
        with open(conv_memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from llm_service import LLMService",
            "from .llm_service import LLMService"
        )
        
        with open(conv_memory_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {conv_memory_file}")


def main():
    print("🚀 开始迁移项目到模块化结构...")
    
    # 1. 创建core目录
    core_dir = create_core_directory()
    
    # 2. 移动服务文件
    moved_files = move_service_files(core_dir)
    
    if not moved_files:
        print("⚠️  没有找到任何服务文件需要移动")
        return
    
    # 3. 更新app.py中的导入语句
    if update_imports_in_app():
        print("✅ 成功更新app.py中的导入语句")
    
    # 4. 更新内部文件的相互引用
    update_internal_imports()
    
    print("\n🎉 迁移完成！")
    print("\n📁 新的项目结构：")
    print("   RAG智能文档检索助手/\n   ├── core/\n   │   ├── __init__.py\n   │   ├── document_parser.py\n   │   ├── llm_service.py\n   │   ├── vector_service.py\n   │   ├── reranker_service.py\n   │   └── conversation_memory.py\n   ├── app.py\n   ├── run.py\n   ├── start.bat\n   ├── requirements.txt\n   └── ...")
    
    print("\n💡 提示：现在可以运行 'streamlit run app.py' 来启动应用")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：将项目从扁平结构迁移到模块化结构
此脚本将自动执行以下操作：
1. 创建 core 目录
2. 移动服务文件到 core 目录
3. 更新导入语句
4. 创建必要的 __init__.py 文件
"""

import os
import shutil
import fileinput
from pathlib import Path


def create_core_directory():
    """创建core目录"""
    core_dir = Path("core")
    core_dir.mkdir(exist_ok=True)
    print(f"✅ 创建目录: {core_dir}")
    
    # 创建 __init__.py 文件
    init_file = core_dir / "__init__.py"
    init_file.touch(exist_ok=True)
    print(f"✅ 创建文件: {init_file}")
    
    return core_dir


def move_service_files(core_dir):
    """移动服务文件到core目录"""
    service_files = [
        "document_parser.py",
        "llm_service.py",
        "vector_service.py",
        "reranker_service.py",
        "conversation_memory.py"
    ]
    
    moved_files = []
    for file in service_files:
        src = Path(file)
        dst = core_dir / file
        
        if src.exists():
            shutil.move(str(src), str(dst))
            print(f"✅ 移动文件: {src} -> {dst}")
            moved_files.append(dst)
        else:
            print(f"⚠️  文件不存在: {src}")
    
    return moved_files


def update_imports_in_app():
    """更新app.py中的导入语句"""
    app_file = Path("app.py")
    
    if not app_file.exists():
        print(f"❌ 文件不存在: {app_file}")
        return False
    
    # 读取原文件内容
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换导入语句
    replacements = [
        ("from llm_service import LLMService", "from core.llm_service import LLMService"),
        ("from document_parser import DocumentParser", "from core.document_parser import DocumentParser"),
        ("from vector_service import VectorService", "from core.vector_service import VectorService"),
        ("from conversation_memory import ConversationMemory", "from core.conversation_memory import ConversationMemory"),
        ("from reranker_service import RerankerService", "from core.reranker_service import RerankerService"),
    ]
    
    for old_import, new_import in replacements:
        content = content.replace(old_import, new_import)
    
    # 写回文件
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 更新导入语句: {app_file}")
    return True


def update_internal_imports():
    """更新core内部文件的相互引用"""
    core_dir = Path("core")
    
    # 更新vector_service.py中的导入
    vector_service_file = core_dir / "vector_service.py"
    if vector_service_file.exists():
        with open(vector_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from reranker_service import RerankerService",
            "from .reranker_service import RerankerService"
        )
        
        with open(vector_service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {vector_service_file}")
    
    # 更新conversation_memory.py中的导入
    conv_memory_file = core_dir / "conversation_memory.py"
    if conv_memory_file.exists():
        with open(conv_memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from llm_service import LLMService",
            "from .llm_service import LLMService"
        )
        
        with open(conv_memory_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {conv_memory_file}")


def main():
    print("🚀 开始迁移项目到模块化结构...")
    
    # 1. 创建core目录
    core_dir = create_core_directory()
    
    # 2. 移动服务文件
    moved_files = move_service_files(core_dir)
    
    if not moved_files:
        print("⚠️  没有找到任何服务文件需要移动")
        return
    
    # 3. 更新app.py中的导入语句
    if update_imports_in_app():
        print("✅ 成功更新app.py中的导入语句")
    
    # 4. 更新内部文件的相互引用
    update_internal_imports()
    
    print("\n🎉 迁移完成！")
    print("\n📁 新的项目结构：")
    print("   RAG智能文档检索助手/\n   ├── core/\n   │   ├── __init__.py\n   │   ├── document_parser.py\n   │   ├── llm_service.py\n   │   ├── vector_service.py\n   │   ├── reranker_service.py\n   │   └── conversation_memory.py\n   ├── app.py\n   ├── run.py\n   ├── start.bat\n   ├── requirements.txt\n   └── ...")
    
    print("\n💡 提示：现在可以运行 'streamlit run app.py' 来启动应用")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：将项目从扁平结构迁移到模块化结构
此脚本将自动执行以下操作：
1. 创建 core 目录
2. 移动服务文件到 core 目录
3. 更新导入语句
4. 创建必要的 __init__.py 文件
"""

import os
import shutil
import fileinput
from pathlib import Path


def create_core_directory():
    """创建core目录"""
    core_dir = Path("core")
    core_dir.mkdir(exist_ok=True)
    print(f"✅ 创建目录: {core_dir}")
    
    # 创建 __init__.py 文件
    init_file = core_dir / "__init__.py"
    init_file.touch(exist_ok=True)
    print(f"✅ 创建文件: {init_file}")
    
    return core_dir


def move_service_files(core_dir):
    """移动服务文件到core目录"""
    service_files = [
        "document_parser.py",
        "llm_service.py",
        "vector_service.py",
        "reranker_service.py",
        "conversation_memory.py"
    ]
    
    moved_files = []
    for file in service_files:
        src = Path(file)
        dst = core_dir / file
        
        if src.exists():
            shutil.move(str(src), str(dst))
            print(f"✅ 移动文件: {src} -> {dst}")
            moved_files.append(dst)
        else:
            print(f"⚠️  文件不存在: {src}")
    
    return moved_files


def update_imports_in_app():
    """更新app.py中的导入语句"""
    app_file = Path("app.py")
    
    if not app_file.exists():
        print(f"❌ 文件不存在: {app_file}")
        return False
    
    # 读取原文件内容
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换导入语句
    replacements = [
        ("from llm_service import LLMService", "from core.llm_service import LLMService"),
        ("from document_parser import DocumentParser", "from core.document_parser import DocumentParser"),
        ("from vector_service import VectorService", "from core.vector_service import VectorService"),
        ("from conversation_memory import ConversationMemory", "from core.conversation_memory import ConversationMemory"),
        ("from reranker_service import RerankerService", "from core.reranker_service import RerankerService"),
    ]
    
    for old_import, new_import in replacements:
        content = content.replace(old_import, new_import)
    
    # 写回文件
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 更新导入语句: {app_file}")
    return True


def update_internal_imports():
    """更新core内部文件的相互引用"""
    core_dir = Path("core")
    
    # 更新vector_service.py中的导入
    vector_service_file = core_dir / "vector_service.py"
    if vector_service_file.exists():
        with open(vector_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from reranker_service import RerankerService",
            "from .reranker_service import RerankerService"
        )
        
        with open(vector_service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {vector_service_file}")
    
    # 更新conversation_memory.py中的导入
    conv_memory_file = core_dir / "conversation_memory.py"
    if conv_memory_file.exists():
        with open(conv_memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from llm_service import LLMService",
            "from .llm_service import LLMService"
        )
        
        with open(conv_memory_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {conv_memory_file}")


def main():
    print("🚀 开始迁移项目到模块化结构...")
    
    # 1. 创建core目录
    core_dir = create_core_directory()
    
    # 2. 移动服务文件
    moved_files = move_service_files(core_dir)
    
    if not moved_files:
        print("⚠️  没有找到任何服务文件需要移动")
        return
    
    # 3. 更新app.py中的导入语句
    if update_imports_in_app():
        print("✅ 成功更新app.py中的导入语句")
    
    # 4. 更新内部文件的相互引用
    update_internal_imports()
    
    print("\n🎉 迁移完成！")
    print("\n📁 新的项目结构：")
    print("   RAG智能文档检索助手/\n   ├── core/\n   │   ├── __init__.py\n   │   ├── document_parser.py\n   │   ├── llm_service.py\n   │   ├── vector_service.py\n   │   ├── reranker_service.py\n   │   └── conversation_memory.py\n   ├── app.py\n   ├── run.py\n   ├── start.bat\n   ├── requirements.txt\n   └── ...")
    
    print("\n💡 提示：现在可以运行 'streamlit run app.py' 来启动应用")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：将项目从扁平结构迁移到模块化结构
此脚本将自动执行以下操作：
1. 创建 core 目录
2. 移动服务文件到 core 目录
3. 更新导入语句
4. 创建必要的 __init__.py 文件
"""

import os
import shutil
import fileinput
from pathlib import Path


def create_core_directory():
    """创建core目录"""
    core_dir = Path("core")
    core_dir.mkdir(exist_ok=True)
    print(f"✅ 创建目录: {core_dir}")
    
    # 创建 __init__.py 文件
    init_file = core_dir / "__init__.py"
    init_file.touch(exist_ok=True)
    print(f"✅ 创建文件: {init_file}")
    
    return core_dir


def move_service_files(core_dir):
    """移动服务文件到core目录"""
    service_files = [
        "document_parser.py",
        "llm_service.py",
        "vector_service.py",
        "reranker_service.py",
        "conversation_memory.py"
    ]
    
    moved_files = []
    for file in service_files:
        src = Path(file)
        dst = core_dir / file
        
        if src.exists():
            shutil.move(str(src), str(dst))
            print(f"✅ 移动文件: {src} -> {dst}")
            moved_files.append(dst)
        else:
            print(f"⚠️  文件不存在: {src}")
    
    return moved_files


def update_imports_in_app():
    """更新app.py中的导入语句"""
    app_file = Path("app.py")
    
    if not app_file.exists():
        print(f"❌ 文件不存在: {app_file}")
        return False
    
    # 读取原文件内容
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换导入语句
    replacements = [
        ("from llm_service import LLMService", "from core.llm_service import LLMService"),
        ("from document_parser import DocumentParser", "from core.document_parser import DocumentParser"),
        ("from vector_service import VectorService", "from core.vector_service import VectorService"),
        ("from conversation_memory import ConversationMemory", "from core.conversation_memory import ConversationMemory"),
        ("from reranker_service import RerankerService", "from core.reranker_service import RerankerService"),
    ]
    
    for old_import, new_import in replacements:
        content = content.replace(old_import, new_import)
    
    # 写回文件
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 更新导入语句: {app_file}")
    return True


def update_internal_imports():
    """更新core内部文件的相互引用"""
    core_dir = Path("core")
    
    # 更新vector_service.py中的导入
    vector_service_file = core_dir / "vector_service.py"
    if vector_service_file.exists():
        with open(vector_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from reranker_service import RerankerService",
            "from .reranker_service import RerankerService"
        )
        
        with open(vector_service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {vector_service_file}")
    
    # 更新conversation_memory.py中的导入
    conv_memory_file = core_dir / "conversation_memory.py"
    if conv_memory_file.exists():
        with open(conv_memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from llm_service import LLMService",
            "from .llm_service import LLMService"
        )
        
        with open(conv_memory_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {conv_memory_file}")


def main():
    print("🚀 开始迁移项目到模块化结构...")
    
    # 1. 创建core目录
    core_dir = create_core_directory()
    
    # 2. 移动服务文件
    moved_files = move_service_files(core_dir)
    
    if not moved_files:
        print("⚠️  没有找到任何服务文件需要移动")
        return
    
    # 3. 更新app.py中的导入语句
    if update_imports_in_app():
        print("✅ 成功更新app.py中的导入语句")
    
    # 4. 更新内部文件的相互引用
    update_internal_imports()
    
    print("\n🎉 迁移完成！")
    print("\n📁 新的项目结构：")
    print("   RAG智能文档检索助手/\n   ├── core/\n   │   ├── __init__.py\n   │   ├── document_parser.py\n   │   ├── llm_service.py\n   │   ├── vector_service.py\n   │   ├── reranker_service.py\n   │   └── conversation_memory.py\n   ├── app.py\n   ├── run.py\n   ├── start.bat\n   ├── requirements.txt\n   └── ...")
    
    print("\n💡 提示：现在可以运行 'streamlit run app.py' 来启动应用")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：将项目从扁平结构迁移到模块化结构
此脚本将自动执行以下操作：
1. 创建 core 目录
2. 移动服务文件到 core 目录
3. 更新导入语句
4. 创建必要的 __init__.py 文件
"""

import os
import shutil
import fileinput
from pathlib import Path


def create_core_directory():
    """创建core目录"""
    core_dir = Path("core")
    core_dir.mkdir(exist_ok=True)
    print(f"✅ 创建目录: {core_dir}")
    
    # 创建 __init__.py 文件
    init_file = core_dir / "__init__.py"
    init_file.touch(exist_ok=True)
    print(f"✅ 创建文件: {init_file}")
    
    return core_dir


def move_service_files(core_dir):
    """移动服务文件到core目录"""
    service_files = [
        "document_parser.py",
        "llm_service.py",
        "vector_service.py",
        "reranker_service.py",
        "conversation_memory.py"
    ]
    
    moved_files = []
    for file in service_files:
        src = Path(file)
        dst = core_dir / file
        
        if src.exists():
            shutil.move(str(src), str(dst))
            print(f"✅ 移动文件: {src} -> {dst}")
            moved_files.append(dst)
        else:
            print(f"⚠️  文件不存在: {src}")
    
    return moved_files


def update_imports_in_app():
    """更新app.py中的导入语句"""
    app_file = Path("app.py")
    
    if not app_file.exists():
        print(f"❌ 文件不存在: {app_file}")
        return False
    
    # 读取原文件内容
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换导入语句
    replacements = [
        ("from llm_service import LLMService", "from core.llm_service import LLMService"),
        ("from document_parser import DocumentParser", "from core.document_parser import DocumentParser"),
        ("from vector_service import VectorService", "from core.vector_service import VectorService"),
        ("from conversation_memory import ConversationMemory", "from core.conversation_memory import ConversationMemory"),
        ("from reranker_service import RerankerService", "from core.reranker_service import RerankerService"),
    ]
    
    for old_import, new_import in replacements:
        content = content.replace(old_import, new_import)
    
    # 写回文件
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 更新导入语句: {app_file}")
    return True


def update_internal_imports():
    """更新core内部文件的相互引用"""
    core_dir = Path("core")
    
    # 更新vector_service.py中的导入
    vector_service_file = core_dir / "vector_service.py"
    if vector_service_file.exists():
        with open(vector_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from reranker_service import RerankerService",
            "from .reranker_service import RerankerService"
        )
        
        with open(vector_service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {vector_service_file}")
    
    # 更新conversation_memory.py中的导入
    conv_memory_file = core_dir / "conversation_memory.py"
    if conv_memory_file.exists():
        with open(conv_memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将绝对导入改为相对导入
        content = content.replace(
            "from llm_service import LLMService",
            "from .llm_service import LLMService"
        )
        
        with open(conv_memory_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新内部导入: {conv_memory_file}")


def main():
    print("🚀 开始迁移项目到模块化结构...")
    
    # 1. 创建core目录
    core_dir = create_core_directory()
    
    # 2. 移动服务文件
    moved_files = move_service_files(core_dir)
    
    if not moved_files:
        print("⚠️  没有找到任何服务文件需要移动")
        return
    
    # 3. 更新app.py中的导入语句
    if update_imports_in_app():
        print("✅ 成功更新app.py中的导入语句")
    
    # 4. 更新内部文件的相互引用
    update_internal_imports()
    
    print("\n🎉 迁移完成！")
    print("\n📁 新的项目结构：")
    print("   RAG智能文档检索助手/\n   ├── core/\n   │   ├── __init__.py\n   │   ├── document_parser.py\n   │   ├── llm_service.py\n   │   ├── vector_service.py\n   │   ├── reranker_service.py\n   │   └── conversation_memory.py\n   ├── app.py\n   ├── run.py\n   ├── start.bat\n   ├── requirements.txt\n   └── ...")
    
    print("\n💡 提示：现在可以运行 'streamlit run app.py' 来启动应用")


if __name__ == "__main__":
    main()