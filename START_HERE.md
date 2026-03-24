# 🏫 UniExamAgent-CN 运行指南

> 专为 Steven（Steph）配置的个人运行手册

---

## 📋 环境信息

- **系统**: Windows 11
- **Python**: 已安装 (可通过 `python --version` 确认)
- **项目路径**: `C:\Users\Steph\Desktop\UniExamAgent-CN`

---

## 🚀 快速启动（5分钟）

### 步骤 1：配置 API Key

1. 打开文件 `C:\Users\Steph\Desktop\UniExamAgent-CN\config.py`
2. 找到 `MINIMAX_API_KEY`，填入你的 API Key：
   ```python
   MINIMAX_API_KEY = "你的API密钥"  # 例如: "abc123xyz..."
   ```
3. 保存文件

### 步骤 2：安装依赖

打开 **PowerShell** 或 **命令提示符**，运行：

```powershell
cd C:\Users\Steph\Desktop\UniExamAgent-CN

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3：启动应用

```powershell
# 确保在虚拟环境中
.\venv\Scripts\activate

# 启动
streamlit run app.py
```

### 步骤 4：访问

浏览器自动打开，访问：**http://localhost:8501**

---

## 🔧 详细配置

### MiniMax API Key 获取

1. 访问 https://platform.minimax.chat/
2. 注册/登录账号
3. 进入「API Key」页面
4. 创建新 Key，复制粘贴到 `config.py`

### 模型选择

在 `config.py` 中修改：

```python
MODEL_PROVIDER = "minimax"  # 可选: minimax, qwen, glm, ollama
```

### 其他配置

```python
# 考试生成配置
DEFAULT_NUM_PAPERS = 5       # 默认生成试卷数量
COVERAGE_THRESHOLD = 0.98    # 知识点覆盖率要求 (98%)

# RAG 配置
CHUNK_SIZE = 500             # 知识块大小
```

---

## 📁 项目结构说明

```
C:\Users\Steph\Desktop\UniExamAgent-CN\
│
├── app.py              # Streamlit 主界面（启动这个）
├── config.py           # 配置文件（API Key 在这里）
├── prompts.py          # AI 提示词模板
├── agents.py           # LangGraph 智能体
├── rag_pipeline.py     # 知识库向量流程
├── generate_mocks.py   # 试卷生成核心
├── utils.py            # 工具函数
│
├── data/               # 数据目录
│   ├── uploads/        # 上传的文件存放
│   ├── chroma_db/      # 向量数据库
│   └── output/         # 生成的试卷输出
│
├── requirements.txt    # Python 依赖
└── run.bat            # Windows 一键启动脚本
```

---

## 🎯 使用流程

1. **上传资料**: 点击上传 PPT/PDF/TXT 文件
2. **设置规格**: 输入考试规格，如「选择题 40分 8题，简答 40分 4题，大题 20分 2题」
3. **生成试卷**: 点击「生成模拟卷」
4. **下载**: 生成完成后打包下载 5 套试卷

---

## ❓ 常见问题

### Q: 提示 "API Key 无效"
**A**: 检查 `config.py` 中的 `MINIMAX_API_KEY` 是否正确填入

### Q: 依赖安装失败
**A**: 确保 Python 版本 >= 3.11，运行 `python --version` 确认

### Q: 浏览器打不开
**A**: 手动打开浏览器，访问 http://localhost:8501

### Q: 页面空白/样式错乱
**A**: 清除浏览器缓存，或使用无痕模式

---

## 🔄 常用命令

```powershell
# 进入项目目录
cd C:\Users\Steph\Desktop\UniExamAgent-CN

# 激活虚拟环境
.\venv\Scripts\activate

# 启动应用
streamlit run app.py

# 退出虚拟环境
deactivate

# 重新安装依赖
pip install -r requirements.txt
```

---

## 📞 帮助

如遇问题，请检查：
1. API Key 是否配置正确
2. Python 版本是否 >= 3.11
3. 虚拟环境是否激活

---

*最后更新：2025年3月*
