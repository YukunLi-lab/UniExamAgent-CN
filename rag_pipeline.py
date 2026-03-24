"""
UniExamAgent-CN RAG 流程模块
PPT/PDF/爬取内容 → FAISS 向量入库
"""

import hashlib
import pickle
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

import faiss
import numpy as np
from loguru import logger
from tqdm import tqdm

from config import CHROMA_DIR, EMBEDDING_MODEL, EMBEDDING_DIM, CHUNK_SIZE, CHUNK_OVERLAP
from utils import FileProcessor, CourseCrawler


@dataclass
class KnowledgeChunk:
    """知识块数据结构"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    source: str  # "pptx" | "pdf" | "crawl" | "txt"


class KnowledgeBaseBuilder:
    """知识库构建器 - RAG 核心（使用 FAISS）"""

    def __init__(self):
        self.index_path = CHROMA_DIR / "faiss_index.bin"
        self.chunks_path = CHROMA_DIR / "chunks.pkl"
        self.metadata_path = CHROMA_DIR / "metadata.pkl"

        # 初始化 FAISS 索引
        self.index = None
        self.chunks: List[KnowledgeChunk] = []
        self.metadata: List[Dict[str, Any]] = []

        # 加载已有索引
        self._load()

        # 初始化处理器
        self.file_processor = FileProcessor()
        self.crawler = CourseCrawler()

    def _load(self):
        """加载已有索引"""
        if self.index_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"已加载 FAISS 索引，共 {self.index.ntotal} 个向量")
            except Exception as e:
                logger.warning(f"加载索引失败: {e}，将创建新索引")
                self.index = faiss.IndexFlatL2(EMBEDDING_DIM)

        if self.chunks_path.exists():
            try:
                with open(self.chunks_path, 'rb') as f:
                    chunks_data = pickle.load(f)
                # 加载为字典列表
                self.chunks = [
                    KnowledgeChunk(
                        chunk_id=c["chunk_id"],
                        content=c["content"],
                        metadata=c["metadata"],
                        source=c["source"]
                    ) for c in chunks_data
                ]
                logger.info(f"已加载 {len(self.chunks)} 个知识块")
            except Exception as e:
                logger.warning(f"加载知识块失败: {e}")
                self.chunks = []

        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
            except Exception as e:
                logger.warning(f"加载元数据失败: {e}")
                self.metadata = []

        if self.index is None:
            self.index = faiss.IndexFlatL2(EMBEDDING_DIM)

    def _save(self):
        """保存索引到磁盘"""
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        # 保存为普通字典列表（避免 pickle dataclass 问题）
        chunks_dict = [
            {"chunk_id": c.chunk_id, "content": c.content,
             "metadata": c.metadata, "source": c.source}
            for c in self.chunks
        ]
        with open(self.chunks_path, 'wb') as f:
            pickle.dump(chunks_dict, f)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        logger.info(f"索引已保存到 {CHROMA_DIR}")

    def _get_embedding(self, text: str) -> np.ndarray:
        """简单文本嵌入（使用词频统计作为演示）"""
        # 简单的 BOW embedding（实际应用中应使用 sentence-transformers）
        words = text.lower().split()
        vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        for i, word in enumerate(words[:EMBEDDING_DIM]):
            vec[i] = hash(word) % 1000 / 1000.0
        # 归一化
        faiss.normalize_L2(vec.reshape(1, -1))
        return vec

    def add_file(self, file_path: Path) -> int:
        """添加单个文件到知识库"""
        logger.info(f"正在处理文件: {file_path}")

        content = self.file_processor.process_file(file_path)
        if not content:
            return 0

        chunks = self._chunk_text(content, {
            "source": file_path.suffix,
            "file_name": file_path.name,
            "type": "upload"
        })

        self.chunks.extend(chunks)
        logger.info(f"从 {file_path.name} 提取 {len(chunks)} 个知识块")
        return len(chunks)

    def add_files_from_dir(self, dir_path: Path, replace: bool = False) -> int:
        """从目录批量添加文件"""
        if replace:
            # 替换模式：清空现有 chunks
            self.chunks = []
        total_chunks = 0

        for file_path in tqdm(list(dir_path.iterdir()), desc="处理文件"):
            if file_path.is_file():
                total_chunks += self.add_file(file_path)

        return total_chunks

    def crawl_and_add(self, university: str, course_name: str,
                      keywords: List[str], max_results: int = 50) -> int:
        """爬取并添加网络资料"""
        logger.info(f"正在爬取: {university} - {course_name}")

        results = self.crawler.crawl(university, course_name, keywords, max_results)

        chunks = []
        for item in results:
            if item.get("crawl_status") == "success":
                content = f"来源: {item['source_name']}\n标题: {item['title']}\n摘要: {item['content_summary']}"

                chunk = self._chunk_text(content, {
                    "source": "web",
                    "source_name": item["source_name"],
                    "source_url": item["source_url"],
                    "title": item["title"],
                    "relevance_score": item["relevance_score"],
                    "type": "crawl"
                })
                chunks.extend(chunk)

        self.chunks.extend(chunks)
        logger.info(f"从网络爬取添加 {len(chunks)} 个知识块")
        return len(chunks)

    def _chunk_text(self, text: str, metadata: Dict) -> List[KnowledgeChunk]:
        """将长文本分块"""
        chunks = []

        # 简单按段落分块
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) < CHUNK_SIZE:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunk_id = hashlib.md5(current_chunk.encode()).hexdigest()[:16]
                    chunks.append(KnowledgeChunk(
                        chunk_id=f"chunk_{chunk_id}",
                        content=current_chunk.strip(),
                        metadata={**metadata, "chunk_index": chunk_index},
                        source=metadata.get("type", "unknown")
                    ))
                    chunk_index += 1

                current_chunk = para + "\n\n"

        # 处理最后一个块
        if current_chunk.strip():
            chunk_id = hashlib.md5(current_chunk.encode()).hexdigest()[:16]
            chunks.append(KnowledgeChunk(
                chunk_id=f"chunk_{chunk_id}",
                content=current_chunk.strip(),
                metadata={**metadata, "chunk_index": chunk_index},
                source=metadata.get("type", "unknown")
            ))

        return chunks

    def build(self, batch_size: int = 100) -> None:
        """构建向量数据库"""
        if not self.chunks:
            logger.warning("没有知识块可添加")
            return

        logger.info(f"正在构建向量库，共 {len(self.chunks)} 个知识块...")

        # 重新构建索引
        self.index = faiss.IndexFlatL2(EMBEDDING_DIM)

        # 批量添加
        vectors = []
        for i in tqdm(range(0, len(self.chunks), batch_size), desc="向量化"):
            batch = self.chunks[i:i + batch_size]
            for chunk in batch:
                vec = self._get_embedding(chunk.content)
                vectors.append(vec)

        if vectors:
            vectors_array = np.array(vectors).astype('float32')
            faiss.normalize_L2(vectors_array)
            self.index.add(vectors_array)

        # 保存
        self._save()

        logger.info(f"向量库构建完成，共 {self.index.ntotal} 个向量")

    def query(self, query_text: str, top_k: int = 10) -> List[Dict]:
        """查询相关知识块"""
        if self.index.ntotal == 0:
            return []

        query_vec = self._get_embedding(query_text).reshape(1, -1)
        faiss.normalize_L2(query_vec)

        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_vec, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                results.append({
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "distance": float(dist)
                })

        return results

    def get_all_knowledge_points(self) -> List[str]:
        """获取所有知识块内容"""
        return [chunk.content for chunk in self.chunks]

    def get_collection_info(self) -> Dict:
        """获取向量库信息"""
        return {
            "total_chunks": self.index.ntotal if self.index else 0,
            "sources": self._count_by_source()
        }

    def _count_by_source(self) -> Dict[str, int]:
        """按来源统计"""
        counts = {}
        for chunk in self.chunks:
            source = chunk.source
            counts[source] = counts.get(source, 0) + 1
        return counts

    def clear(self) -> None:
        """清空知识库"""
        self.index = faiss.IndexFlatL2(EMBEDDING_DIM)
        self.chunks = []
        self.metadata = []
        if self.index_path.exists():
            os.remove(str(self.index_path))
        if self.chunks_path.exists():
            os.remove(str(self.chunks_path))
        if self.metadata_path.exists():
            os.remove(str(self.metadata_path))
        logger.info("知识库已清空")


class RAGPipeline:
    """RAG 检索增强生成管道"""

    def __init__(self, knowledge_base: KnowledgeBaseBuilder):
        self.kb = knowledge_base

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict]:
        """检索相关上下文"""
        return self.kb.query(query, top_k)

    def build_context(self, query: str, knowledge_requirements: List[str]) -> str:
        """构建 RAG 上下文"""
        contexts = []

        # 检索每个知识点
        for req in knowledge_requirements:
            results = self.retrieve(req, top_k=5)
            for r in results:
                contexts.append(r["content"])

        # 去重并连接
        unique_contexts = list(dict.fromkeys(contexts))
        return "\n\n---\n\n".join(unique_contexts[:10])

    def generate_prompt(self, question: str, context: str) -> str:
        """构建带上下文的提示词"""
        return f"""基于以下背景知识回答问题：

背景知识：
{context}

问题：{question}

请给出准确、详细的回答。"""
