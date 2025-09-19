import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from env_config import HUGGINGFACE_MODEL_NAME, DEVICE


# Singleton pattern for model loading
class ModelManager:
    _instance = None
    _model = None
    _tokenizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model_and_tokenizer(self):
        if self._model is None or self._tokenizer is None:
            print(f"Loading model {HUGGINGFACE_MODEL_NAME} for the first time...")
            self._tokenizer = AutoTokenizer.from_pretrained(HUGGINGFACE_MODEL_NAME)
            self._model = AutoModelForCausalLM.from_pretrained(
                HUGGINGFACE_MODEL_NAME
            ).to(DEVICE)
            print("Model loaded successfully!")
        return self._model, self._tokenizer


# Create singleton instance
model_manager = ModelManager()


def call_huggingface_llm(
    prompt: str, temperature: float = 0.7, max_tokens: int = 512
) -> str:
    """Make a call to HuggingFace model"""
    model, tokenizer = model_manager.get_model_and_tokenizer()

    try:
        # Prepare the model input
        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            enable_thinking=False,
            add_generation_prompt=True,
        )

        model_inputs = tokenizer([text], return_tensors="pt").to(DEVICE)

        # Generate the output with temperature and max_new_tokens
        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True if temperature > 0 else False,
                pad_token_id=tokenizer.eos_token_id,
            )

        # Get and decode the output
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]) :]
        response = tokenizer.decode(output_ids, skip_special_tokens=True)

        return response.strip()

    except Exception as e:
        print(f"Error calling HuggingFace model: {e}")
        return ""


def call_huggingface_llm_stream(
    prompt: str, temperature: float = 0.7, max_tokens: int = 512
):
    """Stream responses from HuggingFace model"""
    model, tokenizer = model_manager.get_model_and_tokenizer()

    try:
        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            enable_thinking=False,
            add_generation_prompt=True,
        )

        model_inputs = tokenizer([text], return_tensors="pt").to(DEVICE)

        from transformers import TextIteratorStreamer
        from threading import Thread

        streamer = TextIteratorStreamer(
            tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        generation_kwargs = dict(
            **model_inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True if temperature > 0 else False,
            pad_token_id=tokenizer.eos_token_id,
            streamer=streamer,
        )

        # Run generation in a separate thread
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()

        for token in streamer:
            yield token

        thread.join()

    except Exception as e:
        print(f"Error in streaming: {e}")
        yield ""


# Keep the original for non-streaming needs
call_llm = call_huggingface_llm
call_llm_stream = call_huggingface_llm_stream
