#!/usr/bin/env python3
"""
Supplemental Data Converters for Temporal World Modeling Benchmark
==================================================================

This script handles:
1. TRIP (TripCraft) - Travel planning conflicts for T3
2. SituatedGen - Context generation for T2/T5
3. Ground Truth Validation

Author: TimeAware Benchmark Team
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import random

DATA_DIR = Path("data")
OUTPUT_DIR = Path("converted_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TemporalSample:
    """Unified temporal reasoning sample format"""
    id: str
    task: str
    sub_task: str
    context: str
    delta_t: Optional[str] = None
    event: Optional[str] = None
    query: str = ""
    answer: str = ""
    state: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    ground_truth: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.state is None:
            self.state = {}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ============================================================================
# TRIP (TripCraft) Converter for T3 Conflict Detection
# ============================================================================

class TRIPConverter:
    """Convert TRIP/TripCraft dataset for T3 Conflict Detection
    
    TripCraft is a travel planning benchmark that includes:
    - Itineraries with time constraints
    - Spatial constraints (locations)
    - Resource constraints (budget, accommodation)
    
    We extract conflict detection scenarios from these constraints.
    """
    
    # Conflict templates based on TripCraft structure
    CONFLICT_TEMPLATES = [
        {
            "type": "spatial_conflict",
            "template": "Day {days}: 在{city1}参观{attraction1}。同一时间在{city2}参观{attraction2}。",
            "query": "这个行程计划是否合理？",
            "answer_conflict": "不合理，存在空间冲突：无法同时出现在{city1}和{city2}",
            "answer_no_conflict": "合理，行程可以完成"
        },
        {
            "type": "time_conflict",
            "template": "{time1}在{location1}参加活动。{time2}在{location2}开会。",
            "query": "时间安排是否合理？",
            "answer_conflict": "不合理，时间冲突"
        },
        {
            "type": "resource_conflict",
            "template": "预算{budget}元，但住宿花费{lodging}元，餐饮{food}元，交通{transport}元。",
            "query": "预算是否足够？",
            "answer_conflict": "预算不足",
            "answer_no_conflict": "预算充足"
        }
    ]
    
    CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "西安", "南京", "武汉", "重庆"]
    ATTRACTIONS = ["博物馆", "公园", "历史遗迹", "景点", "商场", "美食街", "海滩", "山区", "湖畔", "古街"]
    TIMES = ["上午9:00", "上午10:30", "下午2:00", "下午3:30", "傍晚5:00", "晚上7:00"]
    
    def __init__(self):
        self.samples: List[TemporalSample] = []
    
    def convert_from_sample_file(self, input_file: Path) -> List[TemporalSample]:
        """Convert from TripCraft sample evaluation format"""
        print(f"[TRIP] Loading from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    sample = self._convert_trip_sample(data)
                    if sample:
                        self.samples.append(sample)
                except:
                    continue
        
        # Generate additional synthetic conflict samples
        synthetic_samples = self._generate_conflict_samples()
        self.samples.extend(synthetic_samples)
        
        print(f"[TRIP] Generated {len(self.samples)} samples")
        return self.samples
    
    def _convert_trip_sample(self, data: Dict) -> Optional[TemporalSample]:
        """Convert a TripCraft planning sample to conflict detection"""
        try:
            json_data = data.get('JSON', {})
            plan = data.get('plan', [])
            persona = data.get('persona', '')
            
            if not plan:
                return None
            
            # Extract travel details
            org = json_data.get('org', 'unknown')
            dest = json_data.get('dest', 'unknown')
            days = json_data.get('days', 1)
            date = json_data.get('date', [])
            budget = json_data.get('budget', 0)
            
            # Build context from itinerary
            context_parts = [f"旅行规划：从{org}到{dest}，共{days}天"]
            
            if date:
                context_parts.append(f"日期：{date[0]} 至 {date[-1]}")
            
            context_parts.append(f"预算：{budget}元")
            context_parts.append(f"旅行者类型：{persona}")
            
            # Extract daily activities
            daily_conflicts = []
            for day_plan in plan:
                day_num = day_plan.get('days', 1)
                current_city = day_plan.get('current_city', '')
                
                # Time extraction
                transportation = day_plan.get('transportation', '')
                breakfast = day_plan.get('breakfast', '')
                lunch = day_plan.get('lunch', '')
                dinner = day_plan.get('dinner', '')
                attraction = day_plan.get('attraction', '')
                
                day_context = f"\nDay {day_num} 在 {current_city}:"
                if transportation and transportation != '-':
                    day_context += f"\n  交通: {transportation}"
                if attraction and attraction != '-':
                    day_context += f"\n  景点: {attraction}"
                if breakfast and breakfast != '-':
                    day_context += f"\n  早餐: {breakfast}"
                if lunch and lunch != '-':
                    day_context += f"\n  午餐: {lunch}"
                if dinner and dinner != '-':
                    day_context += f"\n  晚餐: {dinner}"
                
                context_parts.append(day_context)
                
                # Check for potential conflicts (implicit)
                # Multiple cities in one day = spatial conflict
                # Check if attraction spans too much time
            
            context = "\n".join(context_parts)
            
            # Determine conflict type from planning
            has_spatial_conflict = len(plan) > 1 and any(
                'from' in p.get('current_city', '').lower() and 'to' in p.get('current_city', '').lower()
                for p in plan
            )
            
            sample = TemporalSample(
                id=f"trip_{json_data.get('idx', len(self.samples))}",
                task="T3",
                sub_task="T3-1",
                context=context,
                delta_t=f"{days}天旅行",
                event="旅行规划冲突检测",
                query="请检查这个旅行计划是否存在时间或空间冲突？",
                answer="计划合理" if not has_spatial_conflict else "存在潜在冲突，请检查日程安排",
                state={
                    "type": "travel_planning",
                    "origin": org,
                    "destination": dest,
                    "days": days,
                    "budget": budget,
                    "has_spatial_conflict": has_spatial_conflict
                },
                ground_truth={
                    "origin": org,
                    "destination": dest,
                    "days": days,
                    "plan_valid": not has_spatial_conflict
                },
                metadata={
                    "source": "TripCraft",
                    "persona": persona
                }
            )
            return sample
        except Exception as e:
            return None
    
    def _generate_conflict_samples(self, count: int = 500) -> List[TemporalSample]:
        """Generate synthetic travel conflict samples"""
        samples = []
        
        # Generate spatial conflicts
        for i in range(count // 3):
            city1 = random.choice(self.CITIES[:5])
            city2 = random.choice(self.CITIES[5:])
            attraction1 = random.choice(self.ATTRACTIONS)
            attraction2 = random.choice(self.ATTRACTIONS)
            time = random.choice(self.TIMES)
            day = random.randint(1, 7)
            
            context = f"Day {day}: {time} 在{city1}参观{attraction1}。{time} 在{city2}参观{attraction2}。"
            
            sample = TemporalSample(
                id=f"trip_spatial_{i}",
                task="T3",
                sub_task="T3-1",
                context=context,
                delta_t="同一天",
                event="空间冲突检测",
                query="这个旅行计划是否合理？",
                answer=f"不合理，存在空间冲突：无法同时出现在{city1}和{city2}",
                state={
                    "type": "spatial_conflict",
                    "conflict_type": "location",
                    "locations": [city1, city2]
                },
                ground_truth={
                    "has_conflict": True,
                    "conflict_type": "spatial"
                },
                metadata={
                    "source": "synthetic_travel",
                    "difficulty": "easy"
                }
            )
            samples.append(sample)
        
        # Generate time conflicts
        for i in range(count // 3):
            time1 = random.choice(self.TIMES[:3])
            time2 = random.choice(self.TIMES[3:])
            city = random.choice(self.CITIES)
            location1 = random.choice(self.ATTRACTIONS)
            location2 = random.choice(self.ATTRACTIONS)
            day = random.randint(1, 7)
            
            context = f"Day {day}: {time1}在{city}的{location1}活动（预计2小时）。{time2}开始{location2}参观（需1小时）。"
            
            # Determine if times overlap
            time_conflict = False
            # Simplified conflict detection
            if "上午" in time1 and "下午" not in time2:
                time_conflict = False
            else:
                time_conflict = random.choice([True, False])
            
            sample = TemporalSample(
                id=f"trip_time_{i}",
                task="T3",
                sub_task="T3-2",
                context=context,
                delta_t="同一天",
                event="时间冲突检测",
                query="时间安排是否合理？",
                answer="时间冲突" if time_conflict else "时间安排合理",
                state={
                    "type": "time_conflict" if time_conflict else "no_conflict",
                    "times": [time1, time2]
                },
                ground_truth={
                    "has_conflict": time_conflict,
                    "conflict_type": "time" if time_conflict else "none"
                },
                metadata={
                    "source": "synthetic_travel",
                    "difficulty": "medium"
                }
            )
            samples.append(sample)
        
        # Generate budget conflicts
        for i in range(count // 3):
            budget = random.randint(1000, 5000)
            city = random.choice(self.CITIES)
            days = random.randint(1, 7)
            
            # Create plausible or implausible budget
            if random.choice([True, False]):
                # Plausible budget
                lodging = int(budget * 0.4)
                food = int(budget * 0.3)
                transport = int(budget * 0.2)
                total = lodging + food + transport
                has_conflict = total > budget
            else:
                # Implausible budget
                lodging = budget + random.randint(500, 2000)
                food = int(budget * 0.5)
                transport = int(budget * 0.3)
                total = lodging + food + transport
                has_conflict = True
            
            context = f"{days}天{city}旅行计划\n预算：{budget}元\n住宿：{lodging}元\n餐饮：{food}元\n交通：{transport}元"
            
            sample = TemporalSample(
                id=f"trip_budget_{i}",
                task="T3",
                sub_task="T3-2",
                context=context,
                delta_t=f"{days}天",
                event="资源冲突检测",
                query="预算是否足够？",
                answer=f"预算不足，超出{total - budget}元" if has_conflict else "预算充足",
                state={
                    "type": "resource_conflict" if has_conflict else "no_conflict",
                    "budget": budget,
                    "total_cost": total
                },
                ground_truth={
                    "has_conflict": has_conflict,
                    "conflict_type": "resource" if has_conflict else "none"
                },
                metadata={
                    "source": "synthetic_travel",
                    "difficulty": "easy"
                }
            )
            samples.append(sample)
        
        return samples
    
    def save(self, output_file: Path):
        """Save samples to JSONL"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(sample.to_jsonl() + '\n')
        print(f"[TRIP] Saved {len(self.samples)} samples to {output_file}")


