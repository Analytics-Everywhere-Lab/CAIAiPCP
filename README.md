# Contestable LLMs for Care Plan Generation in Aging-in-Place (CAIAiPCP)

This repository contains code for the CAIAiPCP project, which focuses on using contestable large language models (LLMs) to generate care plans for aging-in-place scenarios. The project aims to enhance the quality and transparency of care plans through interactive and contestable AI systems.

## Installation

To set up the project, follow these steps:

1. Set up Huggingface CLI to use the `HuggingFaceTB/SmolLM3-3B` model:

   ```bash
   huggingface-cli login
   ```

2. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Setup the vector database with MedicalRAG dataset:

```bash
python rag/indexer.py
```

2. Start the application:

```bash
python main.py
```

## References

<https://github.com/anurag-mishra899/Multi-Agents-Appointment-Booking/blob/main/Back-End/tools/tools.py>

## TODO

- [ ] After human review, the status is not updated.
- [ ] Streaming LLM is not real-time.