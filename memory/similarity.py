"""Scope-safe semantic relations between memory items, ported from SEMV's
memory_similarity.py: a lexical (token + character-trigram) similarity, a
deterministic relation classifier, and a batched LLM check only for pairs the
rules cannot decide. Ambiguity fails closed to "unrelated"."""
import hashlib
import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "is", "are", "was", "were", "be",
    "been", "it", "its", "this", "that", "with", "as", "by", "at", "from", "when", "while", "should",
    "must", "into", "patient", "patients", "care", "plan",
}
_NEGATION_TOKENS = {"not", "never", "no", "avoid", "reject", "without", "dont", "against", "unless"}
_RELATIONS = {"equivalent", "a_entails_b", "b_entails_a", "contradicts", "unrelated"}


def stable_hash(text: str, length: int = 16) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:length]


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    lowered = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return " ".join(lowered.split())


def content_tokens(text: Optional[str]) -> set:
    return {token for token in normalize_text(text).split() if token not in _STOPWORDS}


def canonical_key(memory_type: str, stage: Optional[str], text: Optional[str]) -> str:
    return "|".join([memory_type or "", stage or "general", stable_hash(normalize_text(text) or "empty")])


def semantic_signature(memory_type: str, stage: Optional[str], failure_type: Optional[str],
                       polarity: Optional[str]) -> str:
    return "|".join([memory_type or "", stage or "general", failure_type or "none", polarity or "neutral"])


