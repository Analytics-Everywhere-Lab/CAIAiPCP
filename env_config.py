import os
import torch

# DEVICE
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# HuggingFace Model Configuration
HUGGINGFACE_MODEL_NAME = "HuggingFaceTB/SmolLM3-3B"
# env_config.py
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/sse")
