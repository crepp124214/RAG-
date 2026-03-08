@echo off
chcp 65001 >nul
echo 正在启动RAG智能文档检索助手...
echo 如果浏览器未自动打开，请手动访问显示的URL
echo 按Ctrl+C停止应用
echo ===================================================
.

streamlit run 页面开发.py

pause