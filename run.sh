#!/bin/bash

# ===================================
#   UniExamAgent-CN 大学考试专家
# ===================================

echo "===================================="
echo "  UniExamAgent-CN 大学考试专家"
echo "===================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未安装 Python，请先安装 Python 3.11+"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "[步骤 1/4] 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "[步骤 2/4] 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "[步骤 3/4] 安装依赖..."
pip install -r requirements.txt

# 启动应用
echo "[步骤 4/4] 启动应用..."
echo ""
echo "应用启动后访问: http://localhost:8501"
echo "按 Ctrl+C 停止服务"
echo ""
streamlit run app.py
