# Benchmarking the Ability of Large Language Models to Reason about Event Sets: `BAMER`

`BAMER` serves as a benchmark for assessing the capability of Large Language Models (LLMs) to interpret temporal references within extensive event sets. It comprises over 2,200 questions designed to evaluate LLM performance through a Question Answering task. Users can select from four state-of-the-art LLMs within the benchmark and analyze their performance based on the length of the event set and the clarity of the temporal references involved. <br>
Check out our paper here: [BAMER](https://www.scitepress.org/PublicationsDetail.aspx?ID=lbTfx4I1bU0=&t=1)

## Extension:
The `BAMER` Benchmark was extended and contains now also the question category _Vague_. 
Check out the extension at the branch [Implicit Vague](https://gitlab.ub.uni-bielefeld.de/s.kenneweg/TRaVelER/-/tree/implicit_vague?ref_type=heads)!

## First steps:
1. Create a virtual python environment (if you want)
2. Install the requirements: `pip install -r requirements.txt`
3. Manually install en_core_web_sm: `python3 -m spacy download en_core_web_sm`
4. GPT-4: 
    - Get an openai account 
    - Set the API key (OPENAI_API_KEY) in your environment variables
5. Llama3 or Gemma: 
    - GPU needed 
    - Create huggingface account 
    - Add meta-llama/Meta-Llama-3-70B-Instruct to your huggingface account
    - Add meta-llama/Meta-Llama-3-8B-Instruct to your huggingface account
    - Add google/gemma-7b-it to your huggingface account
    - Create token https://huggingface.co/settings/tokens
    - "huggingface-cli login" via terminal


## Run the Code: 
1. In the root directory: `python3 src/runAll.py` -> opens a GUI


### GUI

- **Parameter Selection**: Enter with which Parameters the selected options out of 'Code to Run' should be executed
  - Question Categories: referential ('referential relative to speech time' questions), explicit ('temporally explicit' questions)
  - Length Event Sets: 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100 (Number of events in the event set)
  - Models: gpt-4-0125-preview, Meta-Llama-3-8B-Instruct, Meta-Llama-3-70B-Instruct, gemma-7b-it (Large Language Models)
  - Use Prompt Engineering: If you want to perform Prompt Engineering
    - Results are then saved under results_promptEngineering 
    - When Evaluate is selected results_promptEngineering is evaluated
    - Prompt Engineering Methods Appear when you select 'Yes'
  - Prompt Engineering Methods: Date-Extended, Language, CoT_Review/CoT_Step-by-Step, Default
    - Default is the zero-shot baseline prompt: Json, Date-Only and Zero-Shot
    - If you want to use the final prompt enter: CoT_Review, Language

- **Code to Run**: Toggle options for:
  - Create new Events and Questions based on them: If you want to create a new Dataset with explicit and referential questions or not
  - Benchmark LLMs: Benchmark the LLMs from the Parameter Selection on the selected Length of Event Sets and Question Categories
  - Evaluated the Benchmarked LLMs: Evaluate the LLMs from the Parameter Selection on the selected Length of Event Sets and Question Categories. The results are saved in the results folder

- **Run Script Button**: Execute the code from the 'Code to Run' section with the provided parameters.




[//]: # ()
[//]: # (Problems:)

[//]: # (- huggingface model no disk space/loads very slow: in ~/.cache: rm -r huggingface/)