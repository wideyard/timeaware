# Choice-75: A Dataset on Decision Branching in Script Learning
- [Link to paper](https://aclanthology.org/2024.lrec-main.285/)

## Data
- Location: `/data/final_dataset/`
- Format:
    - Script
        - `goal` (str): goal of the script
        - `steps` (list\[str\]): list of steps
        - `original_index` (int): original index in ProScript
        - `index` (int): randomized index 
        - `branching_info` (dict): information about branching
            - `branching_idx` (int): index of the branching step
            - `branching_step` (str): content of the branching step
            - `option 1`, `option 2` (str): options for the branching
            - `op1_ra`, `op2_ra` (list\[int\]): list of rationales for the branches
            - `typr` (str): type of this branching, could be `golden`, `silver_dev`
            - `dataset`: dataset, could be `train`, `dev`, `test`
