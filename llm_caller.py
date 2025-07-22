import requests
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from env_config import (
    HUGGINGFACE_MODEL_NAME,
    NVIDIA_API_KEY,
    NVIDIA_API_URL,
    NVIDIA_MODEL_NAME,
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading model on {DEVICE}")


def call_nvidia_llm(
    prompt: str, temperature: float = 0.7, max_tokens: int = 512
) -> str:
    """Make a call to NVIDIA NIM API (kept for reference)"""
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json",
    }

    payload = {
        "model": NVIDIA_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 1.00,
        "stream": False,
    }

    try:
        response = requests.post(NVIDIA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error calling NVIDIA API: {e}")
        return ""


def call_huggingface_llm(
    prompt: str, temperature: float = 0.7, max_tokens: int = 512
) -> str:
    """Make a call to HuggingFace model"""
    tokenizer = AutoTokenizer.from_pretrained(HUGGINGFACE_MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(HUGGINGFACE_MODEL_NAME).to(DEVICE)
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

call_llm = call_huggingface_llm  # Use HuggingFace model for LLM calls