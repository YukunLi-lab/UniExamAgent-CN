@echo off
chcp 65001 >nul
title UniExamAgent-CN

echo ====================================
echo   UniExamAgent-CN 大学考试专家
echo ====================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)

REM 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo [步骤 1/4] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo [步骤 2/4] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [步骤 3/4] 安装依赖...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

REM 启动应用
echo [步骤 4/4] 启动应用...
echo.
echo 应用启动后访问: http://localhost:8501
echo 按 Ctrl+C 停止服务
echo.
streamlit run app.py

pause
