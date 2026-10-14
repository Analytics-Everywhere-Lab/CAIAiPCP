"""Published literature for care plan citations, searched on Europe PMC.

The local vector database holds case records of other patients. They inform
generation as background but are never cited, quoted or shown, so every
reference in a care plan is a published source found here: peer-reviewed papers,
reviews and guidelines indexed by Europe PMC (which covers PubMed/MEDLINE), each
with a public record the reader can open through its DOI or PubMed link.

A failed search never fails a care plan. Without network access the plan is
written without references, and the search pauses for a while rather than
waiting for a timeout on every query.
"""
import html
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from env_config import LITERATURE_PER_QUERY, LITERATURE_SEARCH, LITERATURE_TIMEOUT
from utils import clip_text

EUROPE_PMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
SOURCE_NAME = "Europe PMC"
OFFLINE_PAUSE_SECONDS = 600
MAX_QUERY_TERMS = 5
_CACHE_SIZE = 256

# Strongest evidence first; a record of any other type counts as a journal article.
_EVIDENCE_KINDS = [
    ("practice guideline", "Practice guideline", 4),
    ("guideline", "Guideline", 4),
    ("systematic review", "Systematic review", 3),
    ("meta-analysis", "Meta-analysis", 3),
    ("randomized controlled trial", "Randomized controlled trial", 2),
    ("review", "Review", 2),
]
# Not knowledge to cite: reports about individual patients, retracted work and correspondence.
_EXCLUDED_TYPES = ("case report", "retracted publication", "retraction of publication", "erratum",
                   "published erratum", "comment", "letter", "editorial", "news")
_CASE_TITLE = re.compile(r"\b(case reports?|a case of|case series)\b", re.IGNORECASE)
_QUERY_NOISE = re.compile(r'[:()\[\]{}"^~*?\\/!+=<>|&]|(?<!\w)-')
_STOPWORDS = {
    "a", "an", "and", "or", "not", "the", "of", "in", "for", "to", "on", "with", "at", "by", "from", "as",
    "patient", "patients", "year", "years", "old", "aged", "age", "yo", "specific", "query", "queries",
}

_cache: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
_lock = threading.Lock()
_paused_until = 0.0


def enabled() -> bool:
    return LITERATURE_SEARCH not in ("off", "none", "false", "0", "")


def reset() -> None:
    """Forget cached results and any pause after a network failure."""
    global _paused_until
    with _lock:
        _cache.clear()
        _paused_until = 0.0


def clean_query(text: str) -> str:
    """A search line from the model as plain keywords: no numbering, quotes, ages or filler words.

    Europe PMC requires every term to match, so long sentences find little; lower case also keeps
    words such as "and" from being read as search operators."""
    text = (text or "").strip()
    if text.endswith(":"):  # a heading line such as "Here are five queries:"
        return ""
    text = _QUERY_NOISE.sub(" ", re.sub(r"^\s*(?:\d+[.)]|[-*•])\s*", "", text))
    terms: List[str] = []
    for word in text.split():
        word = word.strip(".,;'`").lower()
        if word and not any(ch.isdigit() for ch in word) and word not in _STOPWORDS and word not in terms:
            terms.append(word)
    return " ".join(terms[:MAX_QUERY_TERMS])


def _clean(text: Any) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", str(text or ""))).split())


def _authors(author_string: Any) -> str:
    names = [name.strip() for name in _clean(author_string).rstrip(".").split(",") if name.strip()]
    if len(names) > 3:
        return ", ".join(names[:3]) + ", et al."
    return ", ".join(names)


def _evidence_kind(types: List[str]) -> Tuple[str, int]:
    for key, label, weight in _EVIDENCE_KINDS:
        if any(key in kind for kind in types):
            return label, weight
    return "Journal article", 1


def format_citation(authors: str, title: str, journal: str, year: str, doi: str, pmid: str) -> str:
    """Vancouver-style citation: Authors. Title. Journal. Year. doi:..."""
    pieces = []
    if authors:
        pieces.append(authors if authors.endswith(".") else authors + ".")
    pieces.append(title.rstrip(".") + ".")
    venue = ". ".join(part for part in (journal.rstrip("."), year) if part)
    if venue:
        pieces.append(venue + ".")
    if doi:
        pieces.append(f"doi:{doi}")
    elif pmid:
        pieces.append(f"PMID: {pmid}")
    return " ".join(pieces)


