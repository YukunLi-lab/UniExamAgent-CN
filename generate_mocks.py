"""
UniExamAgent-CN 模拟卷生成核心模块
5 套生成逻辑 + 覆盖验证 + 变体算法
"""

import time
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from loguru import logger
from tqdm import tqdm

from agents import ExamGeneratorAgent
from rag_pipeline import KnowledgeBaseBuilder
from utils import ExamSpecParser, PaperExporter
from config import DEFAULT_NUM_PAPERS, COVERAGE_THRESHOLD, MAX_RETRIES, OUTPUT_DIR


@dataclass
class MockPaperResult:
    """生成的模拟卷结果"""
    paper_id: str
    paper: Dict[str, Any]
    knowledge_coverage: List[str]
    difficulty_distribution: Dict[str, float]
    is_unique: bool  # 是否与其他卷子不同


class MockPaperGenerator:
    """5 套模拟卷生成器"""

    def __init__(
        self,
        knowledge_base: KnowledgeBaseBuilder,
        exam_spec: str,
        course_name: str,
        university: str = "中山大学"
    ):
        self.kb = knowledge_base
        self.exam_spec = exam_spec
        self.parsed_spec = ExamSpecParser.parse(exam_spec)
        self.course_name = course_name
        self.university = university
        self.agent = ExamGeneratorAgent()

        logger.info(f"考试规格解析: {self.parsed_spec}")

    def generate_all(
        self,
        num_papers: int = 5,
        coverage_threshold: float = 0.98
    ) -> Dict[str, Any]:
        """
        生成 5 套模拟卷的完整流程

        流程：
        1. 提取知识点清单
        2. 分析考试规律
        3. 生成 5 套变体
        4. 验证覆盖率
        5. 不达标则重新生成
        """
        logger.info("=" * 50)
        logger.info("开始生成 5 套模拟卷")
        logger.info("=" * 50)

        # Step 1: 获取知识内容
        knowledge_contents = self.kb.get_all_knowledge_points()
        if not knowledge_contents:
            raise ValueError("知识库为空，请先上传课程资料或爬取网络资源")

        logger.info(f"知识库包含 {len(knowledge_contents)} 个知识块")

        # Step 2: 调用 Agent 生成
        result = self._generate_with_retry(
            knowledge_contents,
            num_papers,
            coverage_threshold
        )

        # Step 3: 后处理
        papers = result["papers"]
        coverage_rate = result["coverage_rate"]

        # 验证唯一性
        papers = self._ensure_uniqueness(papers)

        # 生成答案解析
        papers = self._add_answer_sheet(papers)

        logger.info("=" * 50)
        logger.info(f"生成完成！共 {len(papers)} 套试卷")
        logger.info(f"覆盖率: {coverage_rate:.1%}")
        logger.info("=" * 50)

        return {
            "papers": papers,
            "coverage_rate": coverage_rate,
            "verification": result.get("verification"),
            "passed": coverage_rate >= coverage_threshold
        }

    def _generate_with_retry(
        self,
        knowledge_contents: List[str],
        num_papers: int,
        coverage_threshold: float
    ) -> Dict[str, Any]:
        """带重试的生成"""
        for attempt in range(MAX_RETRIES):
            logger.info(f"生成尝试 {attempt + 1}/{MAX_RETRIES}")

            result = self.agent.generate_exam_papers(
                exam_spec=self.exam_spec,
                course_name=self.course_name,
                university=self.university,
                knowledge_contents=knowledge_contents,
                num_papers=num_papers,
                coverage_threshold=coverage_threshold
            )

            if result["error"]:
                logger.error(f"生成出错: {result['error']}")
                continue

            coverage_rate = result.get("coverage_rate", 0)
            logger.info(f"本次生成覆盖率: {coverage_rate:.1%}")

            if coverage_rate >= coverage_threshold:
                logger.info("✅ 覆盖率达标！")
                result["passed"] = True
                return result
            else:
                logger.warning(f"❌ 覆盖率未达标 (要求 {coverage_threshold:.1%})，重试...")

        logger.error(f"达到最大重试次数 {MAX_RETRIES}，返回当前最佳结果")
        result["passed"] = False
        return result

    def _ensure_uniqueness(self, papers: List[Dict]) -> List[Dict]:
        """确保 5 套卷子各不相同"""
        if len(papers) <= 1:
            return papers

        unique_papers = [papers[0]]
        seen_signatures = [self._compute_signature(papers[0])]

        for paper in papers[1:]:
            signature = self._compute_signature(paper)

            # 检查是否与已有重复
            is_duplicate = any(
                self._similarity(signature, s) > 0.7
                for s in seen_signatures
            )

            if not is_duplicate:
                unique_papers.append(paper)
                seen_signatures.append(signature)
                logger.info(f"卷子 {paper.get('paper_id')} 通过唯一性检查 ✅")
            else:
                logger.warning(f"卷子 {paper.get('paper_id')} 与其他卷子重复，标记 ❌")
                paper["is_unique"] = False

        return unique_papers

    def _compute_signature(self, paper: Dict) -> str:
        """计算卷子签名（用于比较相似度）"""
        import hashlib

        content_parts = []
        for section in paper.get("sections", []):
            for q in section.get("questions", []):
                content_parts.append(q.get("content", ""))

        signature = "|".join(sorted(content_parts))
        return hashlib.md5(signature.encode()).hexdigest()

    def _similarity(self, sig1: str, sig2: str) -> float:
        """计算两个签名的相似度"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, sig1, sig2).ratio()

    def _add_answer_sheet(self, papers: List[Dict]) -> List[Dict]:
        """为每套卷子添加答案解析"""
        for paper in papers:
            answer_sheet = {}

            for section in paper.get("sections", []):
                for q in section.get("questions", []):
                    q_id = q.get("q_id", "")
                    answer_sheet[q_id] = {
                        "answer": q.get("answer", ""),
                        "analysis": q.get("analysis", ""),
                        "knowledge_points": q.get("knowledge_points", [])
                    }

            paper["answer_sheet"] = answer_sheet

        return papers

    def download_all(
        self,
        papers: List[Dict],
        output_dir: Optional[Path] = None,
        format: str = "docx"
    ) -> Path:
        """下载所有试卷"""
        output_dir = output_dir or OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"正在导出 {len(papers)} 套试卷...")

        # 导出每套卷子
        for i, paper in enumerate(papers, 1):
            filename = f"模拟卷_{i}_{paper.get('paper_title', f'第{i}套')}.{format}"
            filepath = output_dir / filename

            if format == "docx":
                PaperExporter.to_docx(paper, filepath)
            elif format == "pdf":
                PaperExporter.to_pdf(paper, filepath)

        # 打包下载
        zip_path = PaperExporter.pack_all(papers, output_dir, format)

        return zip_path


class CoverageAnalyzer:
    """覆盖率分析器"""

    @staticmethod
    def analyze_knowledge_coverage(
        papers: List[Dict],
        knowledge_list: List[str]
    ) -> Dict[str, Any]:
        """分析知识点覆盖情况"""
        covered_kps = set()
        all_kps = set()

        # 从试卷中提取已覆盖的知识点
        for paper in papers:
            for section in paper.get("sections", []):
                for q in section.get("questions", []):
                    for kp in q.get("knowledge_points", []):
                        covered_kps.add(kp)

        # 假设知识清单中的每个条目都是一个 KP
        for i, _ in enumerate(knowledge_list):
            all_kps.add(f"KP-{i:03d}")

        # 计算覆盖率
        coverage_rate = len(covered_kps) / len(all_kps) if all_kps else 0

        # 找出未覆盖的知识点
        uncovered = all_kps - covered_kps

        return {
            "total_knowledge_points": len(all_kps),
            "covered_points": len(covered_kps),
            "uncovered_points": list(uncovered),
            "coverage_rate": coverage_rate,
            "passed": coverage_rate >= COVERAGE_THRESHOLD
        }

    @staticmethod
    def generate_coverage_report(
        papers: List[Dict],
        knowledge_list: List[str]
    ) -> str:
        """生成覆盖率报告"""
        analysis = CoverageAnalyzer.analyze_knowledge_coverage(papers, knowledge_list)

        report = []
        report.append("=" * 50)
        report.append("📊 知识点覆盖率报告")
        report.append("=" * 50)
        report.append(f"总知识点数: {analysis['total_knowledge_points']}")
        report.append(f"已覆盖数: {analysis['covered_points']}")
        report.append(f"覆盖率: {analysis['coverage_rate']:.1%}")
        report.append(f"状态: {'✅ 通过' if analysis['passed'] else '❌ 未达标'}")

        if analysis["uncovered_points"]:
            report.append(f"\n未覆盖知识点 ({len(analysis['uncovered_points'])}个):")
            for kp in analysis["uncovered_points"][:10]:
                report.append(f"  - {kp}")
            if len(analysis["uncovered_points"]) > 10:
                report.append(f"  ... 还有 {len(analysis['uncovered_points']) - 10} 个")

        return "\n".join(report)
