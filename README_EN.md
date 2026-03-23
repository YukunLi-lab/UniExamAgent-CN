# UniExamAgent-CN 🏫📝

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Stars](https://img.shields.io/github/stars/YukunLi-lab/UniExamAgent-CN?style=social)

**Chinese University Exam Expert AI Agent** — Generate 5 full-coverage exam papers from PPT + PDF + web scraping

[English](README_EN.md) | [简体中文](README.md)

</div>

---

## 🎯 Overview

UniExamAgent-CN is an **intelligent exam paper generation system** based on LangGraph + LangChain + ChromaDB. Users can upload course materials (PPT, PDF, TXT) or scrape web resources, and the system automatically extracts knowledge points to generate **5 completely unique exam papers with 100% coverage of knowledge points and question types**.

### Key Features

- ✅ **Multi-format Support**: PPT, PDF, TXT, image batch upload
- 🌐 **Smart Crawling**: MOOC, Zhihu, Baidu Wenku, official website materials
- 🧠 **RAG Enhancement**: ChromaDB vector database for knowledge retrieval
- 📝 **5 Papers Generation**: Generate 5 variant papers at once, coverage ≥98%
- ✅ **Verifier Validation**: Automatically verify coverage, regenerate if failed
- 📊 **Answer Analysis**: Each question with detailed answers + knowledge mapping
- 📥 **One-click Download**: Pack 5 papers for download (.docx/.pdf)

---

## 🚀 Quick Start

```bash
# Clone project
git clone https://github.com/YukunLi-lab/UniExamAgent-CN.git
cd UniExamAgent-CN

# Create virtual environment (Python 3.11+)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start application
streamlit run app.py
```

Or use quick scripts:

```bash
# Windows
run.bat

# Linux/Mac
chmod +x run.sh && ./run.sh
```

---

## 📁 Project Structure

```
UniExamAgent-CN/
├── app.py                 # Streamlit main interface
├── agents.py              # LangGraph multi-agent definitions
├── rag_pipeline.py         # RAG vectorization pipeline
├── generate_mocks.py       # 5 papers generation core logic
├── utils.py                # File processing, crawler, PPT extraction
├── prompts.py              # All system prompts
├── config.py               # API Key configuration
├── requirements.txt        # Dependencies list
├── run.bat / run.sh        # One-click startup scripts
├── docs/                   # Documentation directory
│   └── demo.gif           # Demo animation
└── README.md               # This file
```

---

## 🔧 Configuration

### API Key Configuration

Edit `config.py`:

```python
# Model provider selection
MODEL_PROVIDER = "qwen"  # qwen | glm | ollama | openai

# Alibaba Cloud Qwen
QWEN_API_KEY = "your-qwen-api-key"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# Zhipu GLM (backup)
GLM_API_KEY = "your-glm-api-key"

# Local Ollama (offline priority)
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5:7b"
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

** Made with ❤️ for Chinese Education **

</div>
