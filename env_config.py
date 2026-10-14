import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Ollama Configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:latest")

# env_config.py
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/sse")

# Self-evolving memory (see memory/). Thresholds live in memory/config.py.
MEMORY_ENABLED = os.environ.get("MEMORY_ENABLED", "true").lower() in ("1", "true", "yes")
MEMORY_DIR = os.environ.get("MEMORY_DIR", os.path.join(PROJECT_ROOT, "data", "memory"))
# Consolidate short-term memory into long-term memory once this many reviewed
# cases are waiting; 1 means after every reviewed case.
MEMORY_CONSOLIDATE_EVERY_N = int(os.environ.get("MEMORY_CONSOLIDATE_EVERY_N", "1"))
MEMORY_TOP_K = int(os.environ.get("MEMORY_TOP_K", "3"))
# Turn applicable long-term lessons into arguments the clinician can contest, instead
# of only adding them to prompts as guidance.
MEMORY_INSTANTIATE_ARGUMENTS = os.environ.get("MEMORY_INSTANTIATE_ARGUMENTS", "true").lower() in ("1", "true", "yes")

# Chatbot context compaction, in approximate tokens (1 token ~ 4 characters)
CHAT_CONTEXT_TOKEN_BUDGET = int(os.environ.get("CHAT_CONTEXT_TOKEN_BUDGET", "2400"))
CHAT_HISTORY_TOKEN_BUDGET = int(os.environ.get("CHAT_HISTORY_TOKEN_BUDGET", "1200"))
CHAT_RECENT_TURNS = int(os.environ.get("CHAT_RECENT_TURNS", "6"))
# Room for the assistant's answer. Only the context it reads is compacted, never its reply.
CHAT_MAX_TOKENS = int(os.environ.get("CHAT_MAX_TOKENS", "4096"))

# Citable knowledge. Case records in the local vector database describe other patients:
# they inform generation as background but are never cited or shown. References come
# only from published literature, searched on Europe PMC ("off" disables the search).
LITERATURE_SEARCH = os.environ.get("LITERATURE_SEARCH", "europepmc").lower()
LITERATURE_TIMEOUT = float(os.environ.get("LITERATURE_TIMEOUT", "8"))
LITERATURE_PER_QUERY = int(os.environ.get("LITERATURE_PER_QUERY", "2"))

# QBAF: arguments authored by the clinician are re-verified like any other, but
# their base score blends the verifier's validity with this prior of clinician authority.
HUMAN_TRUST_PRIOR = float(os.environ.get("HUMAN_TRUST_PRIOR", "0.9"))
HUMAN_TRUST_WEIGHT = float(os.environ.get("HUMAN_TRUST_WEIGHT", "0.5"))
