"""评估报告生成器"""

import json
from datetime import datetime
from typing import Dict, List, Any
from config import EVALUATION_OUTPUT_PATH

class Evaluator:
    """评估报告生成器"""
    
    def __init__(self):
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "qa_evaluation": {},
            "dialogue_evaluation": {},
            "issues": [],
            "recommendations": []
        }
    
    def add_qa_evaluation(self, qa_type: str, questions: List[Dict], 
                          validation_results: List[Dict]):
        """添加QA评估结果"""
        total = len(questions)
        valid_count = sum(1 for v in validation_results if v.get("is_valid", False))
        
        # 统计各维度
        dimensions = {
            "mutual_exclusive": 0,
            "unique_answer": 0,
            "clear_question": 0,
            "good_distractors": 0,
            "logical_time": 0
        }
        
        for v in validation_results:
            for dim in dimensions:
                if v.get(dim, False):
                    dimensions[dim] += 1
        
        # 收集问题
        issues = []
        for v in validation_results:
            if not v.get("is_valid", False):
                issues.append({
                    "question_id": v.get("question_id", "unknown"),
                    "issues": v.get("issues", []),
                    "quality_score": v.get("quality_score", 0)
                })
        
        self.report["qa_evaluation"][qa_type] = {
            "total": total,
            "valid": valid_count,
            "validation_rate": valid_count / total if total > 0 else 0,
            "average_score": sum(v.get("quality_score", 0) for v in validation_results) / total if total > 0 else 0,
            "dimensions": {
                dim: {"count": count, "rate": count / total if total > 0 else 0}
                for dim, count in dimensions.items()
            },
            "issues": issues
        }
    
    def add_dialogue_evaluation(self, dialogue_type: str, questions: List[Dict],
                                validation_results: List[Dict]):
        """添加对话评估结果"""
        total = len(questions)
        valid_count = sum(1 for v in validation_results if v.get("is_valid", False))
        
        # 统计各维度
        dimensions = {
            "natural_dialogue": 0,
            "clear_time_clues": 0,
            "deducible_answer": 0,
            "good_distractors": 0
        }
        
        for v in validation_results:
            for dim in dimensions:
                if v.get(dim, False):
                    dimensions[dim] += 1
        
        # 收集问题
        issues = []
        for v in validation_results:
            if not v.get("is_valid", False):
                issues.append({
                    "question_id": v.get("question_id", "unknown"),
                    "issues": v.get("issues", []),
                    "quality_score": v.get("quality_score", 0)
                })
        
        self.report["dialogue_evaluation"][dialogue_type] = {
            "total": total,
            "valid": valid_count,
            "validation_rate": valid_count / total if total > 0 else 0,
            "average_score": sum(v.get("quality_score", 0) for v in validation_results) / total if total > 0 else 0,
            "dimensions": {
                dim: {"count": count, "rate": count / total if total > 0 else 0}
                for dim, count in dimensions.items()
            },
            "issues": issues
        }
    
    def generate_summary(self):
        """生成总结"""
        # QA总结
        qa_total = sum(data["total"] for data in self.report["qa_evaluation"].values())
        qa_valid = sum(data["valid"] for data in self.report["qa_evaluation"].values())
        qa_avg_score = 0
        if qa_total > 0:
            qa_avg_score = sum(data["average_score"] * data["total"] 
                              for data in self.report["qa_evaluation"].values()) / qa_total
        
        # 对话总结
        dialogue_total = sum(data["total"] for data in self.report["dialogue_evaluation"].values())
        dialogue_valid = sum(data["valid"] for data in self.report["dialogue_evaluation"].values())
        dialogue_avg_score = 0
        if dialogue_total > 0:
            dialogue_avg_score = sum(data["average_score"] * data["total"] 
                                    for data in self.report["dialogue_evaluation"].values()) / dialogue_total
        
        self.report["summary"] = {
            "qa": {
                "total_questions": qa_total,
                "valid_questions": qa_valid,
                "validation_rate": qa_valid / qa_total if qa_total > 0 else 0,
                "average_quality_score": qa_avg_score
            },
            "dialogue": {
                "total_questions": dialogue_total,
                "valid_questions": dialogue_valid,
                "validation_rate": dialogue_valid / dialogue_total if dialogue_total > 0 else 0,
                "average_quality_score": dialogue_avg_score
            },
            "overall": {
                "total_questions": qa_total + dialogue_total,
                "valid_questions": qa_valid + dialogue_valid,
                "validation_rate": (qa_valid + dialogue_valid) / (qa_total + dialogue_total) if (qa_total + dialogue_total) > 0 else 0
            }
        }
        
        # 生成建议
        self._generate_recommendations()
    
    def _generate_recommendations(self):
        """生成改进建议"""
        recommendations = []
        
        # 检查QA问题
        for qa_type, data in self.report["qa_evaluation"].items():
            if data["validation_rate"] < 0.8:
                recommendations.append(f"QA类型 '{qa_type}' 的验证率较低 ({data['validation_rate']:.1%})，需要改进题目质量")
            
            # 检查各维度
            for dim, dim_data in data["dimensions"].items():
                if dim_data["rate"] < 0.7:
                    recommendations.append(f"QA类型 '{qa_type}' 的 '{dim}' 维度表现不佳 ({dim_data['rate']:.1%})")
        
        # 检查对话问题
        for dialogue_type, data in self.report["dialogue_evaluation"].items():
            if data["validation_rate"] < 0.8:
                recommendations.append(f"对话类型 '{dialogue_type}' 的验证率较低 ({data['validation_rate']:.1%})，需要改进题目质量")
        
        self.report["recommendations"] = recommendations
    
    def save_report(self, output_path: str = None):
        """保存评估报告"""
        if output_path is None:
            output_path = EVALUATION_OUTPUT_PATH
        
        self.generate_summary()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        print(f"评估报告已保存到: {output_path}")
        return self.report
    
    def print_summary(self):
        """打印评估摘要"""
        self.generate_summary()
        
        print("\n" + "=" * 60)
        print("时间推理Benchmark评估报告")
        print("=" * 60)
        
        # QA摘要
        print("\n【QA题目评估】")
        qa_summary = self.report["summary"]["qa"]
        print(f"  总题目数: {qa_summary['total_questions']}")
        print(f"  有效题目: {qa_summary['valid_questions']}")
        print(f"  验证率: {qa_summary['validation_rate']:.1%}")
        print(f"  平均质量分: {qa_summary['average_quality_score']:.2f}")
        
        print("\n  各类型详情:")
        for qa_type, data in self.report["qa_evaluation"].items():
            print(f"    - {qa_type}: {data['valid']}/{data['total']} ({data['validation_rate']:.1%})")
        
        # 对话摘要
        print("\n【对话题目评估】")
        dialogue_summary = self.report["summary"]["dialogue"]
        print(f"  总题目数: {dialogue_summary['total_questions']}")
        print(f"  有效题目: {dialogue_summary['valid_questions']}")
        print(f"  验证率: {dialogue_summary['validation_rate']:.1%}")
        print(f"  平均质量分: {dialogue_summary['average_quality_score']:.2f}")
        
        print("\n  各类型详情:")
        for dialogue_type, data in self.report["dialogue_evaluation"].items():
            print(f"    - {dialogue_type}: {data['valid']}/{data['total']} ({data['validation_rate']:.1%})")
        
        # 总体摘要
        print("\n【总体评估】")
        overall = self.report["summary"]["overall"]
        print(f"  总题目数: {overall['total_questions']}")
        print(f"  有效题目: {overall['valid_questions']}")
        print(f"  总体验证率: {overall['validation_rate']:.1%}")
        
        # 建议
        if self.report["recommendations"]:
            print("\n【改进建议】")
            for i, rec in enumerate(self.report["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 60)
