"""Europe PMC search results for tests, in the shape of the REST API's "core" result type.

Fictional records with reserved example identifiers: tests never reach the network."""

RESULTS = [
    {
        "id": "10000001", "source": "MED", "pmid": "10000001", "doi": "10.0000/example.falls-guideline",
        "title": "Falls prevention for older adults living at home: a <i>practice</i> guideline.",
        "authorString": "Smith A, Jones B, Lee C, Patel D.",
        "journalInfo": {"yearOfPublication": 2022, "journal": {"title": "Age and ageing", "isoabbreviation": "Age Ageing"}},
        "pubYear": "2022",
        "abstractText": "<h4>Background</h4>Falls are common among older adults who live alone. Home hazard "
                        "modification and balance exercise reduce the rate of falls.",
        "pubTypeList": {"pubType": ["Practice Guideline", "Journal Article"]},
    },
    {
        "id": "10000002", "source": "MED", "pmid": "10000002", "doi": "10.0000/example.home-review",
        "title": "Home modification to prevent falls in older adults: a systematic review",
        "authorString": "Garcia M, Chen L.",
        "journalInfo": {"yearOfPublication": 2021, "journal": {"title": "Journal of the American Geriatrics Society",
                                                               "isoabbreviation": "J Am Geriatr Soc"}},
        "pubYear": "2021",
        "abstractText": "Home modifications led by occupational therapists reduced falls by about a fifth.",
        "pubTypeList": {"pubType": ["Systematic Review", "Review", "Journal Article"]},
    },
    {
        "id": "10000003", "source": "MED", "pmid": "10000003",
        "title": "Recurrent falls in an 84-year-old man living alone: a case report",
        "authorString": "Doe J.",
        "journalInfo": {"journal": {"isoabbreviation": "BMJ Case Rep"}},
        "pubYear": "2023",
        "abstractText": "We describe an 84-year-old man with recurrent falls.",
        "pubTypeList": {"pubType": ["Case Reports", "Journal Article"]},
    },
    {
        "id": "10000004", "source": "MED", "pmid": "10000004",
        "title": "Pharmacist medication review for older adults at home: a randomized controlled trial",
        "authorString": "Brown K, White S, Black T, Green R, Gray P.",
        "journalInfo": {"journal": {"isoabbreviation": "BMJ"}},
        "pubYear": "2020",
        "abstractText": "A pharmacist-led medication review reduced potentially inappropriate prescriptions.",
        "pubTypeList": {"pubType": ["Randomized Controlled Trial", "Journal Article"]},
    },
    {
        "id": "10000005", "source": "MED", "pmid": "10000005",
        "title": "Re: home safety programmes",
        "authorString": "Grey H.",
        "pubYear": "2024",
        "abstractText": "A letter about home safety programmes.",
        "pubTypeList": {"pubType": ["Letter"]},
    },
]


def fake_fetch(query, page_size, timeout):
    return [dict(item) for item in RESULTS][:page_size]
