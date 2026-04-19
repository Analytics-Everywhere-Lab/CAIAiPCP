# Contestable LLMs for Care Plan Generation in Aging-in-Place (CAIAiPCP)

This repository contains code for the CAIAiPCP project, which focuses on using contestable large language models (LLMs) to generate care plans for aging-in-place scenarios. The project aims to enhance the quality and transparency of care plans through interactive and contestable AI systems.

## Installation

To set up the project, follow these steps:

1. **Install Ollama**
   To support local model hosting, [install Ollama](https://ollama.com/) on your machine.
   Once installed, run and serve the `gemma` model:
   ```bash
   ollama run gemma4:latest
   ```
   The application communicates with Ollama locally via `http://localhost:11434`.

2. Create your virtual environment and install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install the required npm packages:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm run dev
   ```

> [!NOTE]
> The backend server must be running on `http://localhost:8001` for the frontend to communicate with it.

## Setup

1. Setup the vector database with MedicalRAG dataset:

```bash
python rag/indexer.py
```

2. Start the application:

```bash
python main.py
```


## Demo

![Demo](media/demo.gif)


## Citation

If you use or reference this work in a scientific publication,
we would appreciate that you use the following citations:

```
@article{nguyen2026position,
  title={Position: Multi-Agent Algorithmic Care Systems Demand Contestability for Trustworthy AI},
  author={Nguyen, Truong Thanh Hung and Fournier, H{\'e}l{\`e}ne and Jackson, Piper and Itoh, Makoto and Freeman, Shannon and Richard, Rene and Cao, Hung},
  journal={arXiv preprint arXiv:2603.20595},
  year={2026}
}
```


## References

<https://github.com/anurag-mishra899/Multi-Agents-Appointment-Booking/blob/main/Back-End/tools/tools.py>

## TODO

- [ ] After human review, the status is not updated.
- [ ] Streaming LLM is not real-time.
