#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG智能文档检索助手启动脚本
"""

import os
import sys
import subprocess

def main():
    """
    主函数，启动Streamlit应用
    """
    print("正在启动RAG智能文档检索助手...")
    print("如果浏览器未自动打开，请手动访问显示的URL")
    print("按Ctrl+C停止应用")
    print("-" * 50)
    
    try:
        # 启动Streamlit应用
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动应用时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()