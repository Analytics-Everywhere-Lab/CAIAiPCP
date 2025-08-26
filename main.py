from env_config import DEVICE, HUGGINGFACE_MODEL_NAME
from interface import CarePlanGradioInterface


if __name__ == "__main__":
    print(f"Loading HuggingFace model: {HUGGINGFACE_MODEL_NAME} on {DEVICE}")
    print("This may take a moment on first run...")

    # Launch Gradio interface
    print("\n" + "=" * 50)
    print("Launching Elderly Care Plan Generator Interface")
    print("=" * 50)
    print("\nThe interface will open in your default browser.")
    print("If it doesn't open automatically, click the URL shown below.")
    print("\nIn the interface, you can:")
    print("1. Enter patient information")
    print("2. Review and modify generated arguments interactively")
    print("3. Get a comprehensive care plan with explanations")
    print("\nPress Ctrl+C to stop the server.\n")

    interface = CarePlanGradioInterface()
    interface.launch(share=False)  # Set share=True to create a public link
