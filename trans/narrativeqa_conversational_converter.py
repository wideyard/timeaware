#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NarrativeQA Conversational Temporal Data Converter

Converts NarrativeQA (ConTEB version) dataset to conversational temporal format.
Primary focus: T2 (State Update), T4 (Long-term Memory)
Secondary: T1 (Time Calculation), T5 (Counterfactual)

Output: converted_data_v3/narrativeqa_conversational.jsonl
"""

import json
import random
import re
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict

# =====================================================================
# Data Structures
# =====================================================================

@dataclass
class ConversationalSample:
    task: str  # T1, T2, T4, T5
    sub_task: str  # e.g., "T2-Convo-State", "T4-Convo-Buried"
    context: str  # Original chunk (truncated)
    conversation: List[Dict[str, str]]
    query: str
    answer: str
    state_info: Optional[Dict[str, Any]] = None
    ground_truth: Optional[Dict[str, Any]] = None
    difficulty: str = "medium"
    source_id: Optional[str] = None

# =====================================================================
# Helper Functions
# =====================================================================

# Time expressions for narrative state tracking
TIME_EXPRESSIONS = {
    "day": ["by day", "during the day", "in the daytime", "every morning", "each day"],
    "night": ["by night", "at night", "in the evening", "after dark", "every night"],
    "past": ["yesterday", "earlier", "previously", "before", "in the past"],
    "future": ["tomorrow", "later", "next", "in the future", "soon"],
    "sequence": ["then", "after that", "subsequently", "next", "afterward"]
}

# State transition keywords
STATE_KEYWORDS = {
    "location": ["goes to", "arrives at", "leaves", "enters", "exits", "travels to", "moves to"],
    "status": ["becomes", "transforms into", "changes to", "evolves to", "turns into"],
    "emotion": ["feels", "is happy", "is sad", "is angry", "fears", "loves", "hates"],
    "action": ["starts", "begins", "stops", "ends", "continues", "resumes"]
}

# Noise questions for distraction
NOISE_QUESTIONS = [
    "By the way, what's the weather like?",
    "I heard about a new restaurant downtown.",
    "The traffic was terrible this morning.",
    "My neighbor has a new dog.",
    "I forgot to water the plants.",
    "What's for dinner tonight?",
    "Did you see the game last night?",
    "The movie reviews were mixed.",
    "I need to buy groceries later.",
    "Have you tried that new coffee shop?"
]

def extract_characters(text: str) -> List[str]:
    """Extract character names from text (simple heuristic)."""
    # Find capitalized words that appear multiple times
    words = re.findall(r'\b([A-Z][a-z]+)\b', text)
    # Count occurrences
    from collections import Counter
    char_counts = Counter(words)
    # Return characters mentioned at least twice
    return [char for char, count in char_counts.items() if count >= 2 and len(char) > 2]

def extract_events(text: str) -> List[str]:
    """Extract key events from narrative text."""
    # Split by sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)
    events = []
    for s in sentences:
        s = s.strip()
        # Filter for action-oriented sentences
        if any(kw in s.lower() for kw in ['starts', 'begins', 'goes', 'arrives', 'meets', 'finds', 'discovers', 'decides', 'becomes']):
            events.append(s)
    return events[:5]  # Return top 5 events

def get_chunk_position(chunk_id: str) -> Tuple[str, int]:
    """Extract doc_id and chunk position from chunk_id."""
    parts = chunk_id.rsplit('_', 1)
    if len(parts) == 2:
        return parts[0], int(parts[1])
    return chunk_id, 0

def truncate_text(text: str, max_len: int = 300) -> str:
    """Truncate text to max length, preserving word boundaries."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(' ', 1)[0] + '...'

# =====================================================================
# T2: State Update Converter
# =====================================================================

