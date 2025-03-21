from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
from .base_inference import BaseInference

class LLaMAInference(BaseInference):
    """Handles inference for fine-tuned LLaMA models (Hugging Face)."""

    def __init__(self, model_path, base_model_id):
        super().__init__(model_path, base_model_id, model_type="llama")

    def load_model(self):
        """Loads the fine-tuned LLaMA model and tokenizer."""
        print(f"Loading fine-tuned LLaMA model from: {self.model_path}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

        # Ensure tokenizer has a pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token  

        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )

        # Load fine-tuned LoRA model
        self.model = PeftModel.from_pretrained(base_model, self.model_path)
        self.model.to(self.device)

        print("LLaMA model loaded successfully.")

    def generate_response(self, user_query, max_length=256, temperature=0.7, top_p=0.9, do_sample=True):
        """Generates a response using the fine-tuned LLaMA chatbot."""

        prompt = f"<|user|>\n{user_query}\n\n<|assistant|>\n"

        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
        input_ids = inputs.input_ids.to(self.device)
        attention_mask = inputs.attention_mask.to(self.device)

        kwargs = self.generate_kwargs(max_length, temperature, top_p, do_sample)

        with torch.no_grad():
            output = self.model.generate(input_ids, attention_mask=attention_mask, **kwargs)

        return self.tokenizer.decode(output[0], skip_special_tokens=True)
