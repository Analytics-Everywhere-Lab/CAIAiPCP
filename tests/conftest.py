import os
import sys
import tempfile
import types

import pytest

# Heavy retrieval dependencies (chromadb, torch, sentence-transformers) are not
# needed to test the pipeline logic; a small in-memory corpus stands in for them.
os.environ.setdefault("MEMORY_DIR", tempfile.mkdtemp(prefix="caiaipcp-memory-"))

_DOCUMENTS = [
    "Elderly patient, 79, with recurrent falls at home. Home modification with grab bars reduced falls.",
    "Geriatric case: assisted living transition at 85 with dementia; adjustment difficulties were noted.",
    "Older adult with mild cognitive impairment managed at home with medication blister packs.",
]


class FakeVectorDB:
    def __init__(self, *args, **kwargs):
        pass

    def search(self, query, n_results=5):
        return [
            {"document": doc, "metadata": {"source": "test-corpus"}, "distance": 0.2 + 0.05 * i,
             "similarity_score": 0.8 - 0.05 * i}
            for i, doc in enumerate(_DOCUMENTS[:n_results])
        ]


_rag_stub = types.ModuleType("rag.vector_db")
_rag_stub.MedicalVectorDB = FakeVectorDB
sys.modules["rag.vector_db"] = _rag_stub


@pytest.fixture(autouse=True)
def llm_settings(tmp_path, monkeypatch):
    """Fresh provider settings for every test, on the scripted local model."""
    import llm_caller
    import llm_settings as settings_module

    monkeypatch.setenv("SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings_module.reset_settings_cache()
    llm_caller.clear_status()
    settings_module.update_settings({"provider": "ollama", "anthropic_model": "claude-opus-5-5"})
    yield settings_module
    settings_module.reset_settings_cache()


@pytest.fixture
def fake_llm(monkeypatch):
    import llm_caller
    from tests.fake_ollama import FakeOllama

    fake = FakeOllama()
    monkeypatch.setattr(llm_caller.requests, "post", fake.post)
    return fake


@pytest.fixture(autouse=True)
def memory_service(tmp_path, fake_llm):
    """A fresh, isolated memory store for every test."""
    from memory.config import MemoryConfig
    from memory.service import MemoryService, set_memory_service

    service = MemoryService(MemoryConfig(memory_dir=str(tmp_path / "memory")))
    set_memory_service(service)
    yield service
    service.close()
    set_memory_service(None)
