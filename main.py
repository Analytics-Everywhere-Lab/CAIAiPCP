import uvicorn
from env_config import OLLAMA_MODEL

if __name__ == "__main__":
    print(f"Loading Ollama model: {OLLAMA_MODEL}")
    print("This may take a moment on first run...")
    print("\n" + "=" * 50)
    print("Launching FastAPI Server")
    print("=" * 50)
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
