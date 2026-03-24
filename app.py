"""
UniExamAgent-CN Streamlit 主界面
中国大学考试专家 AI Agent
"""

import time
import os
import tempfile
from pathlib import Path
from typing import List

import streamlit as st
from loguru import logger

from config import (
    BASE_DIR, UPLOAD_DIR, OUTPUT_DIR,
    MODEL_PROVIDER, check_config
)
from utils import FileProcessor, ExamSpecParser
from rag_pipeline import KnowledgeBaseBuilder, RAGPipeline
from generate_mocks import MockPaperGenerator, CoverageAnalyzer
from agents import ExamGeneratorAgent


# ==================== 页面配置 ====================
st.set_page_config(
    page_title="UniExamAgent-CN | 大学考试专家",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 隐藏 Streamlit 默认样式
st.markdown("""
<style>
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==================== 初始化 ====================
@st.cache_resource
def init_knowledge_base():
    """初始化知识库"""
    return KnowledgeBaseBuilder()


def init_session_state():
    """初始化会话状态"""
    if "kb" not in st.session_state:
        st.session_state.kb = init_knowledge_base()

    if "papers_generated" not in st.session_state:
        st.session_state.papers_generated = False

    if "generated_papers" not in st.session_state:
        st.session_state.generated_papers = []

    if "coverage_rate" not in st.session_state:
        st.session_state.coverage_rate = 0

    # 高级选项默认值
    if "num_papers" not in st.session_state:
        st.session_state.num_papers = 5
    if "coverage_threshold" not in st.session_state:
        st.session_state.coverage_threshold = 0.98
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.8


init_session_state()


# ==================== 侧边栏 ====================
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title("⚙️ 配置")

        # 模型选择
        st.subheader("模型配置")
        provider = st.selectbox(
            "选择模型提供商",
            ["minimax", "qwen", "glm", "ollama"],
            index=["minimax", "qwen", "glm", "ollama"].index(MODEL_PROVIDER) if MODEL_PROVIDER in ["minimax", "qwen", "glm", "ollama"] else 0
        )

        if provider == "ollama":
            st.info("请确保 Ollama 已启动: `ollama serve`")

        # 知识库信息
        st.subheader("📚 知识库状态")
        kb_info = st.session_state.kb.get_collection_info()
        st.metric("知识块数量", kb_info.get("total_chunks", 0))

        if kb_info.get("sources"):
            for source, count in kb_info["sources"].items():
                st.write(f"- {source}: {count}")

        # 清空知识库按钮
        if st.button("🗑️ 清空知识库", key="btn_clear_kb", use_container_width=True):
            st.session_state.kb.clear()
            st.session_state.papers_generated = False
            # 同时清空上传目录
            for f in UPLOAD_DIR.glob("*"):
                f.unlink()
            st.success("知识库已清空！")
            st.rerun()

        # 高级选项
        with st.expander("🔧 高级选项"):
            num_papers = st.slider(
                "生成试卷数量", 3, 10,
                key="num_papers_slider"
            )
            coverage_threshold = st.slider(
                "覆盖率阈值", 0.90, 1.0, 0.98, step=0.01,
                key="coverage_threshold_slider"
            )
            temperature = st.slider(
                "生成温度", 0.5, 1.0, 0.8, step=0.05,
                key="temperature_slider"
            )
            st.session_state.num_papers = num_papers
            st.session_state.coverage_threshold = coverage_threshold
            st.session_state.temperature = temperature

        return st.session_state.num_papers, st.session_state.coverage_threshold


# ==================== 主页面 ====================
def render_header():
    """渲染页面头部"""
    st.title("🏫 UniExamAgent-CN")
    st.markdown("### 中国大学考试专家 AI Agent")
    st.markdown("---")


def render_upload_section():
    """渲染文件上传区域"""
    st.header("📁 上传课程资料")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📤 上传文件")
        uploaded_files = st.file_uploader(
            "支持 PPT、PDF、TXT、图片",
            type=["pptx", "pdf", "txt", "jpg", "png", "jpeg"],
            accept_multiple_files=True,
            help="上传课程相关资料，系统将自动提取知识点"
        )

        if uploaded_files:
            st.success(f"已上传 {len(uploaded_files)} 个文件")

            # 保存文件
            for uploaded_file in uploaded_files:
                file_path = UPLOAD_DIR / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            st.info(f"文件保存至: {UPLOAD_DIR}")

    with col2:
        st.subheader("🌐 爬取网络资源")
        university = st.text_input("学校名称", placeholder="如：清华大学")
        course_name = st.text_input("课程名称", placeholder="如：高等数学")

        if st.button("🔍 开始爬取", key="btn_crawl", use_container_width=True):
            if not course_name:
                st.error("请输入课程名称")
            else:
                with st.spinner("正在爬取..."):
                    try:
                        st.session_state.kb.crawl_and_add(
                            university=university,
                            course_name=course_name,
                            keywords=[course_name],
                            max_results=50
                        )
                        st.success("爬取完成！")
                    except Exception as e:
                        st.error(f"爬取失败: {e}")


def render_knowledge_section():
    """渲染知识库预览"""
    st.header("📚 知识库预览")

    if st.button("🔄 更新知识库", key="btn_update_kb", use_container_width=True):
        with st.spinner("正在处理..."):
            try:
                st.session_state.kb.add_files_from_dir(UPLOAD_DIR, replace=True)
                st.session_state.kb.build()
                st.success("知识库更新完成！")
                st.rerun()
            except Exception as e:
                st.error(f"更新失败: {e}")

    # 显示知识块预览
    kb_info = st.session_state.kb.get_collection_info()
    if kb_info.get("total_chunks", 0) > 0:
        st.info(f"📊 当前知识库包含 {kb_info['total_chunks']} 个知识块")

        with st.expander("👁️ 预览知识块"):
            chunks = st.session_state.kb.get_all_knowledge_points()
            for i, chunk in enumerate(chunks[:5], 1):
                st.markdown(f"**知识块 {i}:**")
                st.text(chunk[:300] + "..." if len(chunk) > 300 else chunk)
                st.divider()
    else:
        st.warning("⚠️ 知识库为空，请先上传资料或爬取网络资源")


def render_exam_spec_section():
    """渲染考试规格区域"""
    st.header("📝 设置考试规格")

    col1, col2 = st.columns([2, 1])

    with col1:
        exam_spec = st.text_input(
            "考试规格",
            placeholder="如：选择题 40分 8题，简答 40分 4题，大题 20分 2题",
            help="设置试卷的题型、分值和题数"
        )

    with col2:
        st.markdown("**规格预览:**")
        if exam_spec:
            spec = ExamSpecParser.parse(exam_spec)
            st.json(spec)

    return exam_spec


def render_generation_section(exam_spec: str, num_papers: int, coverage_threshold: float):
    """渲染生成区域"""
    st.header("🎯 生成模拟卷")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        generate_btn = st.button(
            "🚀 一键生成 5 套模拟卷",
            key="btn_generate",
            use_container_width=True,
            type="primary"
        )

    with col2:
        st.metric("试卷数量", num_papers)

    with col3:
        st.metric("覆盖率阈值", f"{coverage_threshold:.0%}")

    if generate_btn:
        if not exam_spec:
            st.error("请先设置考试规格")
            return

        kb_info = st.session_state.kb.get_collection_info()
        if kb_info.get("total_chunks", 0) == 0:
            st.error("请先上传课程资料或爬取网络资源")
            return

        # 开始生成
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Step 1: 构建知识库
            status_text.text("📚 正在构建知识库...")
            progress_bar.progress(20)
            time.sleep(0.5)

            # Step 2: 生成试卷
            status_text.text("✍️ 正在生成试卷...")
            progress_bar.progress(40)

            generator = MockPaperGenerator(
                knowledge_base=st.session_state.kb,
                exam_spec=exam_spec,
                course_name="课程"
            )

            result = generator.generate_all(
                num_papers=num_papers,
                coverage_threshold=coverage_threshold
            )

            progress_bar.progress(80)
            status_text.text("✅ 验证覆盖率...")
            time.sleep(0.5)

            # Step 3: 完成
            progress_bar.progress(100)
            status_text.text("🎉 生成完成！")

            st.session_state.generated_papers = result["papers"]
            st.session_state.coverage_rate = result["coverage_rate"]
            st.session_state.papers_generated = True

            # 显示结果
            st.success(f"✅ 成功生成 {len(result['papers'])} 套试卷！")
            st.info(f"📊 知识点覆盖率: {result['coverage_rate']:.1%}")

            if result.get("verification"):
                st.json(result["verification"])

        except Exception as e:
            st.error(f"生成失败: {e}")
            logger.exception("生成失败")


def render_download_section():
    """渲染下载区域"""
    st.header("📥 下载试卷")

    if not st.session_state.papers_generated:
        st.info("👆 请先点击「生成模拟卷」")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        download_format = st.selectbox("下载格式", ["docx", "pdf"])

    with col2:
        st.metric("已生成试卷", len(st.session_state.generated_papers))

    # 生成覆盖率报告
    st.subheader("📊 覆盖率报告")
    chunks = st.session_state.kb.get_all_knowledge_points()
    report = CoverageAnalyzer.generate_coverage_report(
        st.session_state.generated_papers,
        chunks
    )
    st.markdown(report)

    # 下载按钮
    st.divider()

    if st.button("📦 打包下载全部试卷", key="btn_download", use_container_width=True, type="primary"):
        with st.spinner("正在打包..."):
            try:
                generator = MockPaperGenerator(
                    knowledge_base=st.session_state.kb,
                    exam_spec="",
                    course_name="课程"
                )

                zip_path = generator.download_all(
                    st.session_state.generated_papers,
                    OUTPUT_DIR,
                    download_format
                )

                st.success(f"✅ 已打包完成！")

                # 提供下载链接
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="⬇️ 点击下载",
                        data=f.read(),
                        file_name=zip_path.name,
                        mime="application/zip"
                    )

            except Exception as e:
                st.error(f"打包失败: {e}")

    # 逐套预览
    st.divider()
    st.subheader("📋 试卷预览")

    for i, paper in enumerate(st.session_state.generated_papers, 1):
        with st.expander(f"📄 模拟卷 {i}: {paper.get('paper_title', f'第{i}套')}"):
            st.json(paper)


# ==================== 主函数 ====================
def main():
    """主函数"""
    # 检查配置
    if not check_config():
        st.warning("⚠️ 请在 config.py 中配置有效的 API Key")

    # 渲染侧边栏
    num_papers, coverage_threshold = render_sidebar()

    # 渲染主页面
    render_header()
    render_upload_section()

    st.divider()

    render_knowledge_section()

    st.divider()

    exam_spec = render_exam_spec_section()

    st.divider()

    render_generation_section(exam_spec, num_papers, coverage_threshold)

    st.divider()

    render_download_section()

    # 页脚
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "UniExamAgent-CN | 中国大学考试专家 AI Agent | "
        "基于 LangGraph + LangChain + ChromaDB"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
