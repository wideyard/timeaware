from transformers import (
    T5Tokenizer,
    T5ForConditionalGeneration,
    AutoTokenizer,
    AutoModelForCausalLM,
)
import torch


class GoogleLLMRunner:
    """
     A class to interact with the Gemma model from huggingface for generating responses.
    """
    def __init__(self, model_name, temperature=0):
        """
        Initializes the GoogleLLMRunner with the specified model and temperature.

        Args:
            model_name (str): The Gemma model variant to use.
            temperature (float): Temperature setting to control response randomness (default is 0).
        """
        self.tokenizer = AutoTokenizer.from_pretrained("google/" + str(model_name))
        self.model = AutoModelForCausalLM.from_pretrained(
            "google/" + str(model_name),
            device_map="auto",
            torch_dtype=torch.bfloat16
        )
        self.model_name = model_name
        self.temperature = temperature

    def get_completion(self, action_prompt, restriction, today_restriction, formatted_question):
        """
        Generates a response based on the prompt.

        Args:
            action_prompt (str): The main prompt describing the action or query.
            restriction (str): Answer restriction for the llm.
            today_restriction (str): Date from today.
            formatted_question (str): The question formatted appropriately.

        Returns:
            tuple: A tuple containing the model's response and the input prompt sent to the model.
        """
        chat = [
            {"role": "user",
             "content": restriction + " " + today_restriction + " " + action_prompt + formatted_question},
        ]
        prompt = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
        outputs = self.model.generate(input_ids=inputs.to(self.model.device), max_new_tokens=500)
        outputs = self.tokenizer.decode(outputs[0])
        return outputs, prompt
