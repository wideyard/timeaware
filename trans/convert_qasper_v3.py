#!/usr/bin/env python3
"""
QASPER Dataset Conversion Script for Time-Aware Benchmark

Converts QASPER dataset to conversational format following the analysis in qasper.md.

Task Mapping:
- T4 (Long-term Memory): Main focus - long document comprehension with buried information
- Noise injection for memory decay testing
"""

import json
import os
import random
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

def load_qasper_data(filepath: str) -> Dict:
    """Load QASPER JSON data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def generate_id(paper_id: str, question_id: str, task: str, sub_task: str) -> str:
    """Generate unique ID for each converted item."""
    hash_input = f"{paper_id}_{question_id}_{task}_{sub_task}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:10]
    return f"qasper_{task.lower()}_{hash_val}"

def extract_answer(answer_data: Dict) -> Tuple[str, str]:
    """Extract answer and type from answer data."""
    if answer_data.get('unanswerable', False):
        return ('unanswerable', 'unanswerable')
    
    if answer_data.get('extractive_spans'):
        spans = answer_data['extractive_spans']
        if isinstance(spans, list) and len(spans) > 0:
            return ('extractive', ' '.join(spans[:2]))  # Take first 2 spans max
    
    if answer_data.get('free_form_answer'):
        return ('abstractive', answer_data['free_form_answer'])
    
    if answer_data.get('yes_no') is not None:
        return ('boolean', 'Yes' if answer_data['yes_no'] else 'No')
    
    return ('unknown', 'unknown')

def extract_evidence(answer_data: Dict) -> List[str]:
    """Extract evidence from answer data."""
    evidence = answer_data.get('evidence', [])
    if evidence and isinstance(evidence, list):
        # Filter out FLOAT SELECTED (figure/table evidence) for text-only
        text_evidence = [e for e in evidence if not e.startswith('FLOAT SELECTED')]
        return text_evidence[:3]  # Take first 3 evidence pieces
    return []

# Noise texts for T4 memory decay testing
NOISE_CHAT_MESSAGES = [
    "对了，我今天下午要去喝咖啡。",
    "今天天气真不错。",
    "我最近在学习做新菜。",
    "周末我打算去看电影。",
    "昨天我买了一件新衣服。",
    "我刚刚吃完午饭。",
    "明天有个会议。",
    "我最近在追一部新剧。",
    "我家的猫今天特别调皮。",
    "最近工作比较忙。",
    "我打算下周去爬山。",
    "我刚刚收到一个快递。",
    "最近睡眠不太好。",
    "我正在听一首新歌。",
    "我想明天去跑步。",
    "对了，我明天要早起。",
    "我的电脑最近有点慢。",
    "最近在看一本新书。",
    "我刚刚喝了杯奶茶。",
    "对了，我下周有个考试。",
]

# Section names that typically contain key information
KEY_SECTIONS = ['introduction', 'conclusion', 'abstract', 'method', 'results', 'discussion']

def convert_t4_long_document(paper_data: Dict, paper_id: str) -> List[Dict]:
    """Convert QASPER paper to T4 long-term memory task."""
    results = []
    
    title = paper_data.get('title', '')
    abstract = paper_data.get('abstract', '')
    full_text = paper_data.get('full_text', [])
    figures_and_tables = paper_data.get('figures_and_tables', [])
    qas = paper_data.get('qas', [])
    
    if not full_text or not qas:
        return results
    
    # Build section summaries
    sections = []
    for section in full_text:
        section_name = section.get('section_name', 'Unknown')
        paragraphs = section.get('paragraphs', [])
        if paragraphs:
            # Combine paragraphs, limit length
            combined_text = ' '.join([p for p in paragraphs if p])
            sections.append({
                'name': section_name,
                'text': combined_text[:2000] if len(combined_text) > 2000 else combined_text,
                'length': len(combined_text)
            })
    
    if len(sections) < 2:
        return results
    
    # For each question, create a T4 task
    for qa in qas:
        question_id = qa.get('question_id', '')
        question = qa.get('question', '')
        
        if not question:
            continue
        
        # Get answers
        answers = qa.get('answers', [])
        if not answers:
            continue
        
        for answer_data in answers:
            answer_type, answer_text = extract_answer(answer_data.get('answer', {}))
            
            if answer_type == 'unanswerable' or answer_type == 'unknown':
                continue
            
            evidence = extract_evidence(answer_data.get('answer', {}))
            
            # Create buried information task
            result = create_buried_info_task(
                paper_id=paper_id,
                question_id=question_id,
                title=title,
                abstract=abstract,
                sections=sections,
                figures_and_tables=figures_and_tables,
                question=question,
                answer_text=answer_text,
                answer_type=answer_type,
                evidence=evidence
            )
            if result:
                results.append(result)
            
            # Create noise retrieval task
            noise_result = create_noise_retrieval_task(
                paper_id=paper_id,
                question_id=question_id,
                title=title,
                abstract=abstract,
                sections=sections,
                question=question,
                answer_text=answer_text,
                answer_type=answer_type,
                evidence=evidence
            )
            if noise_result:
                results.append(noise_result)
    
    return results

def create_buried_info_task(
    paper_id: str, question_id: str, title: str, abstract: str,
    sections: List[Dict], figures_and_tables: List[Dict],
    question: str, answer_text: str, answer_type: str,
    evidence: List[str]
) -> Optional[Dict]:
    """Create T4 task with information buried in early conversation."""
    conversation = []
    
    # 1. Start with buried key information
    conversation.append({
        "role": "user",
        "content": f"我最近在看一篇论文，标题是《{title[:100]}》。"
    })
    
    # 2. Add abstract with key details marked
    if abstract:
        conversation.append({
            "role": "user",
            "content": f"摘要是：{abstract[:500]}..." if len(abstract) > 500 else f"摘要是：{abstract}"
        })
    
    conversation.append({
        "role": "assistant",
        "content": "好的，我记住了这篇论文的基本信息。"
    })
    
    # 3. Add sections incrementally with noise
    noise_positions = random.sample(range(len(sections)), min(2, len(sections)))
    
    for i, section in enumerate(sections):
        # Add section content
        conversation.append({
            "role": "user",
            "content": f"这一部分是{section['name']}：{section['text'][:800]}"
        })
        
        # Add noise at random positions
        if i in noise_positions:
            conversation.append({
                "role": "user",
                "content": random.choice(NOISE_CHAT_MESSAGES)
            })
            conversation.append({
                "role": "assistant",
                "content": "好的，继续说论文吧。"
            })
        
        conversation.append({
            "role": "assistant",
            "content": f"已收到{section['name']}部分。"
        })
    
    # 4. Add figures/tables if available
    if figures_and_tables:
        fig_text = figures_and_tables[0].get('caption', '')[:300] if figures_and_tables else ''
        if fig_text:
            conversation.append({
                "role": "user",
                "content": f"论文还有图表：{fig_text}"
            })
            conversation.append({
                "role": "assistant",
                "content": "了解了。"
            })
    
    # 5. Ask about buriedinformation
    # Find which section contains the answer
    evidence_section = None
    if evidence:
        for sec in sections:
            for ev in evidence:
                if ev and ev[:50] in sec['text']:
                    evidence_section = sec['name']
                    break
    
    conversation.append({
        "role": "user",
        "content": f"回到刚才的论文，{question}"
    })
    
    # Build context (short summary)
    context = f"Paper: {title[:100]}"
    if evidence:
        context += f" | Evidence: {evidence[0][:100]}..." if len(evidence[0]) >100 else f" | Evidence: {evidence[0]}"
    
    return {
        "task": "T4",
        "sub_task": "T4-Buried-Info",
        "context": context,
        "conversation": conversation,
        "query": question,
        "answer": answer_text,
        "state_info": {
            "type": "buried_paper_info",
            "answer_type": answer_type,
            "paper_id": paper_id,
            "evidence_section": evidence_section,
            "num_sections": len(sections),
            "num_turns": len(conversation)
        },
        "ground_truth": {
            "answer": answer_text,
            "answer_type": answer_type,
            "evidence": evidence,
            "question_id": question_id,
            "paper_id": paper_id
        },
        "difficulty": "hard"if len(conversation) >10 else "medium",
        "source_id": generate_id(paper_id, question_id, "T4", "Buried")
    }

def create_noise_retrieval_task(
    paper_id: str, question_id: str, title: str, abstract: str,
    sections: List[Dict], question: str, answer_text: str,
    answer_type: str, evidence: List[str]
) -> Optional[Dict]:
    """Create T4 task with heavy noise injection."""
    conversation = []
    
    # Start with paper info
    conversation.append({
        "role": "user",
        "content": f"论文标题是：{title[:80]}"
    })
    
    # Add intensive noise
    noise_count = random.randint(3, 5)
    inserted_noise = []
    
    for i in range(noise_count):
        noise_msg = NOISE_CHAT_MESSAGES[i % len(NOISE_CHAT_MESSAGES)]
        conversation.append({
            "role": "user",
            "content": noise_msg
        })
        inserted_noise.append(noise_msg)
        
        if i < noise_count - 1:
            conversation.append({
                "role": "assistant",
                "content": random.choice(["好的。", "嗯。", "明白。", "收到。"])
            })
    
    # Add key paper content in between noise
    key_info = f"摘要：{abstract[:300]}" if abstract else ""
    if key_info:
        conversation.append({
            "role": "user",
            "content": key_info
        })
    
    # More noise
    conversation.append({
        "role": "user",
        "content": random.choice(NOISE_CHAT_MESSAGES)
    })
    
    # Final question
    conversation.append({
        "role": "assistant",
        "content": "请问你有什么问题？"
    })
    conversation.append({
        "role": "user",
        "content": question
    })
    
    context = f"Paper: {title[:80]} | Noise: {noise_count} messages"
    
    return {
        "task": "T4",
        "sub_task": "T4-Noise-Retrieval",
        "context": context,
        "conversation": conversation,
        "query": question,
        "answer": answer_text,
        "state_info": {
            "type": "noise_retrieval",
            "answer_type": answer_type,
            "paper_id": paper_id,
            "noise_count": noise_count,
            "num_turns": len(conversation)
        },
        "ground_truth": {
            "answer": answer_text,
            "answer_type": answer_type,
            "evidence": evidence,
            "question_id": question_id,
            "paper_id": paper_id
        },
        "difficulty": "very_hard",
        "source_id": generate_id(paper_id, question_id, "T4", "Noise")
    }

def convert_t4_section_navigation(paper_data: Dict, paper_id: str) -> List[Dict]:
    """Create T4 task asking about specific section content after long context."""
    results = []
    
    title = paper_data.get('title', '')
    abstract = paper_data.get('abstract', '')
    full_text = paper_data.get('full_text', [])
    qas = paper_data.get('qas', [])
    
    if not full_text or not qas:
        return results
    
    # Build sections
    sections = []
    for section in full_text:
        section_name = section.get('section_name', 'Unknown')
        paragraphs = section.get('paragraphs', [])
        if paragraphs:
            combined_text = ' '.join([p for p in paragraphs if p])
            sections.append({
                'name': section_name,
                'text': combined_text
            })
    
    if len(sections) < 3:
        return results
    
    # Create tasks for questions with evidence in specific sections
    for qa in qas:
        question_id = qa.get('question_id', '')
        question = qa.get('question', '')
        answers = qa.get('answers', [])
        
        if not question or not answers:
            continue
        
        for answer_data in answers:
            answer_type, answer_text = extract_answer(answer_data.get('answer', {}))
            
            if answer_type == 'unanswerable' or answer_type == 'unknown':
                continue
            
            evidence = extract_evidence(answer_data.get('answer', {}))
            
            # Find which section contains the evidence
            evidence_section_idx = None
            if evidence:
                for idx, sec in enumerate(sections):
                    for ev in evidence:
                        if ev and ev[:30] in sec['text']:
                            evidence_section_idx = idx
                            break
                    if evidence_section_idx is not None:
                        break
            
            # Only create task if evidence is in middle or late section
            if evidence_section_idx is None or evidence_section_idx <len(sections) // 2:
                continue
            
            # Create conversationwith all sections before asking
            conversation = []
            
            conversation.append({
                "role": "user",
                "content": f"论文标题：《{title[:60]}》"
            })
            
            # Add all sections
            for sec in sections:
                conversation.append({
                    "role": "user",
                    "content": f"{sec['name']}：{sec['text'][:500]}"
                })
                conversation.append({
                    "role": "assistant",
                    "content": f"已阅读{sec['name']}部分。"
                })
            
            # Ask the question
            conversation.append({
                "role": "user",
                "content": question
            })
            
            context = f"Paper: {title[:60]} | Sections: {len(sections)}"
            
            result = {
                "task": "T4",
                "sub_task": "T4-Section-Nav",
                "context": context,
                "conversation": conversation,
                "query": question,
                "answer": answer_text,
                "state_info": {
                    "type": "section_navigation",
                    "answer_type": answer_type,
                    "paper_id": paper_id,
                    "evidence_section_idx": evidence_section_idx,
                    "total_sections": len(sections)
                },
                "ground_truth": {
                    "answer": answer_text,
                    "answer_type": answer_type,
                    "evidence": evidence,
                    "question_id": question_id,
                    "paper_id": paper_id
                },
                "difficulty": "hard",
                "source_id": generate_id(paper_id, question_id, "T4", "Section")
            }
            results.append(result)
            break# Only one result per question
    
    return results

def convert_qasper_to_conversational(input_file: str, output_file: str, split: str):
    """Main conversion function for QASPER."""
    print(f"Loading {input_file}...")
    data = load_qasper_data(input_file)
    print(f"Loaded {len(data)} papers")
    
    converted_data = []
    stats = defaultdict(int)
    
    for paper_id, paper_data in data.items():
        # T4: Buried information
        t4_buried = convert_t4_long_document(paper_data, paper_id)
        for item in t4_buried:
            if item['sub_task'] == 'T4-Buried-Info':
                stats['T4-Buried'] += 1
            else:
                stats['T4-Noise'] += 1
        converted_data.extend(t4_buried)
        
        # T4: Section navigation
        t4_section = convert_t4_section_navigation(paper_data, paper_id)
        converted_data.extend(t4_section)
        stats['T4-Section'] += len(t4_section)
    
    # Write output
    print(f"Writing {len(converted_data)} converted items...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in converted_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Write stats
    stats_file = output_file.replace('.jsonl', '_report.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        report = {
            "source": "QASPER",
            "split": split,
            "total_items": len(converted_data),
            "total_papers": len(data),
            "statistics": dict(stats),
            "task_distribution": {"T4": sum(stats.values())}
        }
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"Conversion complete. Stats: {dict(stats)}")
    return stats

def main():
    # Set random seed for reproducibility
    random.seed(42)
    
    #Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data", "qasper")
    output_dir = os.path.join(base_dir, "converted_data_v3")
    
    # Convert train set
    train_input = os.path.join(data_dir, "qasper-train-v0.3.json")
    train_output = os.path.join(output_dir, "qasper_conversational.jsonl")
    print("\n=== Converting TRAIN set ===")
    if os.path.exists(train_input):
        convert_qasper_to_conversational(train_input, train_output, "train")
    else:
        print(f"File not found: {train_input}")
    
    # Convert dev set
    dev_input = os.path.join(data_dir, "qasper-dev-v0.3.json")
    dev_output = os.path.join(output_dir, "qasper_dev_conversational.jsonl")
    print("\n=== Converting DEV set ===")
    if os.path.exists(dev_input):
        convert_qasper_to_conversational(dev_input, dev_output, "dev")
    else:
        print(f"File not found: {dev_input}")
    
    # Convert test set
    test_input = os.path.join(data_dir, "qasper-test-v0.3.json")
    test_output = os.path.join(output_dir, "qasper_test_conversational.jsonl")
    print("\n=== Converting TEST set ===")
    if os.path.exists(test_input):
        convert_qasper_to_conversational(test_input, test_output, "test")
    else:
        print(f"File not found: {test_input}")
    
    print("\n=== Conversion Complete ===")

if __name__ == "__main__":
    main()