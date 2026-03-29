"""Winogrande 数据集适配器

WinoGrande: An Adversarial Winograd Schema Challenge at Scale
来源: ACL 2020
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from .task_schema import TemporalSample, TaskType


class WinograndeAdapter:
    """Winogrande 数据集适配器
    
    原始格式: Parquet (sentence, option1, option2, answer)
    任务类型: T2 (状态更新) - 代词消解/常识推理
    
    子数据集:
    - winogrande_xs: 最小版本
    - winogrande_s: 小版本
    - winogrande_m: 中版本
    - winogrande_l: 大版本
    - winogrande_xl: 最大版本
    - winogrande_debiased: 去偏版本
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir) / "Winogrande"
        self.samples: List[TemporalSample] = []
    
    def load(self, subset: str = "winogrande_debiased", split: str = "train") -> List[TemporalSample]:
        """加载Winogrande数据集
        
        Args:
            subset: 子数据集 ("winogrande_xs", "winogrande_s", "winogrande_m", 
                    "winogrande_l", "winogrande_xl", "winogrande_debiased")
            split: 数据划分 ("train", "test", "validation")
        """
        subset_dir = self.data_dir / subset
        
        split_file = f"{split}-00000-of-00001.parquet"
        filepath = subset_dir / split_file
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        df = pd.read_parquet(filepath)
        samples = self._convert_dataframe(df, subset, split)
        
        self.samples = samples
        return samples
    
    def load_all_subsets(self, split: str = "train") -> Dict[str, List[TemporalSample]]:
        """加载所有子数据集
        
        Args:
            split: 数据划分
        
        Returns:
            子数据集名称到样本列表的映射
        """
        subsets = [
            "winogrande_xs",
            "winogrande_s", 
            "winogrande_m",
            "winogrande_l",
            "winogrande_xl",
            "winogrande_debiased"
        ]
        
        results = {}
        for subset in subsets:
            try:
                samples = self.load(subset, split)
                results[subset] = samples
            except FileNotFoundError:
                continue
        
        return results
    
    def _convert_dataframe(
        self, 
        df: pd.DataFrame, 
        subset: str, 
        split: str
    ) -> List[TemporalSample]:
        """转换DataFrame为TemporalSample列表"""
        samples = []
        
        for idx, row in df.iterrows():
            sample = self._convert_row(row, idx, subset, split)
            if sample:
                samples.append(sample)
        
        return samples
    
    def _convert_row(
        self, 
        row: pd.Series, 
        idx: int, 
        subset: str, 
        split: str
    ) -> Optional[TemporalSample]:
        """转换一行数据"""
        sentence = row.get("sentence", "")
        option1 = row.get("option1", "")
        option2 = row.get("option2", "")
        answer = str(row.get("answer", ""))
        
        if not sentence or not option1 or not option2:
            return None
        
        correct_option = option1 if answer == "1" else option2
        
        return TemporalSample(
            id=f"winogrande_{subset}_{split}_{idx}",
            task_type=TaskType.T2_STATE_TRACKING,
            context=f"[句子]\n{sentence}\n\n[选项]\nA. {option1}\nB. {option2}",
            query="请根据句子的语义，选择正确的代词指代对象：",
            answer=correct_option,
            ground_truth={
                "answer": answer,
                "option1": option1,
                "option2": option2,
                "correct_option": correct_option
            },
            metadata={
                "subset": subset,
                "split": split,
                "sentence": sentence
            }
        )


def load_winogrande_data(
    data_dir: str, 
    subset: str = "winogrande_debiased", 
    split: str = "train"
) -> List[TemporalSample]:
    """便捷函数：加载Winogrande数据
    
    Args:
        data_dir: 数据根目录
        subset: 子数据集
        split: 数据划分
    
    Returns:
        TemporalSample列表
    """
    adapter = WinograndeAdapter(data_dir)
    return adapter.load(subset, split)


if __name__ == "__main__":
    import sys
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    print("加载Winogrande数据集...")
    adapter = WinograndeAdapter(str(data_dir))
    
    for subset in ["winogrande_debiased", "winogrande_xl"]:
        for split in ["train", "test"]:
            try:
                samples = adapter.load(subset, split)
                print(f"  {subset}/{split}: {len(samples)} samples")
            except FileNotFoundError as e:
                print(f"  {subset}/{split}: {e}")