def parse_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """One Europe PMC record as a citable source, or None when it is not citable knowledge."""
    if not isinstance(item, dict):
        return None
    title = _clean(item.get("title")).rstrip(".")
    abstract = _clean(item.get("abstractText"))
    types = (item.get("pubTypeList") or {}).get("pubType") or item.get("pubType") or []
    types = [str(kind).lower() for kind in ([types] if isinstance(types, str) else types)]
    if not title or not abstract or _CASE_TITLE.search(title):
        return None
    if any(kind.startswith(excluded) for kind in types for excluded in _EXCLUDED_TYPES):
        return None
    journal_info = item.get("journalInfo") or {}
    journal = journal_info.get("journal") or {}
    journal_name = _clean(journal.get("isoabbreviation") or journal.get("medlineAbbreviation")
                          or journal.get("title") or item.get("journalTitle"))
    year = str(item.get("pubYear") or journal_info.get("yearOfPublication") or "").strip()
    doi = str(item.get("doi") or "").strip()
    pmid = str(item.get("pmid") or "").strip()
    if doi:
        url = f"https://doi.org/{doi}"
    elif pmid:
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    elif item.get("id"):
        url = f"https://europepmc.org/article/{item.get('source') or 'MED'}/{item['id']}"
    else:
        url = ""
    kind, weight = _evidence_kind(types)
    authors = _authors(item.get("authorString"))
    return {
        "title": title,
        "authors": authors,
        "journal": journal_name,
        "year": year,
        "doi": doi,
        "pmid": pmid,
        "url": url,
        "kind": kind,
        "evidence_weight": weight,
        "abstract": abstract,
        "citation": format_citation(authors, title, journal_name, year, doi, pmid),
        "source": SOURCE_NAME,
    }


def _fetch(query: str, page_size: int, timeout: float) -> List[Dict[str, Any]]:
    response = requests.get(EUROPE_PMC_SEARCH, params={
        "query": f"({query}) AND HAS_ABSTRACT:y AND SRC:MED",
        "format": "json",
        "resultType": "core",
        "pageSize": page_size,
    }, timeout=timeout)
    response.raise_for_status()
    return ((response.json() or {}).get("resultList") or {}).get("result") or []


def record_key(record: Dict[str, Any]) -> str:
    return (record.get("doi") or record.get("pmid") or record.get("title") or "").lower()


def search(query: str, limit: int = LITERATURE_PER_QUERY) -> List[Dict[str, Any]]:
    """Up to `limit` citable sources for one query: the strongest evidence among the most relevant hits."""
    global _paused_until
    query = clean_query(query)
    if not enabled() or limit <= 0 or len(query.split()) < 2:
        return []
    key = (query, limit)
    with _lock:
        if key in _cache:
            return [dict(record) for record in _cache[key]]
        if time.monotonic() < _paused_until:
            return []
    try:
        items = _fetch(query, page_size=max(4 * limit, 8), timeout=LITERATURE_TIMEOUT)
    except (requests.ConnectionError, requests.Timeout) as exc:
        with _lock:
            _paused_until = time.monotonic() + OFFLINE_PAUSE_SECONDS
        print(f"Literature search unreachable ({type(exc).__name__}); retrying in {OFFLINE_PAUSE_SECONDS // 60} minutes")
        return []
    except Exception as exc:  # a bad answer for one query; the others may still work
        print(f"Literature search failed for '{query}': {exc}")
        return []
    records = [record for record in (parse_result(item) for item in items) if record]
    ranked = [record for _, record in sorted(enumerate(records), key=lambda pair: (-pair[1]["evidence_weight"], pair[0]))]
    found = []
    for record in ranked:
        if record_key(record) not in {record_key(kept) for kept in found}:
            found.append({**record, "search_query": query})
        if len(found) >= limit:
            break
    with _lock:
        if len(_cache) >= _CACHE_SIZE:
            _cache.pop(next(iter(_cache)))
        _cache[key] = found
    return [dict(record) for record in found]


def search_many(queries: Iterable[str], limit: int = LITERATURE_PER_QUERY, max_queries: int = 5) -> List[Dict[str, Any]]:
    """Sources for several queries, searched in parallel, without duplicates, in query order."""
    cleaned: List[str] = []
    for query in queries:
        text = clean_query(query)
        if len(text.split()) >= 2 and text not in cleaned:
            cleaned.append(text)
    cleaned = cleaned[:max_queries]
    if not cleaned or not enabled():
        return []
    with ThreadPoolExecutor(max_workers=min(4, len(cleaned))) as pool:
        batches = list(pool.map(lambda text: search(text, limit), cleaned))
    seen, results = set(), []
    for batch in batches:
        for record in batch:
            if record_key(record) not in seen:
                seen.add(record_key(record))
                results.append(record)
    return results


def as_reference(record: Dict[str, Any], ref_id: int) -> Dict[str, Any]:
    """A source as a numbered reference of the case, cited in the plan as [REF-<id>]."""
    return {
        **record,
        "id": ref_id,
        "content": clip_text(record.get("abstract", ""), 200),
        "full_content": record.get("abstract", ""),
        "metadata": {"title": record.get("title"), "source": record.get("source", SOURCE_NAME)},
        "used_in": [],
    }