class T2Converter:
    """Convert NarrativeQA data to T2 conversational format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_state_update_sample(self, chunk: str, chunk_id: str, 
                                     query: str, answer: str,
                                     source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-State: Track character state through narrative."""
        characters = extract_characters(chunk)
        if not characters:
            return None
        
        main_char = characters[0]
        events = extract_events(chunk)
        
        # Check for time-based state transitions
        time_state = None
        for time_key, expressions in TIME_EXPRESSIONS.items():
            for expr in expressions:
                if expr in chunk.lower():
                    time_state = time_key
                    break
            if time_state:
                break
        
        # Create conversation
        conversation = []
        
        # Round 1: Present initial state
        initial_text = truncate_text(chunk, 200)
        conversation.append({
            "role": "user",
            "content": f"I'm reading a story. Here's a part: {initial_text}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Got it, this is about {main_char}. Let me know if you have questions about them."
        })
        
        # Round 2: Add distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I don't have information about that in this story."
        })
        
        # Round 3: Ask about state
        if time_state:
            if time_state == "day":
                query_text = f"What does {main_char} do during the day?"
            elif time_state == "night":
                query_text = f"What does {main_char} do at night?"
            else:
                query_text = f"What is {main_char}'s current state in this story?"
        else:
            query_text = f"What is {main_char} doing or experiencing in this part of the story?"
        
        conversation.append({
            "role": "user",
            "content": query_text
        })
        
        # Generate answer from chunk
        state_answer = self.extract_state_answer(chunk, main_char, time_state)
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-State",
            context=truncate_text(chunk, 300),
            conversation=conversation,
            query=query_text,
            answer=state_answer,
            state_info={
                "type": "narrative_state",
                "main_character": main_char,
                "time_context": time_state,
                "events": events[:3] if events else []
            },
            ground_truth={
                "character": main_char,
                "time_state": time_state,
                "original_answer": answer[:100] if answer else ""
            },
            difficulty="medium",
            source_id=f"narrativeqa_t2_state_{source_id}"
        )
    
    def create_progressive_sample(self, chunks: List[Dict], source_id: str) -> Optional[ConversationalSample]:
        """T2-Convo-Progressive: Track state progression across chunks."""
        if len(chunks) < 2:
            return None
        
        # Get characters from first chunk
        first_chunk = chunks[0]
        characters = extract_characters(first_chunk['chunk'])
        if not characters:
            return None
        
        main_char = characters[0]
        
        conversation = []
        
        # Round 1: First chunk event
        events_1 = extract_events(first_chunk['chunk'])
        if events_1:
            event_text = truncate_text(events_1[0], 150)
        else:
            event_text = truncate_text(first_chunk['chunk'], 150)
        
        conversation.append({
            "role": "user",
            "content": f"In this story, {main_char} begins with: {event_text}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"I understand. {main_char} is in the initial state of this narrative."
        })
        
        # Round 2-3: More chunks with distraction
        for i, chunk_data in enumerate(chunks[1:3], 1):
            events = extract_events(chunk_data['chunk'])
            if events:
                event_text = truncate_text(events[0], 100)
            else:
                event_text = truncate_text(chunk_data['chunk'], 100)
            
            conversation.append({
                "role": "user",
                "content": f"Then {event_text}"
            })
            
            conversation.append({
                "role": "assistant",
                "content": f"Continuing the story. {main_char}'s situation is evolving."
            })
        
        # Add distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me focus on the story."
        })
        
        # Query about current state
        conversation.append({
            "role": "user",
            "content": f"Based on these events, what is {main_char}'s current situation?"
        })
        
        # Extract final state
        last_chunk = chunks[-1]
        final_events = extract_events(last_chunk['chunk'])
        final_state = final_events[-1] if final_events else truncate_text(last_chunk['chunk'], 100)
        
        return ConversationalSample(
            task="T2",
            sub_task="T2-Convo-Progressive",
            context=truncate_text(first_chunk['chunk'], 200),
            conversation=conversation,
            query=f"Based on these events, what is {main_char}'s current situation?",
            answer=final_state,
            state_info={
                "type": "progressive_state",
                "main_character": main_char,
                "chunk_count": len(chunks),
                "events_per_chunk": [len(extract_events(c['chunk'])) for c in chunks[:3]]
            },
            ground_truth={
                "final_state": final_state,
                "chunk_ids": [c['chunk_id'] for c in chunks[:3]]
            },
            difficulty="hard",
            source_id=f"narrativeqa_t2_prog_{source_id}"
        )
    
    def extract_state_answer(self, chunk: str, character: str, time_state: str) -> str:
        """Extract character state from chunk."""
        # Find sentences about the character
        sentences = re.split(r'[.!?]+', chunk)
        relevant = []
        
        for s in sentences:
            if character in s:
                s = s.strip()
                # Check for state keywords
                for kw_type, keywords in STATE_KEYWORDS.items():
                    if any(kw in s.lower() for kw in keywords):
                        relevant.append(s.strip())
                        break
        
        if relevant:
            return relevant[0]
        
        # Fallback: return first sentence with character
        for s in sentences:
            if character in s:
                return s.strip()
        
        return f"{character} is present in the narrative."

