"""Consolidate all _report.json files into a unified T1-T5 subtask inventory."""
import json
import os
from collections import defaultdict

DATA_DIR = r"D:\workspace\timeaware\converted_data_v3"

# Load all reports
reports = {}
for f in sorted(os.listdir(DATA_DIR)):
    if f.endswith('_report.json'):
        with open(os.path.join(DATA_DIR, f), 'r') as fh:
            reports[f] = json.load(fh)

# Aggregate subtasks by dimension
# Structure: {dimension: {subtask: {source: count}}}
dim_subtask_sources = defaultdict(lambda: defaultdict(dict))
dim_subtask_total = defaultdict(lambda: defaultdict(int))

for report_name, report in reports.items():
    # Some reports use 'statistics' instead of 'subtask_distribution'
    subtask_dist = report.get('subtask_distribution', report.get('statistics', {}))
    for subtask, count in subtask_dist.items():
        # Determine dimension from subtask prefix
        dim = subtask.split('-')[0]  # T1, T2, T3, T4, T5
        dim_subtask_sources[dim][subtask][report_name] = count
        dim_subtask_total[dim][subtask] += count

# Print full inventory
print("=" * 100)
print("COMPLETE T1-T5 SUBTASK INVENTORY (ALL DATASETS)")
print("=" * 100)

for dim in ['T1', 'T2', 'T3', 'T4', 'T5']:
    print(f"\n{'='*100}")
    print(f"  {dim}")
    print(f"{'='*100}")
    
    subtasks = sorted(dim_subtask_sources[dim].items(), key=lambda x: -dim_subtask_total[dim][x[0]])
    for subtask, sources in subtasks:
        total = dim_subtask_total[dim][subtask]
        print(f"\n  [{subtask}]  TOTAL: {total:,}")
        for src, cnt in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"    {src:60s} {cnt:>8,}")

# Identify redundant/mergeable subtasks
print("\n\n" + "=" * 100)
print("REDUNDANCY ANALYSIS & MERGE RECOMMENDATIONS")
print("=" * 100)

