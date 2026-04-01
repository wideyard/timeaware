"""
Subtask configuration for the Timeaware Benchmark Experiment.

Defines all subtasks to be tested, their sampling counts, context-giving rules,
and noise injection strategies.

Each subtask entry contains:
- atomic_tasks: list of original sub_task names to sample from
- sample_count: number of samples to draw (or 'all' if < sample_count)
- context_mode: 'required' | 'optional' | 'forbidden'
    - required: context contains essential info (biography, paper text) → give in single-turn
    - optional: context is meta-description → give in single-turn (harmless)
    - forbidden: context IS the answer → don't give in single-turn
- has_noise_version: whether this subtask already has built-in noise variants
- noise_injectable: whether to inject noise for the noise experiment
"""

SUBTASK_CONFIG = {
    # ==================== T1: Time Calculation ====================
    "T1-Ordering": {
        "dimension": "T1",
        "atomic_tasks": ["T1-Convo-Ordering", "T1-Ordering-MC", "T1-Ordering-Direct"],
        "sample_count": 10,
        "context_mode": "required",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-Duration": {
        "dimension": "T1",
        "atomic_tasks": ["T1-Convo-Duration", "T1-Duration-Compare", "T1-TimeCalc", "T1-TimeNoise"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-TimeBoundary": {
        "dimension": "T1",
        "atomic_tasks": ["T1-TimeBoundary-Reasoning"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-MultiChoice": {
        "dimension": "T1",
        "atomic_tasks": ["T1-Convo-MultiChoice", "T1-Convo-Calc"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-Distractor": {
        "dimension": "T1",
        "atomic_tasks": ["T1-Convo-Distractor"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-Sequence": {
        "dimension": "T1",
        "atomic_tasks": ["T1-Convo-Sequence"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-Addition": {
        "dimension": "T1",
        "atomic_tasks": ["T1-Convo-Addition"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-Multihop": {
        "dimension": "T1",
        "atomic_tasks": ["T1-Convo-Multihop"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-Causal": {
        "dimension": "T1",
        "atomic_tasks": ["T1-Convo-Causal"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-Parallel": {
        "dimension": "T1",
        "atomic_tasks": ["T1-Convo-Parallel"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T1-HistNoise": {
        "dimension": "T1",
        "atomic_tasks": ["T1-TimeCalc-HistNoise"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": True,
        "noise_injectable": False,
    },
    "T1-ConfusionNoise": {
        "dimension": "T1",
        "atomic_tasks": ["T1-TimeCalc-ConfusionNoise"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": True,
        "noise_injectable": False,
    },
    "T1-NumNoise": {
        "dimension": "T1",
        "atomic_tasks": ["T1-TimeCalc-NumNoise"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": True,
        "noise_injectable": False,
    },

    # ==================== T2: State Tracking ====================
    "T2-StateTrack": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Convo-State", "T2-StateTrack-Easy", "T2-StateTrack-Hard",
                         "T2-StateTimeline-Easy", "T2-StateTimeline-Hard"],
        "sample_count": 10,
        "context_mode": "required",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-SocialState": {
        "dimension": "T2",
        "atomic_tasks": ["T2-SocialState", "T2-CFState"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Transition": {
        "dimension": "T2",
        "atomic_tasks": ["T2-StateTransition-BeforeAfter", "T2-StateTransition-WithContext", "T2-StateTransition-MC"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Basic": {
        "dimension": "T2",
        "atomic_tasks": ["T2-PositionTrack-Basic", "T2-PositionTrack-Timeline", "T2-PositionTrack-WithContext", "T2-PositionTrack-MC"],
        "sample_count": 10,
        "context_mode": "required",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Progressive": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Convo-Progressive"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Evidence": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Convo-Evidence"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Commonsense": {
        "dimension": "T2",
        "atomic_tasks": ["T2-CommonsenseReasoning"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Tense": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Convo-Tense", "T2-Convo-Timeline"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Location": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Location", "T2-StateTrack", "T2-PhysicalState", "T2-CausalState"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Consequence": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Convo-Consequence"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Rollback": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Convo-Rollback"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Branch": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Convo-Branch"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Ordering": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Ordering"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T2-Stationarity": {
        "dimension": "T2",
        "atomic_tasks": ["T2-Stationarity"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },

    # ==================== T3: Conflict Resolution ====================
    "T3-Concurrent": {
        "dimension": "T3",
        "atomic_tasks": ["T3-ConcurrentDetect"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T3-Conflict": {
        "dimension": "T3",
        "atomic_tasks": ["T3-Convo-Conflict"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T3-TimeConflict": {
        "dimension": "T3",
        "atomic_tasks": ["T3-Convo-TimeConflict"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T3-TimeOverlap": {
        "dimension": "T3",
        "atomic_tasks": ["T3-Convo-TimeOverlap"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T3-Resource": {
        "dimension": "T3",
        "atomic_tasks": ["T3-Convo-Resource"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },

    # ==================== T4: Long-term Memory ====================
    "T4-Buried": {
        "dimension": "T4",
        "atomic_tasks": ["T4-Convo-Buried", "T4-Buried-Info", "T4-BuriedInfo-Easy", "T4-BuriedInfo-Hard", "T4-Buried-Time"],
        "sample_count": 10,
        "context_mode": "required",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T4-Noise": {
        "dimension": "T4",
        "atomic_tasks": ["T4-Convo-Noisy", "T4-Noise-Retrieval", "T4-NoiseRetrieval-Hard", "T4-Noisy-Retrieval"],
        "sample_count": 10,
        "context_mode": "required",
        "has_noise_version": True,
        "noise_injectable": False,
    },
    "T4-Section": {
        "dimension": "T4",
        "atomic_tasks": ["T4-SectionNav-Easy", "T4-SectionNav-Hard"],
        "sample_count": 10,
        "context_mode": "required",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T4-Detail": {
        "dimension": "T4",
        "atomic_tasks": ["T4-Convo-Detail"],
        "sample_count": 10,
        "context_mode": "required",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T4-Distractor": {
        "dimension": "T4",
        "atomic_tasks": ["T4-Convo-Distractor"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },

    # ==================== T5: Counterfactual Reasoning ====================
    "T5-RulePerturbation": {
        "dimension": "T5",
        "atomic_tasks": ["T5-RulePerturbation", "T5-ReversedPremise", "T5-WorldInversion"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-Counterfactual": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Convo-Counterfactual"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-SocialReverse": {
        "dimension": "T5",
        "atomic_tasks": ["T5-SocialReverse"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-RuleChange": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Convo-RuleChange", "T5-RuleMutation", "T5-EntityMutation"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-RuleReversal": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Convo-RuleReversal"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-WrongToRight": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Convo-WrongToRight"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-Rule": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Convo-Rule"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-Confusion": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Convo-Confusion"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-ChoiceInversion": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Convo-ChoiceInversion"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-Twist": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Convo-Twist"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-Emotion": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Convo-Emotion"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
    "T5-ProcessReverse": {
        "dimension": "T5",
        "atomic_tasks": ["T5-Process-Reverse"],
        "sample_count": 10,
        "context_mode": "optional",
        "has_noise_version": False,
        "noise_injectable": True,
    },
}


# Models to test
EVAL_MODELS = ["gpt-4o-mini", "doubao-seed-1-8", "doubao-seed-2-0-pro"]

# Conversation modes
CONV_MODES = ["single_turn", "multi_turn", "multi_turn_noise"]

# Noise types for injection
NOISE_TYPES = ["hist_noise", "confusion_noise", "num_noise"]

# Data directory
DATA_DIR = "converted_data_v3"

# Output directory
OUTPUT_DIR = "experiment/output"

# LLM-as-judge model (use a strong model for evaluation)
JUDGE_MODEL = "gpt-4o-mini"

# Temperature for LLM calls
LLM_TEMPERATURE = 0.0  # deterministic for evaluation

# Max retries for API calls
MAX_RETRIES = 3

# Delay between API calls (seconds) to avoid rate limiting
API_DELAY = 0.5
