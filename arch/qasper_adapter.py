"""QASPer 数据集适配器

QASPer: A Dataset of Information-Seeking Questions and Answers Anchored in Research Papers

来源: ACL 2021
论文: https://aclanthology.org/2021.naacl-main.15/
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from .task_schema import TemporalSample, TaskType


class QASPerAdapter:
    """QASPer 数据集适配器
    
    原始格式: JSON (字典结构，key为论文ID)
    任务类型: T1 (时间计算) - 论文中的时间理解
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "qasper"
        self.samples: List[TemporalSample] = []
    
    def load(self, split: str = "train") -> List[TemporalSample]:
        """加载QASPer数据集
        
        Args:
            split: "train", "dev", 或 "test"
        """
        filepath = self.data_dir / f"qasper-{split}-v0.3.json"
        
        # Try alternative naming pattern
        if not filepath.exists():
            filepath = self.data_dir / f"qasper-{split}.json"
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            for paper_id, paper in data.items():
                paper_samples = self._convert_paper(paper, split)
                samples.extend(paper_samples)
        
        self.samples = samples
        return samples
    
    def _convert_paper(self, paper: Dict, split: str) -> List[TemporalSample]:
        """转换一篇论文的所有问答"""
        samples = []
        
        paper_id = paper.get("id", "")
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        
        full_text = paper.get("full_text", {})
        paragraphs = []
        for section in full_text.get("paragraphs", []) if isinstance(full_text, dict) else []:
            if isinstance(section, list):
                paragraphs.extend(section)
            else:
                paragraphs.append(section)
        
        context = self._build_context(title, abstract, paragraphs)
        
        for qa in paper.get("qas", []):
            sample = self._convert_qa(qa, context, paper_id, split)
            if sample:
                samples.append(sample)
        
        return samples
    
    def _build_context(self, title: str, abstract: str, paragraphs: List[str]) -> str:
        """构建上下文"""
        parts = []
        
        if title:
            parts.append(f"[Title]\n{title}")
        
        if abstract:
            parts.append(f"[Abstract]\n{abstract}")
        
        if paragraphs:
            text_parts = []
            for i, p in enumerate(paragraphs[:10]):
                text_parts.append(f"Para {i+1}: {p}")
            parts.append(f"[Full Text]\n" + "\n".join(text_parts))
        
        return "\n\n".join(parts)
    
    def _convert_qa(self, qa: Dict, context: str, paper_id: str, split: str) -> Optional[TemporalSample]:
        """转换一个问答对"""
        question = qa.get("question", "")
        if not question:
            return None
        
        answers = qa.get("answers", [])
        if not answers:
            return None
        
        best_answer = self._extract_best_answer(answers)
        if not best_answer:
            return None
        
        metadata = {
            "question_id": qa.get("question_id", ""),
            "paper_id": paper_id,
            "nlp_background": qa.get("nlp_background", ""),
            "topic_background": qa.get("topic_background", ""),
        }
        
        return TemporalSample(
            id=f"qasper_{split}_{paper_id}_{qa.get('question_id', '')}",
            task_type=TaskType.T1_TEMPORAL_CALCULATION,
            context=context,
            query=question,
            answer=best_answer,
            ground_truth={
                "answer": best_answer,
                "all_answers": [self._extract_answer_text(a) for a in answers]
            },
            metadata=metadata
        )
    
    def _extract_best_answer(self, answers: List[Dict]) -> Optional[str]:
        """提取最佳答案"""
        for answer in answers:
            answer_text = self._extract_answer_text(answer)
            if answer_text and len(answer_text) > 5:
                return answer_text
        return None
    
    def _extract_answer_text(self, answer: Dict) -> str:
        """提取答案文本"""
        if not answer:
            return ""
        
        ans = answer.get("answer", {})
        if isinstance(ans, str):
            return ans
        
        if isinstance(ans, dict):
            if ans.get("unanswerable"):
                return "Unanswerable"
            
            free_form = ans.get("free_form_answer", "")
            if free_form:
                return free_form
            
            extractive = ans.get("extractive_spans", [])
            if extractive:
                return " ".join(extractive)
            
            yes_no = ans.get("yes_no")
            if yes_no is not None:
                return "Yes" if yes_no else "No"
        
        return ""


def load_qasper_data(data_dir: str, split: str = "train") -> List[TemporalSample]:
    """便捷函数：加载QASPer数据
    
    Args:
        data_dir: 数据根目录
        split: 数据集划分 ("train", "dev", "test")
    
    Returns:
        TemporalSample列表
    """
    adapter = QASPerAdapter(data_dir)
    return adapter.load(split)


if __name__ == "__main__":
    import sys
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    print("加载QASPer数据集...")
    adapter = QASPerAdapter(str(data_dir))
    
    for split in ["train", "dev", "test"]:
        try:
            samples = adapter.load(split)
            print(f"  {split}: {len(samples)} samples")
        except FileNotFoundError as e:
            print(f"  {split}: {e}")
