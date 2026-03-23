"""
UniExamAgent-CN LangGraph 多智能体模块
定义 Extractor、Crawler、Analyzer、Generator、Verifier Agent
"""

import json
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from loguru import logger

from config import get_llm_config, MODEL_PROVIDER
from prompts import get_prompt
from rag_pipeline import KnowledgeBaseBuilder


# ==================== Agent State ====================
@dataclass
class AgentState(TypedDict):
    """智能体共享状态"""
    messages: List[dict]  # 对话历史
    extracted_knowledge: Optional[Dict]  # 提取的知识
    crawled_results: Optional[List[Dict]]  # 爬取结果
    analysis_result: Optional[Dict]  # 分析结果
    generated_papers: List[Dict]  # 生成的试卷
    verification_result: Optional[Dict]  # 验证结果
    exam_spec: str  # 考试规格
    course_name: str  # 课程名
    university: str  # 学校
    coverage_rate: float  # 覆盖率
    current_step: str  # 当前步骤
    error: Optional[str]  # 错误信息


# ==================== LLM 初始化 ====================
def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    """获取 LLM 实例"""
    config = get_llm_config()

    if config["provider"] == "minimax":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
            model=config["model"],
            temperature=temperature
        )
    elif config["provider"] == "qwen":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
            model=config["model"],
            temperature=temperature
        )
    elif config["provider"] == "glm":
        return ChatOpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
            model=config["model"],
            temperature=temperature
        )
    elif config["provider"] == "ollama":
        return ChatOpenAI(
            base_url=config["base_url"],
            model=config["model"],
            temperature=temperature
        )
    else:
        return ChatOpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
            model=config["model"],
            temperature=temperature
        )


# ==================== Extractor Agent ====================
def extractor_agent(state: AgentState) -> AgentState:
    """知识点提取 Agent"""
    logger.info("执行 Extractor Agent...")

    llm = get_llm(temperature=0.3)
    system_prompt, user_template = get_prompt("extractor")

    # 构建用户消息
    knowledge_contents = state.get("extracted_knowledge", {}).get("contents", [])
    combined_content = "\n\n".join(knowledge_contents)

    user_message = user_template.format(content=combined_content[:10000])

    # 调用 LLM
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ])

    try:
        # 尝试解析 JSON
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        extracted = json.loads(content.strip())
        state["extracted_knowledge"] = extracted
        state["current_step"] = "extraction_complete"
    except Exception as e:
        logger.error(f"解析提取结果失败: {e}")
        state["error"] = f"提取失败: {str(e)}"

    return state


# ==================== Crawler Agent ====================
def crawler_agent(state: AgentState) -> AgentState:
    """网络爬取 Agent"""
    logger.info("执行 Crawler Agent...")

    llm = get_llm(temperature=0.3)
    system_prompt, user_template = get_prompt("crawler")

    user_message = user_template.format(
        university=state.get("university", ""),
        course_name=state.get("course_name", ""),
        keywords=[state.get("course_name", "")],
        max_results=50
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ])

    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        crawled = json.loads(content.strip())
        state["crawled_results"] = crawled if isinstance(crawled, list) else []
        state["current_step"] = "crawl_complete"
    except Exception as e:
        logger.error(f"解析爬取结果失败: {e}")
        state["crawled_results"] = []
        state["error"] = f"爬取失败: {str(e)}"

    return state


# ==================== Analyzer Agent ====================
def analyzer_agent(state: AgentState) -> AgentState:
    """知识点分析 Agent"""
    logger.info("执行 Analyzer Agent...")

    llm = get_llm(temperature=0.5)
    system_prompt, user_template = get_prompt("analyzer")

    user_message = user_template.format(
        knowledge_list=json.dumps(state.get("extracted_knowledge", {}), ensure_ascii=False),
        exam_spec=state.get("exam_spec", "")
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ])

    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        analysis = json.loads(content.strip())
        state["analysis_result"] = analysis
        state["current_step"] = "analysis_complete"
    except Exception as e:
        logger.error(f"解析分析结果失败: {e}")
        state["error"] = f"分析失败: {str(e)}"

    return state


