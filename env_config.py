import torch

# DEVICE
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# HuggingFace Model Configuration
HUGGINGFACE_MODEL_NAME = "HuggingFaceTB/SmolLM3-3B"
