import os
from datetime import datetime

from models.chatgpt_baseline import GPTRunner
from models.googlellms_baseline import GoogleLLMRunner
from models.llama_baseline import LlamaRunner
from models.prompt_and_json import LoadAndSaveJson, PromptPreparation

class LLMRunner:
    """
       A class for running various language models to generate text completions based on given questions from the dataset.
    """
    def __init__(self, today_timestamp, question_types, num_events,
                 model_names=["gpt-4-0125-preview"],
                 temperature=0,
                 prompt_engineering_methods=["CoT_Review", "Language"],
                 prompt_engineering=False):
        """
        Initializes the LLMRunner with the specified parameters for model execution.

        Args:
            today_timestamp (str): The current date and time.
            question_types (list): Question Categories (temporally explicit, referential to speech time).
            num_events (list): Event sets to benchmark.
            model_names (list): List of LLMs to benchmark.
            temperature (float): Temperature for the LLMs.
            prompt_engineering_methods (list): Prompt Engineering Methods to benchmark.
            prompt_engineering (bool): Flag to enable or disable prompt engineering.
        """
        self.today_timestamp = today_timestamp
        self.question_types = question_types
        self.num_events = num_events
        self.model_names = model_names
        self.temperature = temperature
        self.prompt_engineering_methods = prompt_engineering_methods
        self.prompt_engineering = prompt_engineering

    def generate_completions(self):
        """
        Generates text completions for specified question types using the selected models.

        This method iterates through the configured models, loads events, prepares prompts, and
        generates responses for each question. The results are saved in specified JSON files.
        """
        for model_name in self.model_names:
            # Instantiate the appropriate model runner based on the model name
            if model_name == "gpt-4-0125-preview":
                model_class = GPTRunner(model_name=model_name, temperature=self.temperature)
            elif "gemma" in model_name:
                model_class = GoogleLLMRunner(model_name=model_name, temperature=self.temperature)
            elif "Llama" in model_name:
                model_class = LlamaRunner(model_name=model_name, temperature=self.temperature)
            else:
                print("Model not found")
                return

            # Iterate through each question category and event set
            for question_type in self.question_types:
                for num_event in self.num_events:
                    text_to_save = []
                    events = LoadAndSaveJson('events/100Events.json').content
                    prompt_class = PromptPreparation(self.today_timestamp, events, num_event, self.prompt_engineering_methods)

                    if not self.prompt_engineering:
                        answer_file = LoadAndSaveJson(
                            f'results/{question_type}/{model_name}/{num_event}Events.json')
                    else:
                        result_string = "_".join(self.prompt_engineering_methods)
                        answer_file = LoadAndSaveJson(
                            f'results_promptEngineering/{question_type}/{model_name}/{result_string}/{num_event}Events.json')

                    questions = LoadAndSaveJson(
                        f'dataset/{question_type}/{num_event}Events.json').content

                    questions_count = 0
                    for question in questions:
                        questions_count += 1

                        # Extract components from the question for prompt generation
                        action_prompt, restriction, today_restriction, formatted_question = prompt_class.get_prompt_components(question["text"])
                        # Generate a response from the model
                        response, prompt_text = model_class.get_completion(action_prompt, restriction, today_restriction, formatted_question)
                        print("Model:" + str(model_name) + " Category:" + str(question_type) + " Num Events:" + str(num_event))
                        print(str(questions_count) + ":\n" + str(prompt_text) + "\n" + "Response: " + str(response) + "\n")

                        # Prepare the text data to save
                        text = dict.fromkeys({"Question", "Response", "GT"}, None)
                        text["Prompt"] = prompt_text
                        text["Question"] = question["text"]
                        text["Response"] = str(response)
                        text["GT"] = str(question["gt_answers"])
                        text_to_save.append(text.copy())
                        answer_file.save_to_json(text_to_save)

                    # Save model information and date of test to the answer file
                    text_to_save.append(f"Model: {model_name}")
                    text_to_save.append(f"Date of Test: {datetime.today()}")
                    answer_file.save_to_json(text_to_save)
