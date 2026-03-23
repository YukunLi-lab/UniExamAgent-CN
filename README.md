# UniExamAgent-CN 🏫📝

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Stars](https://img.shields.io/github/stars/YukunLi-lab/UniExamAgent-CN?style=social)

**中国大学考试专家 AI Agent** — 支持 PPT + PDF + 爬取资料生成 5 套全覆盖模拟卷

[English](README_EN.md) | 简体中文

</div>

---

## 🎯 项目简介

UniExamAgent-CN 是一款基于 LangGraph + LangChain + ChromaDB 的**智能考试卷生成系统**。用户可上传课程资料（PPT、PDF、TXT）或爬取网络资源，系统自动提取知识点，生成**5 套完全不重复、100% 覆盖知识点和题型套路**的模拟试卷。

### 核心特性

- ✅ **多格式支持**：PPT、PDF、TXT、图片批量上传
- 🌐 **智能爬取**：MOOC、知乎、百度文库、官网资料
- 🧠 **RAG 增强**：ChromaDB 向量数据库实现知识点检索
- 📝 **5 套生成**：一次生成 5 套变体题，覆盖率 ≥98%
- ✅ **Verifier 验证**：自动校验覆盖率，不达标则重新生成
- 📊 **答案解析**：每题附带详细答案 + 知识点映射
- 📥 **一键下载**：5 套卷子打包下载（.docx/.pdf）

---

## 🖥️ Demo 演示

![Demo GIF](docs/demo.gif)

> **提示**：Demo 展示完整流程：上传资料 → 知识点提取 → 生成 5 套卷子 → 下载

---

## 🚀 一键安装

```bash
# 克隆项目
git clone https://github.com/YukunLi-lab/UniExamAgent-CN.git
cd UniExamAgent-CN

# 创建虚拟环境 (Python 3.11+)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

或使用快捷脚本：

```bash
# Windows
run.bat

# Linux/Mac
chmod +x run.sh && ./run.sh
```

---

## 📁 项目结构

```
UniExamAgent-CN/
├── app.py                 # Streamlit 主界面
├── agents.py              # LangGraph 多智能体定义
├── rag_pipeline.py         # RAG 向量化流程
├── generate_mocks.py       # 5 套生成核心逻辑
├── utils.py                # 文件处理、爬虫、PPT 提取
├── prompts.py              # 所有系统提示词
├── config.py               # API Key 配置
├── requirements.txt        # 依赖清单
├── run.bat / run.sh        # 一键启动脚本
├── docs/                   # 文档目录
│   └── demo.gif           # 演示动画
└── README.md               # 本文件
```

---

## 🔧 配置说明

### 1. API Key 配置

编辑 `config.py`：

```python
# 支持的模型选择
MODEL_PROVIDER = "minimax"  # minimax | qwen | glm | ollama | openai

# MiniMax 海螺AI
MINIMAX_API_KEY = "your-minimax-api-key"
MINIMAX_BASE_URL = "https://api.minimax.chat/v"
MINIMAX_MODEL = "MiniMax-Text-01"

# 阿里云通义千问
QWEN_API_KEY = "your-qwen-api-key"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 智谱 GLM（备选）
GLM_API_KEY = "your-glm-api-key"

# 本地 Ollama（离线优先）
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5:7b"
```

### 2. 向量数据库

ChromaDB 数据存储在 `data/chroma_db/` 目录，首次运行自动初始化。

---

## 🎓 使用流程

### 方式一：界面上传

1. 启动应用：`streamlit run app.py`
2. 上传课程资料（支持 .pptx/.pdf/.txt/.jpg）
3. 输入考试规格（例："选择题 40分 8题，简答 40分 4题，大题 20分 2题"）
4. 点击「生成模拟卷」
5. 等待 5 套卷子生成完成，点击下载

### 方式二：命令行爬取生成

```python
from agents import ExamGeneratorAgent
from rag_pipeline import KnowledgeBaseBuilder

# 初始化
kb = KnowledgeBaseBuilder()
agent = ExamGeneratorAgent()

# 爬取课程资料
kb.crawl_course("清华大学 高等数学")

# 构建知识库
kb.build()

# 生成 5 套卷子
result = agent.generate_exam_papers(
    exam_spec="选择题 40分 8题，简答 40分 4题，大题 20分 2题",
    num_papers=5,
    coverage_threshold=0.98
)

# 下载
result.download_all("output/")
```

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      Streamlit UI                        │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  ExamGeneratorAgent                      │
│  (LangGraph StateGraph)                                │
├─────────────┬─────────────┬─────────────┬───────────────┤
│  Extractor  │   Crawler   │  Analyzer   │  Generator    │
│   Agent     │   Agent     │   Agent     │    Agent      │
└──────┬──────┴──────┬──────┴──────┬──────┴───────┬───────┘
       │             │             │              │
       ▼             ▼             ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                   ChromaDB Vector Store                  │
│            (知识点 + 题型 + 套路 向量索引)              │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 知识点覆盖验证流程

```
知识点清单 ──→ 题型映射 ──→ 5 套变体生成
                                   │
                                   ▼
                            ┌────────────┐
                            │  Verifier  │
                            │   Agent    │
                            └─────┬──────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │  覆盖率 ≥ 98%？           │
                    └─────────────┬─────────────┘
                         是 ✅    │   否 ❌
                                  ▼
                         返回「覆盖报告」  →  重新生成
```

---

## 🌟 星标目标

<div align="center">

| 目标 | 描述 |
|:---:|:---|
| ⭐ 100 | 基础功能完成 |
| ⭐ 500 | 5 套生成通过率 >95% |
| ⭐ 1K | 支持更多模型 + API 集成 |

**如果这个项目对你有帮助，请点一颗 ⭐！**

</div>

---

## 🤝 贡献指南

欢迎提交 Issue 和 PR！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add AmazingFeature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) — LLM 应用框架
- [LangGraph](https://github.com/langchain-ai/langgraph) — 多智能体框架
- [ChromaDB](https://github.com/chroma-core/chroma) — 向量数据库
- [Qwen](https://github.com/QwenLM) — 阿里通义千问
- [ZhipuAI](https://github.com/THUDM) — 智谱 GLM

---

<div align="center">

** Made with ❤️ for Chinese Education **

</div>
