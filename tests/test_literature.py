import requests

from rag import literature
from tests.fake_literature import RESULTS


def test_search_lines_become_plain_keywords():
    assert literature.clean_query('1. "elderly patient 75 years diabetes management"') == "elderly diabetes management"
    assert literature.clean_query("- geriatric fall prevention age 80+") == "geriatric fall prevention"
    assert literature.clean_query("Falls AND (home OR hospital) NOT stroke") == "falls home hospital stroke"
    assert literature.clean_query("Here are five search queries:") == ""  # a heading, not a query
    assert literature.clean_query("older adults home safety assessment and modification") == \
        "older adults home safety assessment"  # every term must match, so long queries are cut


def test_records_become_citations_with_a_public_link():
    guideline = literature.parse_result(RESULTS[0])
    assert guideline["title"] == "Falls prevention for older adults living at home: a practice guideline"
    assert guideline["kind"] == "Practice guideline" and guideline["url"] == "https://doi.org/10.0000/example.falls-guideline"
    assert guideline["citation"] == (
        "Smith A, Jones B, Lee C, et al. Falls prevention for older adults living at home: a practice guideline. "
        "Age Ageing. 2022. doi:10.0000/example.falls-guideline")
    assert guideline["abstract"].startswith("Background Falls are common")  # markup removed
    trial = literature.parse_result(RESULTS[3])
    assert trial["url"] == "https://pubmed.ncbi.nlm.nih.gov/10000004/" and trial["citation"].endswith("PMID: 10000004")
    # Reports about individual patients and correspondence are not knowledge to cite.
    assert literature.parse_result(RESULTS[2]) is None
    assert literature.parse_result(RESULTS[4]) is None


def test_search_prefers_the_strongest_evidence_and_caches(monkeypatch):
    calls = []

    def fetch(query, page_size, timeout):
        calls.append(query)
        return [dict(item) for item in RESULTS]

    monkeypatch.setattr(literature, "_fetch", fetch)
    found = literature.search("falls prevention older adults", limit=2)
    assert [record["kind"] for record in found] == ["Practice guideline", "Systematic review"]
    assert literature.search("falls prevention older adults", limit=2) == found and len(calls) == 1
    both = literature.search_many(["1. elderly falls at home", "2. geriatric medication review"], limit=3)
    assert [record["kind"] for record in both] == ["Practice guideline", "Systematic review", "Randomized controlled trial"]


def test_an_unreachable_service_pauses_the_search(monkeypatch):
    calls = []

    def offline(query, page_size, timeout):
        calls.append(query)
        raise requests.ConnectionError("no route to host")

    monkeypatch.setattr(literature, "_fetch", offline)
    assert literature.search("falls prevention older adults") == []
    assert literature.search("medication review older adults") == []  # paused: no second wait for a timeout
    assert len(calls) == 1
    literature.reset()
    assert literature.search("medication review older adults") == [] and len(calls) == 2


def test_a_bad_answer_does_not_pause_the_search(monkeypatch):
    calls = []

    def broken(query, page_size, timeout):
        calls.append(query)
        raise ValueError("not JSON")

    monkeypatch.setattr(literature, "_fetch", broken)
    assert literature.search("falls prevention older adults") == []
    assert literature.search("medication review older adults") == [] and len(calls) == 2


def test_the_search_can_be_turned_off(monkeypatch):
    calls = []
    monkeypatch.setattr(literature, "LITERATURE_SEARCH", "off")
    monkeypatch.setattr(literature, "_fetch", lambda *args: calls.append(args) or [])
    assert literature.search("falls prevention older adults") == []
    assert literature.search_many(["falls prevention older adults"]) == [] and calls == []