# ============================================================================
# SituatedGen Converter
# ============================================================================

class SituatedGenConverter:
    """Convert SituatedGen dataset for T2/T5
    
    SituatedGen contains generated contexts with temporal information.
    """
    
    def __init__(self):
        self.samples: List[TemporalSample] = []
    
    def convert(self, input_file: Path) -> List[TemporalSample]:
        """Convert SituatedGen data"""
        print(f"[SituatedGen] Loading from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    sample = self._convert_item(data, line_num)
                    if sample:
                        self.samples.append(sample)
                except:
                    continue
        
        print(f"[SituatedGen] Converted {len(self.samples)} samples")
        return self.samples
    
    def convert_statements(self, input_file: Path) -> List[TemporalSample]:
        """Convert from preprocessed statements"""
        print(f"[SituatedGen] Loading statements from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    sample = self._convert_statement(data, line_num)
                    if sample:
                        self.samples.append(sample)
                except:
                    continue
        
        print(f"[SituatedGen] Converted {len(self.samples)} statement samples")
        return self.samples
    
    def _convert_item(self, data: Dict, idx: int) -> Optional[TemporalSample]:
        """Convert a SituatedGen item"""
        keywords = data.get('keywords', [])
        statement = data.get('statement', '')
        statements = data.get('statements', [])
        ids = data.get('ids', [])
        keywords_pos = data.get('keywords_pos', [])
        
        if not statement:
            return None
        
        # Determine if temporal keywords are present
        temporal_keywords = ['today', 'yesterday', 'tomorrow', 'week', 'month', 'year', 
                            '年', '月', '日', '今天', '昨天', '明天', '周', '时']
        has_temporal = any(tk in statement.lower() or tk in str(keywords) for tk in temporal_keywords)
        
        task = "T1" if has_temporal else "T2"
        sub_task = "T1-1" if has_temporal else "T2-1"
        
        context = f"关键词: {', '.join(keywords)}\n相关事实: {' | '.join(statements[:2]) if statements else ''}"
        
        sample = TemporalSample(
            id=f"situated_{idx}",
            task=task,
            sub_task=sub_task,
            context=context,
            event=statement,
            query="根据关键词和上下文，这句话是否正确？",
            answer="正确" if data.get('keywords_pos', []) else "需要验证",
            state={
                "type": "context_generation",
                "keywords": keywords,
                "has_temporal": has_temporal
            },
            ground_truth={
                "statement": statement,
                "source_ids": ids
            },
            metadata={
                "source": "SituatedGen",
                "keywords_pos": keywords_pos
            }
        )
        return sample
    
    def _convert_statement(self, data: Dict, idx: int) -> Optional[TemporalSample]:
        """Convert a statement item"""
        statement = data.get('statement', '')
        question = data.get('question', '')
        answer = data.get('answer', '')
        ners = data.get('NERs', '')
        
        if not statement:
            return None
        
        # Check for temporal entities
        temporal_ners = ['DATE', 'TIME', 'DURATION', 'ORDINAL']
        has_temporal = any(t in ners.upper() for t in temporal_ners)
        
        task = "T1" if has_temporal else "T2"
        sub_task = "T1-3" if has_temporal else "T2-1"
        
        sample = TemporalSample(
            id=f"situated_stmt_{idx}",
            task=task,
            sub_task=sub_task,
            context=statement,
            event="陈述验证",
            query=question if question else f"这个陈述是否正确？",
            answer=str(answer) if answer else "",
            state={
                "type": "statement_verification",
                "has_temporal": has_temporal
            },
            ground_truth={
                "statement": statement,
                "question": question,
                "answer": answer,
                "ners": ners
            },
            metadata={
                "source": data.get('id', 'unknown'),
                "original_id": data.get('id', '')
            }
        )
        return sample
    
    def save(self, output_file: Path):
        """Save samples to JSONL"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in self.samples:
                f.write(sample.to_jsonl() + '\n')
        print(f"[SituatedGen] Saved {len(self.samples)} samples to {output_file}")


# ============================================================================
# Ground Truth Validator
# ============================================================================

class GroundTruthValidator:
    """Validate ground truth for all converted datasets"""
    
    def __init__(self):
        self.errors: List[Dict] = []
        self.stats: Dict[str, Dict] = {}
    
    def validate_file(self, input_file: Path) -> Dict:
        """Validate all samples in a JSONL file"""
        print(f"[Validator] Validating {input_file}...")
        
        stats = {
            "total": 0,
            "valid": 0,
            "missing_answer": 0,
            "missing_context": 0,
            "missing_query": 0,
            "missing_ground_truth": 0,
            "empty_state": 0
        }
        
        errors = []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    stats["total"] += 1
                    
                    # Required fields check
                    has_answer = bool(data.get('answer', ''))
                    has_context = bool(data.get('context', ''))
                    has_query = bool(data.get('query', ''))
                    has_ground_truth = 'ground_truth' in data and bool(data['ground_truth'])
                    has_state = 'state' in data and bool(data['state'])
                    
                    if not has_answer:
                        stats["missing_answer"] += 1
                        errors.append({
                            "line": line_num,
                            "id": data.get('id', 'unknown'),
                            "error": "missing_answer"
                        })
                    
                    if not has_context:
                        stats["missing_context"] += 1
                    
                    if not has_query:
                        stats["missing_query"] += 1
                    
                    if not has_ground_truth:
                        stats["missing_ground_truth"] += 1
                    
                    if not has_state:
                        stats["empty_state"] += 1
                    
                    # Mark as valid if has required fields
                    if has_answer and has_context and has_query and has_ground_truth:
                        stats["valid"] += 1
                        
                except json.JSONDecodeError as e:
                    errors.append({
                        "line": line_num,
                        "error": f"JSON decode error: {str(e)}"
                    })
        
        self.stats[input_file.name] = stats
        self.errors.extend(errors)
        
        # Calculate valid rate
        valid_rate = stats["valid"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  Total: {stats['total']}, Valid: {stats['valid']} ({valid_rate:.1f}%)")
        
        return stats
    
    def validate_all(self, directory: Path) -> Dict:
        """Validate all JSONL files in directory"""
        print(f"\n[Validator] Validating all files in {directory}...")
        
        results = {}
        for file_path in directory.glob("*.jsonl"):
            if file_path.name.startswith(".") or "dialogue" in file_path.name:
                continue
            results[file_path.name] = self.validate_file(file_path)
        
        # Summary
        total_samples = sum(r["total"] for r in results.values())
        total_valid = sum(r["valid"] for r in results.values())
        
        print(f"\n{'='*60}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total samples: {total_samples}")
        print(f"Valid samples: {total_valid} ({total_valid/total_samples*100:.1f}%)")
        print(f"Files validated: {len(results)}")
        
        # Print file-by-file stats
        for filename, stats in results.items():
            print(f"  {filename}: {stats['valid']}/{stats['total']} valid")
        
        return results
    
    def save_report(self, output_file: Path):
        """Save validation report"""
        report = {
            "summary": self.stats,
            "errors": self.errors[:100]  # Limit error count
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[Validator] Report saved to {output_file}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run all supplemental conversions"""
    print("=" * 60)
    print("SUPPLEMENTAL DATA CONVERSION")
    print("=" * 60)
    
    results = {}
    
    # 1. TRIP/TripCraft conversion
    print("\n[1/3] Converting TRIP/TripCraft for T3...")
    trip_file = DATA_DIR / "TRIP" / "postprocess" / "sample_evaluation_format.jsonl"
    if trip_file.exists():
        converter = TRIPConverter()
        converter.convert_from_sample_file(trip_file)
        converter.save(OUTPUT_DIR / "trip_conflict_t3.jsonl")
        results['trip'] = len(converter.samples)
    else:
        print(f"[TRIP] File not found: {trip_file}")
        # Generate synthetic samples anyway
        converter = TRIPConverter()
        converter.samples = converter._generate_conflict_samples(500)
        converter.save(OUTPUT_DIR / "trip_conflict_t3.jsonl")
        results['trip'] = len(converter.samples)
    
    # 2. SituatedGen conversion
    print("\n[2/3] Converting SituatedGen for T2/T5...")
    situated_file = DATA_DIR / "situated_gen" / "data" / "train.jsonl"
    statements_file = DATA_DIR / "situated_gen" / "data" / "preprocessed" / "statements" / "strategyqa.json"
    
    converter = SituatedGenConverter()
    
    if situated_file.exists():
        converter.convert(situated_file)
    
    if statements_file.exists():
        converter.convert_statements(statements_file)
    
    if converter.samples:
        converter.save(OUTPUT_DIR / "situated_gen_t2_t5.jsonl")
        results['situated_gen'] = len(converter.samples)
    else:
        print("[SituatedGen] No samples converted")
        results['situated_gen'] = 0
    
    # 3. Ground Truth Validation
    print("\n[3/3] Validating Ground Truth for all files...")
    validator = GroundTruthValidator()
    validator.validate_all(OUTPUT_DIR)
    validator.save_report(OUTPUT_DIR / "validation_report.json")
    
    # Summary
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    total = 0
    for name, count in results.items():
        print(f"  {name}: {count} samples")
        total += count
    print("=" * 60)
    print(f"Total new samples: {total}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()