# =====================================================================
# T4: Long-term Memory Converter
# =====================================================================

class T4Converter:
    """Convert NarrativeQA data to T4 conversational format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_buried_info_sample(self, chunk: str, query: str, answer: str,
                                   chunk_id: str, source_id: str) -> Optional[ConversationalSample]:
        """T4-Convo-Buried: Bury key information in long narrative."""
        # Extract key facts
        key_facts = self.extract_key_facts(chunk)
        if not key_facts:
            return None
        
        key_fact = random.choice(key_facts)
        key_question = self.generate_question_from_fact(key_fact)
        
        conversation = []
        
        # Round 1: Embed key information
        conversation.append({
            "role": "user",
            "content": f"Here's a story detail: {truncate_text(chunk, 150)}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I've noted this story information."
        })
        
        # Round 2-5: Add noise chunks
        for _ in range(random.randint(2, 4)):
            conversation.append({
                "role": "user",
                "content": random.choice(NOISE_QUESTIONS)
            })
            
            conversation.append({
                "role": "assistant",
                "content": "Noted, but let's focus on the story."
            })
        
        # Final query about buried info
        conversation.append({
            "role": "user",
            "content": key_question
        })
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Buried",
            context=truncate_text(chunk, 200),
            conversation=conversation,
            query=key_question,
            answer=key_fact,
            state_info={
                "type": "buried_fact",
                "key_fact": key_fact,
                "noise_rounds": 3
            },
            ground_truth={
                "fact": key_fact,
                "chunk_id": chunk_id
            },
            difficulty="hard",
            source_id=f"narrativeqa_t4_buried_{source_id}"
        )
    
    def create_cross_chunk_sample(self, chunks: List[Dict], query: str, answer: str,
                                    source_id: str) -> Optional[ConversationalSample]:
        """T4-Convo-Cross: Retrieve info across multiple chunks."""
        if len(chunks) < 2:
            return None
        
        conversation = []
        
        # Place key info in early chunk
        first_chunk = chunks[0]
        key_fact = self.extract_key_facts(first_chunk['chunk'])[0] if self.extract_key_facts(first_chunk['chunk']) else truncate_text(first_chunk['chunk'], 50)
        
        conversation.append({
            "role": "user",
            "content": f"Story part 1: {truncate_text(first_chunk['chunk'], 150)}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I've stored this story segment."
        })
        
        # Insert noise chunks in between
        for i, chunk_data in enumerate(chunks[1:3], 2):
            noise_or_content = random.choice([True, False])
            if noise_or_content:
                conversation.append({
                    "role": "user",
                    "content": random.choice(NOISE_QUESTIONS)
                })
            else:
                conversation.append({
                    "role": "user",
                    "content": f"Story part {i}: {truncate_text(chunk_data['chunk'], 100)}"
                })
            
            conversation.append({
                "role": "assistant",
                "content": "Continuing to track the narrative."
            })
        
        # Query about early information
        key_question = self.generate_question_from_fact(key_fact)
        conversation.append({
            "role": "user",
            "content": f"From the first story part: {key_question}"
        })
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Cross",
            context=truncate_text(first_chunk['chunk'], 200),
            conversation=conversation,
            query=key_question,
            answer=key_fact,
            state_info={
                "type": "cross_chunk",
                "key_chunk": 0,
                "noise_chunks": len(chunks) - 1
            },
            ground_truth={
                "answer_location": "first_chunk",
                "original_query": query
            },
            difficulty="very_hard",
            source_id=f"narrativeqa_t4_cross_{source_id}"
        )
    
    def create_detail_recall_sample(self, chunk: str, query: str, answer: str,
                                     source_id: str) -> Optional[ConversationalSample]:
        """T4-Convo-Detail: Recall specific narrative details."""
        conversation = []
        
        # Present context
        conversation.append({
            "role": "user",
            "content": f"Here's a story excerpt: {truncate_text(chunk, 400)}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I've read this story excerpt. What would you like to know?"
        })
        
        # Add distraction
        for _ in range(2):
            conversation.append({
                "role": "user",
                "content": random.choice(NOISE_QUESTIONS)
            })
            
            conversation.append({
                "role": "assistant",
                "content": "I don't have information about that. Let's focus on the story."
            })
        
        # Query about details
        detail_question = self.generate_detail_question(chunk)
        conversation.append({
            "role": "user",
            "content": detail_question
        })
        
        # Extract detail answer
        detail_answer = self.extract_detail_answer(chunk, detail_question)
        
        return ConversationalSample(
            task="T4",
            sub_task="T4-Convo-Detail",
            context=truncate_text(chunk, 200),
            conversation=conversation,
            query=detail_question,
            answer=detail_answer,
            state_info={
                "type": "detail_recall",
                "chunk_length": len(chunk)
            },
            ground_truth={
                "original_query": query,
                "original_answer": answer
            },
            difficulty="medium",
            source_id=f"narrativeqa_t4_detail_{source_id}"
        )
    
    def extract_key_facts(self, chunk: str) -> List[str]:
        """Extract key facts from narrative chunk."""
        sentences = re.split(r'[.!?]+', chunk)
        facts = []
        
        for s in sentences:
            s = s.strip()
            # Look for factual statements (not questions, short phrases)
            if len(s) > 20 and len(s) < 200 and not s.endswith('?'):
                # Check for key information indicators
                if any(kw in s.lower() for kw in ['is', 'are', 'was', 'were', 'has', 'have', 'had']):
                    facts.append(s)
        
        return facts[:3]  # Return top 3 facts
    
    def generate_question_from_fact(self, fact: str) -> str:
        """Generate a question about a fact."""
        # Simple extraction: ask about subjects
        match = re.match(r'([A-Z][a-z]+)', fact)
        if match:
            subject = match.group(1)
            return f"What do we know about {subject} in this story?"
        return "What is a key fact from this story?"
    
    def extract_detail_answer(self, chunk: str, question: str) -> str:
        """Extract answer detail from chunk."""
        # Look for specific details
        sentences = re.split(r'[.!?]+', chunk)
        for s in sentences:
            s = s.strip()
            if len(s) > 30 and len(s) < 150:
                # Return first substantive sentence
                if any(kw in s.lower() for kw in ['is', 'are', 'was', 'called', 'named']):
                    return s
        return truncate_text(chunk, 100)
    
    def generate_detail_question(self, chunk: str) -> str:
        """Generate a detail-oriented question."""
        # Look for specific entities
        characters = extract_characters(chunk)
        if characters:
            return f"What is an important detail about {characters[0]} in this story?"
        
        # Generic fallback
        return "What is an important detail from this story?"

# =====================================================================
# T1: Time Calculation Converter
# =====================================================================

class T1Converter:
    """Convert NarrativeQA data to T1 time calculation format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_ordering_sample(self, chunks: List[Dict], source_id: str) -> Optional[ConversationalSample]:
        """T1-Convo-Ordering: Order narrative events by time."""
        if len(chunks) < 3:
            return None
        
        conversation = []
        
        # Present chunks in random order
        shuffled_indices = list(range(len(chunks)))
        random.shuffle(shuffled_indices)
        
        # Present each chunk
        presented_chunks = []
        for i in shuffled_indices[:3]:
            chunk_data = chunks[i]
            chunk_text = truncate_text(chunk_data['chunk'], 100)
            presented_chunks.append((i, chunk_text))
            
            conversation.append({
                "role": "user",
                "content": f"Story fragment {i+1}: {chunk_text}"
            })
            
            conversation.append({
                "role": "assistant",
                "content": f"Noted story fragment {i+1}."
            })
        
        # Add distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let's focus on ordering these story fragments."
        })
        
        # Query about ordering
        conversation.append({
            "role": "user",
            "content": "In what chronological order do these story fragments occur?"
        })
        
        # Correct order
        correct_order = sorted([(i, i) for i in range(len(chunks[:3]))], key=lambda x: x[0])
        order_answer = ", ".join([f"Fragment {i+1}" for i in range(len(chunks[:3]))])
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Ordering",
            context=truncate_text(chunks[0]['chunk'], 200),
            conversation=conversation,
            query="In what chronological order do these story fragments occur?",
            answer=order_answer,
            state_info={
                "type": "event_ordering",
                "shuffled_order": [i for i, _ in presented_chunks],
                "correct_order": list(range(len(chunks[:3])))
            },
            ground_truth={
                "correct_sequence": [c['chunk_id'] for c in chunks[:3]]
            },
            difficulty="medium",
            source_id=f"narrativeqa_t1_order_{source_id}"
        )
    
    def create_duration_sample(self, chunk: str, source_id: str) -> Optional[ConversationalSample]:
        """T1-Convo-Duration: Calculate narrative duration."""
        # Look for time expressions
        time_keywords = ['days', 'weeks', 'months', 'years', 'hours', 'minutes']
        found_times = []
        
        for kw in time_keywords:
            pattern = rf'(\d+)\s+{kw}'
            matches = re.findall(pattern, chunk.lower())
            found_times.extend(matches)
        
        if not found_times:
            return None
        
        # Create conversation
        conversation = []
        
        conversation.append({
            "role": "user",
            "content": f"Story context: {truncate_text(chunk, 200)}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": "I've noted the story timeline."
        })
        
        # Add calculation question
        conversation.append({
            "role": "user",
            "content": "How much time does this narrative cover in total?"
        })
        
        # Parse duration from context
        duration_text = self.parse_duration(chunk)
        
        return ConversationalSample(
            task="T1",
            sub_task="T1-Convo-Duration",
            context=truncate_text(chunk, 200),
            conversation=conversation,
            query="How much time does this narrative cover in total?",
            answer=duration_text,
            state_info={
                "type": "narrative_duration",
                "time_expressions": found_times[:3]
            },
            ground_truth={
                "duration_text": duration_text
            },
            difficulty="easy",
            source_id=f"narrativeqa_t1_dur_{source_id}"
        )
    
    def parse_duration(self, chunk: str) -> str:
        """Parse narrative duration from text."""
        # Simple heuristic: look for explicit time expressions
        time_patterns = [
            (r'(\d+)\s+days?', 'days'),
            (r'(\d+)\s+weeks?', 'weeks'),
            (r'(\d+)\s+months?', 'months'),
            (r'(\d+)\s+years?', 'years'),
            (r'(\d+)\s+hours?', 'hours'),
        ]
        
        for pattern, unit in time_patterns:
            match = re.search(pattern, chunk.lower())
            if match:
                return f"The narrative spans {match.group(0)}."
        
        return "The narrative duration is not explicitly stated."

