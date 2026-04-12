import os
from datetime import datetime
from openai import OpenAI

# Initialize OpenAI client with API key from environment variables
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class GPTRunner:
    """
    A class to interact with the GPT model for generating responses.
    """
    def __init__(self, model_name="gpt-4-0125-preview", temperature=0):
        """
        Initializes the GPTRunner instance with the specified model name and temperature.

        Args:
            model_name (str): The GPT model to use (default is "gpt-4-0125-preview").
            temperature (float): Temperature setting to control response randomness (default is 0).
        """
        self.temperature = temperature
        self.model_name = model_name

    def get_completion(self, action_prompt, restriction, today_restriction, formatted_question):
        """
        Sends a prompt to the GPT model and returns the model's response.

        Args:
            action_prompt (str): The main prompt describing the action or query.
            restriction (str): Answer restriction for the llm.
            today_restriction (str): Date from today.
            formatted_question (str): The question formatted appropriately.

        Returns:
            tuple: A tuple containing the model's response and the prompt sent to the model.
        """
        prompt = [
            {"role": "system", "content": restriction},
            {"role": "user", "content": today_restriction + " " + action_prompt + formatted_question}, ]
        response = client.chat.completions.create(
            model=self.model_name,
            messages=prompt,
            temperature=self.temperature,
        )
        return response.choices[0].message.content, prompt