merge_groups = {
    'T1': {
        'Ordering': ['T1-Convo-Ordering', 'T1-Ordering-MC', 'T1-Ordering-Direct'],
        'Duration': ['T1-Convo-Duration', 'T1-Duration-Compare', 'T1-TimeCalc-HistNoise', 'T1-TimeCalc-ConfusionNoise', 'T1-TimeCalc-NumNoise', 'T1-TimeCalc', 'T1-TypicalTime', 'T1-TimeNoise'],
        'MultiChoice': ['T1-Convo-MultiChoice', 'T1-Convo-Calc'],
        'Distractor': ['T1-Convo-Distractor'],
        'Sequence': ['T1-Convo-Sequence'],
        'Causal': ['T1-Convo-Causal'],
        'Addition': ['T1-Convo-Addition'],
        'TimeBoundary': ['T1-TimeBoundary-Reasoning'],
        'Multihop': ['T1-Convo-Multihop'],
    },
    'T2': {
        'State': ['T2-Convo-State', 'T2-StateTrack-Easy', 'T2-StateTrack-Hard', 'T2-StateTimeline-Easy', 'T2-StateTimeline-Hard', 'T2-SocialState', 'T2-CFState', 'T2-PhysicalState', 'T2-CausalState'],
        'Progressive': ['T2-Convo-Progressive', 'T2-Sequence'],
        'Rollback': ['T2-Convo-Rollback'],
        'Branch': ['T2-Convo-Branch'],
        'PositionTrack': ['T2-PositionTrack-Basic', 'T2-PositionTrack-Timeline', 'T2-PositionTrack-WithContext', 'T2-PositionTrack-MC'],
        'Transition': ['T2-Transition', 'T2-BeforeAfter', 'T2-TransitionWithContext', 'T2-TransitionMC'],
        'Social': ['T2-SocialState', 'T2-Transition', 'T2-CFState'],
        'Evidence': ['T2-Convo-Evidence'],
        'Tense': ['T2-Convo-Tense', 'T2-Convo-Timeline'],
        'Location': ['T2-Location', 'T2-StateTrack', 'T2-Convo-Location'],
        'Ordering': ['T2-Ordering'],
        'Stationarity': ['T2-Stationarity'],
        'Consequence': ['T2-Convo-Consequence'],
        'Commonsense': ['T2-CommonsenseReasoning'],
    },
    'T3': {
        'Conflict': ['T3-Convo-Conflict', 'T3-Conflict'],
        'TimeConflict': ['T3-Convo-TimeConflict'],
        'TimeOverlap': ['T3-Convo-TimeOverlap'],
        'Resource': ['T3-Convo-Resource'],
        'Location': ['T3-Convo-Location'],
        'Concurrent': ['T3-ConcurrentDetect'],
    },
    'T4': {
        'Buried': ['T4-Convo-Buried', 'T4-Buried', 'T4-BuriedInfo-Easy', 'T4-BuriedInfo-Hard', 'T4-Memory'],
        'Noise': ['T4-Convo-Noisy', 'T4-Noisy', 'T4-Noise', 'T4-NoiseRetrieval-Hard'],
        'Section': ['T4-Convo-Section', 'T4-Section', 'T4-SectionNav-Easy', 'T4-SectionNav-Hard'],
        'Detail': ['T4-Convo-Detail'],
        'Distractor': ['T4-Convo-Distractor'],
        'Cross': ['T4-Convo-Cross'],
        'Dialog': ['T4-Convo-Dialog'],
        'Recall': ['T4-Convo-Recall'],
    },
    'T5': {
        'Counterfactual': ['T5-Convo-Counterfactual', 'T5-Counterfactual'],
        'RuleChange': ['T5-Convo-RuleChange', 'T5-RuleChange', 'T5-RuleMutation', 'T5-EntityMutation'],
        'RuleReverse': ['T5-Convo-RuleReverse', 'T5-Convo-Rule', 'T5-RulePerturbation'],
        'Reversal': ['T5-Convo-Reversal', 'T5-Convo-RuleReversal', 'T5-RuleReversal'],
        'WorldInversion': ['T5-WorldInversion'],
        'ReversedPremise': ['T5-ReversedPremise'],
        'ChoiceInversion': ['T5-Convo-ChoiceInversion'],
        'WrongToRight': ['T5-Convo-WrongToRight'],
        'Twist': ['T5-Convo-Twist'],
        'Emotion': ['T5-Convo-Emotion'],
        'SocialReverse': ['T5-SocialReverse'],
        'Explicit': ['T5-Explicit'],
        'Contrastive': ['T5-Convo-Contrastive'],
        'Alter': ['T5-Alter'],
        'Confusion': ['T5-Convo-Confusion'],
        'Duration-CF': ['T5-Duration-CF', 'T5-Stationarity-CF'],
    },
}

for dim in ['T1', 'T2', 'T3', 'T4', 'T5']:
    print(f"\n{'='*60}")
    print(f"  {dim} - Merge Groups")
    print(f"{'='*60}")
    
    for group_name, members in merge_groups[dim].items():
        # Check which members actually exist
        existing = [m for m in members if m in dim_subtask_total[dim]]
        if not existing:
            continue
        
        total = sum(dim_subtask_total[dim][m] for m in existing)
        print(f"\n  [{group_name}]  Combined total: {total:,}")
        for m in existing:
            cnt = dim_subtask_total[dim][m]
            print(f"    {m:50s} {cnt:>8,}")

# Summary statistics
print("\n\n" + "=" * 100)
print("DIMENSION SUMMARY")
print("=" * 100)

for dim in ['T1', 'T2', 'T3', 'T4', 'T5']:
    total = sum(dim_subtask_total[dim].values())
    n_subtasks = len(dim_subtask_total[dim])
    print(f"  {dim}: {total:>12,} samples across {n_subtasks:>3} unique subtasks")