def lexical_similarity(text_a: Optional[str], text_b: Optional[str]) -> float:
    tokens_a, tokens_b = content_tokens(text_a), content_tokens(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    token_jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    norm_a = normalize_text(text_a).replace(" ", "")
    norm_b = normalize_text(text_b).replace(" ", "")
    grams_a = {norm_a[i:i + 3] for i in range(max(0, len(norm_a) - 2))}
    grams_b = {norm_b[i:i + 3] for i in range(max(0, len(norm_b) - 2))}
    gram_jaccard = len(grams_a & grams_b) / len(grams_a | grams_b) if grams_a and grams_b else 0.0
    return 0.6 * token_jaccard + 0.4 * gram_jaccard


def polarity_of(item: Dict[str, Any]) -> str:
    polarity = item.get("polarity")
    if polarity in ("do", "positive"):
        return "positive"
    if polarity in ("avoid", "negative"):
        return "negative"
    tokens = content_tokens(item.get("text")) | content_tokens(item.get("recommended_action"))
    return "negative" if tokens & _NEGATION_TOKENS else "positive"


def compatible(item_a: Dict[str, Any], item_b: Dict[str, Any]) -> bool:
    if item_a.get("memory_type") != item_b.get("memory_type"):
        return False
    stage_a, stage_b = item_a.get("stage") or "general", item_b.get("stage") or "general"
    if stage_a != stage_b and "general" not in (stage_a, stage_b):
        return False
    failure_a, failure_b = item_a.get("failure_type"), item_b.get("failure_type")
    return failure_a == failure_b or not (failure_a and failure_b)


class HybridSimilarity:
    """Deterministic relations first; an optional LLM call settles ambiguous pairs."""

    def __init__(self, duplicate_similarity: float = 0.85, contradiction_similarity: float = 0.75,
                 shortlist_k: int = 20, llm_json: Optional[Callable[..., Any]] = None) -> None:
        self.duplicate_similarity = duplicate_similarity
        self.contradiction_similarity = contradiction_similarity
        self.shortlist_k = shortlist_k
        self.llm_json = llm_json
        self._cache: Dict[Tuple[str, str], str] = {}

    def similarity(self, text_a: Optional[str], text_b: Optional[str]) -> float:
        return lexical_similarity(text_a, text_b)

    def shortlist(self, query_text: str, items: List[Dict[str, Any]], k: Optional[int] = None):
        scored = [(self.similarity(query_text, item.get("text") or ""), item) for item in items]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[: k or self.shortlist_k]

    @staticmethod
    def _identity(item: Dict[str, Any]) -> str:
        keys = ("memory_type", "stage", "failure_type", "polarity", "text", "trigger_pattern", "recommended_action")
        return stable_hash(json.dumps({key: item.get(key) for key in keys}, sort_keys=True, default=str), 32)

    @staticmethod
    def _reverse(relation: str) -> str:
        return {"a_entails_b": "b_entails_a", "b_entails_a": "a_entails_b"}.get(relation, relation)

    def _remember(self, item_a, item_b, relation: str) -> None:
        key_a, key_b = self._identity(item_a), self._identity(item_b)
        self._cache[(key_a, key_b)] = relation
        self._cache[(key_b, key_a)] = self._reverse(relation)

    def deterministic(self, item_a: Dict[str, Any], item_b: Dict[str, Any]) -> Optional[str]:
        """Return a relation, or None when only an LLM could decide."""
        if not compatible(item_a, item_b):
            return "unrelated"
        key_a = item_a.get("canonical_key") or canonical_key(item_a.get("memory_type", ""), item_a.get("stage"), item_a.get("text"))
        key_b = item_b.get("canonical_key") or canonical_key(item_b.get("memory_type", ""), item_b.get("stage"), item_b.get("text"))
        if key_a == key_b:
            return "equivalent"
        text_a, text_b = item_a.get("text") or "", item_b.get("text") or ""
        sim = self.similarity(text_a, text_b)
        polarity_a, polarity_b = polarity_of(item_a), polarity_of(item_b)
        if sim >= self.duplicate_similarity and polarity_a == polarity_b:
            return "equivalent"
        structured = self._structured_match(item_a, item_b)
        if polarity_a != polarity_b and (
            sim >= self.contradiction_similarity
            or (structured and sim >= self.contradiction_similarity * 0.6)
        ):
            return "contradicts"
        tokens_a, tokens_b = content_tokens(text_a), content_tokens(text_b)
        if tokens_a and tokens_b and polarity_a == polarity_b and sim >= self.contradiction_similarity * 0.6:
            if tokens_a > tokens_b:
                return "a_entails_b"
            if tokens_b > tokens_a:
                return "b_entails_a"
        if sim >= self.contradiction_similarity * 0.6 and self.llm_json is not None:
            return None
        return "unrelated"

    def relation(self, item_a: Dict[str, Any], item_b: Dict[str, Any]) -> str:
        return self.relations_batch([(item_a, item_b)])[0]

    def relations_batch(self, pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[str]:
        results: List[Optional[str]] = [None] * len(pairs)
        pending = []
        for index, (item_a, item_b) in enumerate(pairs):
            cached = self._cache.get((self._identity(item_a), self._identity(item_b)))
            if cached is not None:
                results[index] = cached
                continue
            relation = self.deterministic(item_a, item_b)
            if relation is None:
                pending.append(index)
            else:
                results[index] = relation
                self._remember(item_a, item_b, relation)
        if pending:
            classified = self._llm_relations([pairs[index] for index in pending])
            for index, relation in zip(pending, classified):
                results[index] = relation
                self._remember(pairs[index][0], pairs[index][1], relation)
        return [result or "unrelated" for result in results]

    def _llm_relations(self, pairs) -> List[str]:
        payload = [
            {"pair_id": str(index), "statement_a": a.get("text") or "", "statement_b": b.get("text") or ""}
            for index, (a, b) in enumerate(pairs)
        ]
        prompt = (
            "Classify the semantic relation of every pair of care-planning lessons in one batch. "
            'Return JSON {"results": [{"pair_id": "0", "relation": "equivalent|a_entails_b|b_entails_a|contradicts|unrelated"}]}. '
            "Entailment is directional. Omitted or ambiguous pairs are unrelated.\n"
            f"Pairs: {json.dumps(payload)}"
        )
        try:
            data = self.llm_json(prompt, temperature=0.0, max_tokens=1024)
            rows = data.get("results") if isinstance(data, dict) else None
            by_id = {str(row.get("pair_id")): str(row.get("relation", "")).lower() for row in rows or []}
        except Exception:
            by_id = {}
        output = []
        for index in range(len(pairs)):
            relation = by_id.get(str(index), "unrelated")
            relation = "a_entails_b" if relation == "entails" else relation
            output.append(relation if relation in _RELATIONS else "unrelated")
        return output

    @staticmethod
    def _structured_match(item_a: Dict[str, Any], item_b: Dict[str, Any]) -> bool:
        trigger = lexical_similarity(item_a.get("trigger_pattern"), item_b.get("trigger_pattern"))
        action = lexical_similarity(item_a.get("recommended_action"), item_b.get("recommended_action"))
        return trigger >= 0.4 or action >= 0.4
