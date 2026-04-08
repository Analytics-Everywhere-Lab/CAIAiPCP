import uvicorn
from env_config import DEVICE, HUGGINGFACE_MODEL_NAME

if __name__ == "__main__":
    print(f"Loading HuggingFace model: {HUGGINGFACE_MODEL_NAME} on {DEVICE}")
    print("This may take a moment on first run...")
    print("\n" + "=" * 50)
    print("Launching FastAPI Server")
    print("=" * 50)
    uvicorn.run("api:app", host="0.0.0.0", port=8002, reload=True)
