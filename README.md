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

   - "Tell" the development server to “open in browser” (e.g., type : o in the development server terminal window).
   - This should open your default browser and open the frontend graphical user interface.


> [!NOTE]
> The backend server may need to be running on `http://localhost:8001` for the frontend to communicate with it.

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

## Contestation Workflow

1. **Review the argument graph.** The care team's supporting and challenging arguments appear in the
   *Interactive Graph Review* panel (never in the chat). Edit, remove (kept for audit and restorable) or add
   arguments, then accept to generate the plan.
2. **Read the care plan.** Arguments are verified, then weighed in a quantitative bipolar argumentation
   framework (QBAF, quadratic energy semantics). Each care option gets a strength and an assessment
   (*Recommended*, *Recommended with conditions*, *Clinical judgment required*, *Not recommended at this time*,
   *Not recommended*). The plan is a professional document with fixed sections, a decision summary, references,
   and version history. Use **Download PDF** for a typeset copy, or **Print**.
3. **Give feedback on the plan.** Select text in the plan, comment on a section, write general feedback, or switch
   the chat to *Plan feedback*. Feedback is collected until you click **Regenerate Care Plan**.
4. **Regenerate.** Free-text feedback is formulated as QBAF operations (add, reject or edit an argument, add a
   care option, or a presentation-only writer instruction). Every argument is re-verified against the new
   feedback, the QBAF is re-evaluated, and a revision step reasons about how to update the plan:
   - *targeted revision*: rewrite only the affected sections, keep the rest word for word;
   - *full regeneration*: required whenever an option's assessment or ranking changes;
   - *presentation rewrite*: style or format feedback that leaves the clinical content unchanged.

   The new version explains how it was produced and which feedback and argument changes it applied.
5. **Keep contesting.** The argument table stays editable after the plan exists; table edits alone re-verify
   only the changed arguments, then regenerate.
6. **Approve** a version to sign it off; approval also tells the memory which lessons helped.

The chatbot knows every argument and the current plan through a compact context (pipe-delimited argument
rows, a budgeted plan digest, a rolling conversation summary and a bounded event log), so the prompt stays small
however long the conversation gets.

```text
new case:   rag_retrieval -> care_plan_generation -> argument_generation -> human_review (pause)
            -> argument_validation -> qbaf_evaluation -> revision_planning -> plan_revision
            -> scheduling -> memory_reflection
contest:    argument_validation -> ... -> plan_revision -> memory_reflection
feedback:   feedback_integration -> argument_validation -> ... -> plan_revision -> memory_reflection
```

## Self-Evolving Memory

Adapted from [SEMV](https://github.com/Analytics-Everywhere-Lab/SEMV)'s memory consolidation. Every kind of
clinician feedback reaches memory in one form: operations on the QBAF.

```text
Clinician contestations (table edits + feedback formulated as QBAF operations)
        |  reflection: grounded, de-identified lesson candidates (episodic / failure / semantic)
        v
Fail-closed verification -> short-term memory -> consolidation across cases
        |  independent support per distinct patient, Beta-style confidence, conflicts kept as evidence,
        |  generalization of repeated lessons into semantic rules, deprecation under contradiction
        v
Long-term memory -> guidance in prompts, and contestable "learned" arguments in new cases
```

- Memory is guidance, never evidence. Lessons are retrieved for option generation, argument generation,
  verification and plan writing; applicable lessons also become arguments with a *Learned from past reviews*
  badge, which the clinician can reject like any other argument. Rejecting one is recorded as conflict evidence
  against that lesson.
- Usage outcomes (approved plans, contested lessons) feed back into retrieval ranking.
- The *Learned Memory* panel shows active, under-review, staged and deprecated lessons, and lets a reviewer
  approve, hold or reject them.

Memory lives in `data/memory/` (JSONL, with an archive and snapshots). Inspect or run consolidation from the
command line:

```bash
python scripts/consolidate_memory.py --dry-run
python scripts/consolidate_memory.py --apply --snapshot
python scripts/consolidate_memory.py --review mem_1234abcd --decision approve
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `MEMORY_ENABLED` | `true` | Turn the self-evolving memory on or off |
| `MEMORY_DIR` | `data/memory` | Where memory is stored |
| `MEMORY_CONSOLIDATE_EVERY_N` | `1` | Consolidate once this many reviewed cases are waiting |
| `MEMORY_TOP_K` | `3` | Lessons retrieved per pipeline stage |
| `MEMORY_INSTANTIATE_ARGUMENTS` | `true` | Turn applicable lessons into contestable arguments |
| `CHAT_CONTEXT_TOKEN_BUDGET` | `2400` | Approximate tokens for the chatbot's case context |
| `CHAT_HISTORY_TOKEN_BUDGET` | `1200` | History size before older turns are summarized |
| `CHAT_RECENT_TURNS` | `6` | Turns always kept verbatim |
| `HUMAN_TRUST_PRIOR`, `HUMAN_TRUST_WEIGHT` | `0.9`, `0.5` | Base score of clinician-authored arguments: blend of verified validity and clinician authority |
| `VITE_API_BASE` (frontend) | `http://localhost:8001` | Backend URL used by the frontend |

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /api/chat/start`, `GET /api/chat/stream/{id}` | Start a case and stream a graph run (server-sent events) |
| `POST /api/chat/action/{id}` | `accept`, `modify`, `remove`, `restore`, `add` an argument |
| `POST /api/chat/regenerate/{id}` | Regenerate with `{"feedback": [{"text", "section_id", "quote"}]}`; then open the stream |
| `POST /api/chat/approve/{id}` | Approve a plan version |
| `GET /api/care-plan/{id}/pdf?version=N` | Download a plan version as PDF |
| `POST /api/chat/message/{id}` | Ask the chatbot (streamed) |
| `GET /api/chat/state/{id}` | Current arguments, plan versions and pending changes |
| `GET /api/memory`, `POST /api/memory/consolidate`, `POST /api/memory/{memory_id}/review` | Memory overview, consolidation and governance |

## Tests

The test suite stubs the vector database and the Ollama endpoint, so it runs without a GPU or a model:

```bash
pip install pytest httpx
pytest
```


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
