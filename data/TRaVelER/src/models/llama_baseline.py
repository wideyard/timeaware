from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    BitsAndBytesConfig,
)
import torch


class LlamaRunner:
    """
     A class to interact with the Llama2 and Llama3 models from huggingface for generating responses.
    """
    def __init__(self, model_name="Llama-2-70b-chat-hf", temperature=0.1):
        """
        Initializes the LlamaRunner with the specified model, tokenizer, and configuration for generation.

        Args:
            model_name (str): The Llama model to use.
            temperature (float): Temperature setting to control response randomness (default is 0.1).
        """
        self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/" + str(model_name))
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id  # for open-ended generation
        self.model_name = "meta-llama/" + model_name
        self.temperature = temperature
        if self.temperature < 0.1:
            self.temperature = 0.1
        self.prompt_specifiers = ["<s>[INST]<<SYS>>", "<</SYS>>", "[/INST]"] # System instructions specifiers for Llama models

        # Load appropriate model configuration based on model type
        if "Llama-2" or "Llama-3" in self.model_name:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            model_id = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
            self.generation_pipe = pipeline(
                "text-generation",
                model=model_id,
                tokenizer=self.tokenizer,
                trust_remote_code=True,
                device_map="auto",  # finds GPU
            )
        elif "Llama-3" in self.model_name and "Instruct" in self.model_name:
            self.generation_pipe = pipeline(
                "text-generation",
                model=self.model_name,
                model_kwargs={"torch_dtype": torch.bfloat16},
                device_map="auto",
            )
        else:
            print("Model not found")
            return

    def get_completion(self, action_prompt, restriction, today_restriction, formatted_question):
        """
        Generates a response based on action_prompt, restriction, today_restriction, formatted_question

        Args:
            action_prompt (str): The main prompt describing the action or query.
            restriction (str): Answer restriction for the llm.
            today_restriction (str): Date from today.
            formatted_question (str): The question formatted appropriately.

        Returns:
            tuple: A tuple containing the model's response and the prompt sent to the model.
        """
        if "Llama-2" in self.model_name:
            prompt = (self.prompt_specifiers[0] + restriction + self.prompt_specifiers[1] +
                      today_restriction + action_prompt + formatted_question + self.prompt_specifiers[2])
            sets = self.generation_pipe(
                prompt,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                do_sample=False,
                top_k=1,
                max_new_tokens=256,
                temperature=self.temperature,
                top_p=0
            )
            result = sets[0]['generated_text']
            result = result.split("[/INST]", 1)[1]
        elif "Llama-3" in self.model_name and "Instruct" in self.model_name:
            # Instruct version needs specific conversation structure
            messages = [
                {"role": "system", "content": restriction},
                {"role": "user", "content": today_restriction + " " + action_prompt + formatted_question}, ]
            prompt = self.generation_pipe.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            terminators = [
                self.generation_pipe.tokenizer.eos_token_id,
                self.generation_pipe.tokenizer.convert_tokens_to_ids("<|eot_id|>")
            ]
            outputs = self.generation_pipe(
                prompt,
                max_new_tokens=2000,
                eos_token_id=terminators,
                do_sample=False, # No randomness
                top_p=1,
            )
            result = outputs[0]["generated_text"][len(prompt):]
            prompt = messages
        else:
            result = "Model not found"
            prompt = "Model not found"

        return result, prompt