# ==================== Generator Agent ====================
def generator_agent(state: AgentState) -> AgentState:
    """试卷生成 Agent"""
    logger.info("执行 Generator Agent...")

    llm = get_llm(temperature=0.8)  # 高温度增加多样性
    system_prompt, user_template = get_prompt("generator")

    papers = []

    # 生成 5 套试卷
    for i in range(1, 6):
        user_message = user_template.format(
            paper_num=i,
            exam_spec=state.get("exam_spec", ""),
            knowledge_requirements=json.dumps(state.get("extracted_knowledge", {}), ensure_ascii=False),
            exam_patterns=json.dumps(state.get("analysis_result", {}), ensure_ascii=False)
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])

        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]

            paper = json.loads(content.strip())
            paper["paper_id"] = f"PAPER-{i:03d}"
            papers.append(paper)
            logger.info(f"生成第 {i}/5 套试卷成功")
        except Exception as e:
            logger.error(f"解析第 {i} 套试卷失败: {e}")

    state["generated_papers"] = papers
    state["current_step"] = "generation_complete"

    return state


# ==================== Verifier Agent ====================
def verifier_agent(state: AgentState) -> AgentState:
    """试卷验证 Agent"""
    logger.info("执行 Verifier Agent...")

    llm = get_llm(temperature=0.3)
    system_prompt, user_template = get_prompt("verifier")

    user_message = user_template.format(
        papers=json.dumps(state.get("generated_papers", []), ensure_ascii=False, indent=2),
        knowledge_list=json.dumps(state.get("extracted_knowledge", {}), ensure_ascii=False),
        exam_spec=state.get("exam_spec", ""),
        threshold=0.98
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ])

    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        verification = json.loads(content.strip())
        state["verification_result"] = verification
        state["coverage_rate"] = verification.get("coverage_rate", 0)
        state["current_step"] = "verification_complete"
    except Exception as e:
        logger.error(f"解析验证结果失败: {e}")
        state["error"] = f"验证失败: {str(e)}"
        state["coverage_rate"] = 0

    return state


# ==================== 构建 LangGraph ====================
def build_exam_agent_graph() -> StateGraph:
    """构建考试生成 Agent 图"""

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("extractor", extractor_agent)
    workflow.add_node("crawler", crawler_agent)
    workflow.add_node("analyzer", analyzer_agent)
    workflow.add_node("generator", generator_agent)
    workflow.add_node("verifier", verifier_agent)

    # 设置入口
    workflow.set_entry_point("extractor")

    # 定义流程
    workflow.add_edge("extractor", "crawler")
    workflow.add_edge("crawler", "analyzer")
    workflow.add_edge("analyzer", "generator")
    workflow.add_edge("generator", "verifier")
    workflow.add_edge("verifier", END)

    return workflow.compile()


class ExamGeneratorAgent:
    """考试生成 Agent 包装类"""

    def __init__(self):
        self.graph = build_exam_agent_graph()

    def generate_exam_papers(
        self,
        exam_spec: str,
        course_name: str,
        university: str,
        knowledge_contents: List[str],
        num_papers: int = 5,
        coverage_threshold: float = 0.98
    ) -> Dict[str, Any]:
        """
        完整的考试卷生成流程

        Args:
            exam_spec: 考试规格，如"选择题 40分 8题，简答 40分 4题，大题 20分 2题"
            course_name: 课程名
            university: 学校
            knowledge_contents: 知识内容列表
            num_papers: 生成试卷数量
            coverage_threshold: 覆盖率阈值

        Returns:
            生成结果字典
        """
        # 初始化状态
        initial_state: AgentState = {
            "messages": [],
            "extracted_knowledge": {"contents": knowledge_contents},
            "crawled_results": [],
            "analysis_result": {},
            "generated_papers": [],
            "verification_result": None,
            "exam_spec": exam_spec,
            "course_name": course_name,
            "university": university,
            "coverage_rate": 0,
            "current_step": "init",
            "error": None
        }

        # 执行图
        final_state = self.graph.invoke(initial_state)

        # 检查验证结果
        if final_state.get("coverage_rate", 0) < coverage_threshold:
            logger.warning(
                f"覆盖率 {final_state.get('coverage_rate')} 低于阈值 {coverage_threshold}，"
                "可能需要人工审核"
            )

        return {
            "papers": final_state.get("generated_papers", []),
            "verification": final_state.get("verification_result"),
            "coverage_rate": final_state.get("coverage_rate", 0),
            "error": final_state.get("error")
        }


# ==================== 便捷函数 ====================
def create_agent() -> ExamGeneratorAgent:
    """创建 Agent 实例"""
    return ExamGeneratorAgent()