# =====================================================================
# T5: Counterfactual Converter
# =====================================================================

class T5Converter:
    """Convert NarrativeQA data to T5 counterfactual format."""
    
    def __init__(self):
        self.sample_count = 0
    
    def create_plot_twist_sample(self, chunk: str, query: str, answer: str,
                                   source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-Twist: Modify plot and ask about consequences."""
        characters = extract_characters(chunk)
        if not characters:
            return None
        
        main_char = characters[0]
        events = extract_events(chunk)
        
        conversation = []
        
        # Round 1: Present original context
        conversation.append({
            "role": "user",
            "content": f"In the original story: {truncate_text(chunk, 200)}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"I understand the original story about {main_char}."
        })
        
        # Round 2: Introduce counterfactual
        counterfactual = self.generate_counterfactual(chunk, main_char, events)
        
        conversation.append({
            "role": "user",
            "content": f"But in THIS version: {counterfactual}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"Understood. In this altered version, {counterfactual[:50]}..."
        })
        
        # Round 3: Add distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Let me stay focused on the altered story."
        })
        
        # Query about consequences
        cf_question = self.generate_cf_question(main_char, events)
        conversation.append({
            "role": "user",
            "content": cf_question
        })
        
        # Generate counterfactual answer
        cf_answer = self.generate_cf_answer(chunk, counterfactual, main_char)
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Twist",
            context=truncate_text(chunk, 200),
            conversation=conversation,
            query=cf_question,
            answer=cf_answer,
            state_info={
                "type": "plot_twist",
                "original_plot": events[0] if events else "",
                "counterfactual": counterfactual,
                "main_character": main_char
            },
            ground_truth={
                "original_answer": answer[:100] if answer else "",
                "counterfactual_rule": counterfactual
            },
            difficulty="hard",
            source_id=f"narrativeqa_t5_twist_{source_id}"
        )
    
    def create_character_fate_sample(self, chunk: str, query: str, answer: str,
                                       source_id: str) -> Optional[ConversationalSample]:
        """T5-Convo-Fate: Change character's fate and ask for outcome."""
        characters = extract_characters(chunk)
        if not characters:
            return None
        
        main_char = characters[0]
        
        conversation = []
        
        # Round 1: Original context
        conversation.append({
            "role": "user",
            "content": f"Original story about {main_char}: {truncate_text(chunk, 200)}"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"I've learned about {main_char}'s original story."
        })
        
        # Round 2: Introduce changed fate
        fate_change = f"Imagine {main_char} makes a completely different choice."
        
        conversation.append({
            "role": "user",
            "content": f"{fate_change} What if {main_char} had acted differently at the crucial moment?"
        })
        
        conversation.append({
            "role": "assistant",
            "content": f"I'll consider how {main_char}'s alternative choice affects the story."
        })
        
        # Round 3: Distraction
        conversation.append({
            "role": "user",
            "content": random.choice(NOISE_QUESTIONS)
        })
        
        conversation.append({
            "role": "assistant",
            "content": "Staying focused on the hypothetical scenario."
        })
        
        # Query
        conversation.append({
            "role": "user",
            "content": f"In this altered version, what would be {main_char}'s outcome?"
        })
        
        # Generate alternative outcome
        alt_outcome = f"In the altered story, {main_char}'s outcome would be different based on the hypothetical choice."
        
        return ConversationalSample(
            task="T5",
            sub_task="T5-Convo-Fate",
            context=truncate_text(chunk, 200),
            conversation=conversation,
            query=f"In this altered version, what would be {main_char}'s outcome?",
            answer=alt_outcome,
            state_info={
                "type": "character_fate",
                "main_character": main_char,
                "fate_change": fate_change
            },
            ground_truth={
                "original_fate": answer[:100] if answer else "",
                "character": main_char
            },
            difficulty="very_hard",
            source_id=f"narrativeqa_t5_fate_{source_id}"
        )
    
    def generate_counterfactual(self, chunk: str, character: str, events: List[str]) -> str:
        """Generate a counterfactual twist."""
        counterfactuals = [
            f"{character} makes the opposite choice",
            f"the events unfold in reverse order",
            f"{character} encounters an unexpected ally",
            f"the ending is completely different",
            f"{character} discovers a hidden truth earlier",
        ]
        return random.choice(counterfactuals)
    
    def generate_cf_question(self, character: str, events: List[str]) -> str:
        """Generate question about counterfactual outcome."""
        questions = [
            f"How does {character}'s different choice affect the outcome?",
            f"What happens to {character} in this altered version?",
            f"In this alternative version, what is {character}'s fate?",
        ]
        return random.choice(questions)
    
    def generate_cf_answer(self, chunk: str, counterfactual: str, character: str) -> str:
        """Generate answer for counterfactual scenario."""
        # Generic answer based on counterfactual
        return f"In this altered version, {character}'s story unfolds differently due to {counterfactual.lower()}. The outcome would diverge from the original narrative."

# =====================================================================
# Main Converter
# =====================================================================

class NarrativeQAConversationalConverter:
    """Main converter for NarrativeQA to conversational temporal format."""
    
    def __init__(self, data_dir: str = "data/narrative-qa"):
        self.data_dir = Path(data_dir)
        self.t2_converter = T2Converter()
        self.t4_converter = T4Converter()
        self.t1_converter = T1Converter()
        self.t5_converter = T5Converter()
        
        # Load data
        self.chunks = {}
        self.queries = []
        self.documents = defaultdict(list)  # Group by doc_id
    
    def load_data(self, max_queries: int = None):
        """Load chunks and queries from JSONL files."""
        # Load chunks
        chunks_file = self.data_dir / "chunks.jsonl"
        if chunks_file.exists():
            with open(chunks_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    chunk_id = data['chunk_id']
                    self.chunks[chunk_id] = data['chunk']
                    # Group by document
                    doc_id, _ = get_chunk_position(chunk_id)
                    self.documents[doc_id].append({
                        'chunk_id': chunk_id,
                        'chunk': data['chunk']
                    })
        
        # Load queries
        queries_file = self.data_dir / "queries.jsonl"
        if queries_file.exists():
            with open(queries_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if max_queries and i >= max_queries:
                        break
                    data = json.loads(line.strip())
                    self.queries.append(data)
        
        print(f"Loaded {len(self.chunks)} chunks, {len(self.documents)} documents, {len(self.queries)} queries")
    
    def convert_sample(self, query_data: Dict, query_id: int) -> List[ConversationalSample]:
        """Convert a single query to multiple conversational samples."""
        results = []
        
        chunk_id = query_data.get('chunk_id', '')
        query = query_data.get('query', '')
        og_query = query_data.get('og_query', '')
        answer = query_data.get('answer', '')
        
        # Get chunk
        chunk = self.chunks.get(chunk_id, '')
        if not chunk:
            return results
        
        source_id = f"{chunk_id}_{query_id}"
        
        # T2: State Update
        sample_t2_state = self.t2_converter.create_state_update_sample(
            chunk, chunk_id, query, answer, source_id
        )
        if sample_t2_state:
            results.append(sample_t2_state)
        
        # T4: Long-term Memory
        sample_t4_buried = self.t4_converter.create_buried_info_sample(
            chunk, query, answer, chunk_id, source_id
        )
        if sample_t4_buried:
            results.append(sample_t4_buried)
        
        sample_t4_detail = self.t4_converter.create_detail_recall_sample(
            chunk, query, answer, source_id
        )
        if sample_t4_detail:
            results.append(sample_t4_detail)
        
        # T5: Counterfactual
        if random.random() < 0.3:  # 30% chance for T5
            sample_t5_twist = self.t5_converter.create_plot_twist_sample(
                chunk, query, answer, source_id
            )
            if sample_t5_twist:
                results.append(sample_t5_twist)
        
        return results
    
    def convert_document_samples(self, doc_id: str) -> List[ConversationalSample]:
        """Convert document-level samples (cross-chunk)."""
        results = []
        
        chunks = self.documents.get(doc_id, [])
        if len(chunks) < 2:
            return results
        
        # Sort by chunk position
        chunks = sorted(chunks, key=lambda x: get_chunk_position(x['chunk_id'])[1])
        
        source_id = doc_id[:20]  # Truncate long IDs
        
        # T2: Progressive state tracking
        sample_t2_prog = self.t2_converter.create_progressive_sample(
            chunks[:3], source_id
        )
        if sample_t2_prog:
            results.append(sample_t2_prog)
        
        # T4: Cross-chunk retrieval
        sample_t4_cross = self.t4_converter.create_cross_chunk_sample(
            chunks[:4], "", "", source_id
        )
        if sample_t4_cross:
            results.append(sample_t4_cross)
        
        # T1: Event ordering
        sample_t1_order = self.t1_converter.create_ordering_sample(
            chunks[:3], source_id
        )
        if sample_t1_order:
            results.append(sample_t1_order)
        
        return results
    
    def convert_all(self, output_file: str, max_samples: int = None):
        """Convert all data to conversational format."""
        all_samples = []
        
        # Convert queries
        print("Converting queries...")
        for i, query_data in enumerate(self.queries):
            if max_samples and len(all_samples) >= max_samples:
                break
            converted = self.convert_sample(query_data, i)
            all_samples.extend(converted)
            
            if i % 1000 == 0:
                print(f"  Processed {i} queries, generated {len(all_samples)} samples")
        
        # Convert document-level (cross-chunk) samples
        print("Converting document-level samples...")
        for doc_id in list(self.documents.keys())[:100]:  # Limit to 100 documents
            converted = self.convert_document_samples(doc_id)
            all_samples.extend(converted)
        
        # Save to output
        print(f"\nTotal converted: {len(all_samples)} samples")
        
        # Write JSONL
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in all_samples:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        
        print(f"Saved to: {output_path}")
        
        # Print statistics
        self.print_statistics(all_samples)
        
        return all_samples
    
    def print_statistics(self, samples: List[ConversationalSample]):
        """Print conversion statistics."""
        print("\n" + "=" * 60)
        print("Conversion Summary")
        print("=" * 60)
        
        # Task distribution
        task_counts = {}
        for s in samples:
            task_counts[s.task] = task_counts.get(s.task, 0) + 1
        
        print(f"\nTotal samples: {len(samples)}")
        print("\nTask distribution:")
        for task, count in sorted(task_counts.items()):
            print(f"  {task}: {count}")
        
        # Subtask distribution
        subtask_counts = {}
        for s in samples:
            subtask_counts[s.sub_task] = subtask_counts.get(s.sub_task, 0) + 1
        
        print("\nSubtask distribution:")
        for subtask, count in sorted(subtask_counts.items()):
            print(f"  {subtask}: {count}")
        
        # Difficulty distribution
        diff_counts = {}
        for s in samples:
            diff_counts[s.difficulty] = diff_counts.get(s.difficulty, 0) + 1
        
        print("\nDifficulty distribution:")
        for diff, count in sorted(diff_counts.items()):
            print(f"  {diff}: {count}")

# =====================================================================
# Main Entry
# =====================================================================

def main():
    print("=" * 60)
    print("NarrativeQA Conversational Temporal Data Converter")
    print("=" * 60)
    
    converter = NarrativeQAConversationalConverter()
    converter.load_data(max_queries=5000)  # Limit queries for processing time
    
    output_file = "converted_data_v3/narrativeqa_conversational.jsonl"
    converter.convert_all(output_file, max_samples=10000)

if __name__ == "__main__":
    main()