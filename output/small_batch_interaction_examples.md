## Example Cases

### A. Strictly Correct Cases
1. model=gpt-4o-mini, sub_task=T1-Counting, interaction=single
   - gold: 31 minutes
   - prediction: 31 minutes

2. model=gpt-4o-mini, sub_task=T2-Status, interaction=single
   - gold: Already happened (past tense verbs: said, saw)
   - prediction: Already happened

3. model=gpt-4o-mini, sub_task=T3-SpaceConflict, interaction=single
   - gold: Yes, there's a time overlap.
   - prediction: yes

4. model=gpt-4o-mini, sub_task=T4-NoiseRetrieval, interaction=multiturn_clean
   - gold: 2:30 PM
   - prediction: 2:30 PM

### B. Partial-Correct Cases
1. model=gpt-4o-mini, sub_task=T2-Status, interaction=single
   - gold: Still in progress. The next logical step is: rubs his eye with his fingers.
   - prediction: It is still in progress.
   - partial_reason: status_only_without_next_step

2. model=gpt-4o-mini, sub_task=T4-NoiseRetrieval, interaction=single
   - gold: He might thought it was funny .
   - prediction: He might be shocked.
   - partial_reason: token_overlap

3. model=doubao-seed-1-8, sub_task=T3-SpaceConflict, interaction=multiturn_clean
   - gold: Yes, there's a potential conflict. The the webbing is currently knitted together, but you're trying to use it in a different location. You may need to retrieve or move it first.
   - prediction: Yes, there is an issue—you intend to use webbing that's in a different location, while the webbing you currently have is already knitted together, so you may not be able to access the appropriate webbing for your plan.
   - partial_reason: token_overlap

### C. Incorrect Cases
1. model=gpt-4o-mini, sub_task=T1-Counting, interaction=single
   - gold: The answer is the first six months. Note: 'the first 25 days' is a distractor - it's just a number from the context, not the logical answer. 'the first 15 months' is also a distractor - a number from context.
   - prediction: volume sales

2. model=gpt-4o-mini, sub_task=T2-Status, interaction=single
   - gold: Currently in progress: throws the pink item on a game board on the floor.
   - prediction: You are currently speaking in an office while holding a pink item.

3. model=gpt-4o-mini, sub_task=T3-SpaceConflict, interaction=multiturn_clean
   - gold: Yes, there's a time overlap.
   - prediction: no

4. model=gpt-4o-mini, sub_task=T4-NoiseRetrieval, interaction=multiturn_clean
   - gold: He might thought it was funny .
   - prediction: How might my manager react when he finds out the truth?
