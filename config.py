"""
UniExamAgent-CN 配置模块
支持 MiniMax / Qwen / GLM / Ollama / OpenAI 模型
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 项目路径 ====================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"
OUTPUT_DIR = BASE_DIR / "output"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ==================== 模型配置 ====================
# 可选: "minimax", "qwen", "glm", "ollama", "openai"
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "minimax")

# ==================== MiniMax 海螺AI ====================
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.getenv(
    "MINIMAX_BASE_URL",
    "https://api.minimax.chat/v"
)
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-Text-01")
# MiniMax 支持的模型:
# - MiniMax-Text-01 (默认，高性能)
# - abab6.5s-chat (高速)
# - abab6.5-chat (均衡)

# ==================== 阿里云通义千问 ====================
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")

# ==================== 智谱 GLM（备选）====================
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_BASE_URL = os.getenv(
    "GLM_BASE_URL",
    "https://open.bigmodel.cn/api/paas/v4"
)
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4")

# ==================== OpenAI（备选）====================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ==================== 本地 Ollama ====================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# ==================== RAG 配置 ====================
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ==================== 考试生成配置 ====================
DEFAULT_NUM_PAPERS = 5
COVERAGE_THRESHOLD = 0.98  # 98% 覆盖率要求
MAX_RETRIES = 3

# ==================== 爬虫配置 ====================
CRAWL_TIMEOUT = 30
CRAWL_DELAY = 1.0  # 请求间隔（秒）
MAX_PAGES_PER_SITE = 50

# ==================== 日志配置 ====================
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "app.log"

# ==================== Helper Functions ====================
def get_llm_config() -> dict:
    """获取当前配置的 LLM 参数"""
    if MODEL_PROVIDER == "minimax" and MINIMAX_API_KEY:
        return {
            "provider": "minimax",
            "api_key": MINIMAX_API_KEY,
            "base_url": MINIMAX_BASE_URL,
            "model": MINIMAX_MODEL,
        }
    elif MODEL_PROVIDER == "qwen" and QWEN_API_KEY:
        return {
            "provider": "qwen",
            "api_key": QWEN_API_KEY,
            "base_url": QWEN_BASE_URL,
            "model": QWEN_MODEL,
        }
    elif MODEL_PROVIDER == "glm" and GLM_API_KEY:
        return {
            "provider": "glm",
            "api_key": GLM_API_KEY,
            "base_url": GLM_BASE_URL,
            "model": GLM_MODEL,
        }
    elif MODEL_PROVIDER == "ollama":
        return {
            "provider": "ollama",
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
        }
    elif MODEL_PROVIDER == "openai" and OPENAI_API_KEY:
        return {
            "provider": "openai",
            "api_key": OPENAI_API_KEY,
            "base_url": OPENAI_BASE_URL,
            "model": OPENAI_MODEL,
        }
    else:
        raise ValueError(
            f"未配置有效的模型提供商: {MODEL_PROVIDER}。"
            f"请在 config.py 中配置 API Key 或使用 Ollama。"
        )


def check_config() -> bool:
    """检查配置是否有效"""
    try:
        get_llm_config()
        return True
    except ValueError as e:
        print(f"⚠️ 配置警告: {e}")
        return False
