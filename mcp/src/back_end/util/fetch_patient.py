"""Hit each Accuro provider-portal endpoint for a patient and print the JSON.

Usage:
    python scripts/fetch_patient.py --patient-id 12345
    python scripts/fetch_patient.py --patient-id 12345 --save
    python scripts/fetch_patient.py --phn 1234567890
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from accuro_sample import endpoints  # noqa: E402
from accuro_sample.client import AccuroClient  # noqa: E402
from accuro_sample.config import get_settings  # noqa: E402

PATIENT_ENDPOINTS = [
    ("patient", endpoints.get_patient),
    ("clinical-notes", endpoints.get_clinical_notes),
    ("generated-letters", endpoints.get_generated_letters),
    ("history-items", endpoints.get_history_items),
    ("diagnoses", endpoints.get_diagnoses),
    ("prescriptions", endpoints.get_prescriptions),
    ("allergies", endpoints.get_allergies),
    ("immunizations", endpoints.get_immunizations),
    ("lab-groups", endpoints.get_lab_groups),
    ("documents", endpoints.get_documents),
]


def _print_section(label: str, body: object) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(body, indent=2, default=str))
    return(json.dumps(body, indent=2, default=str))


def _save(name: str, body: object) -> None:
    out_dir = Path(get_settings().responses_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(body, indent=2, default=str))


def _call(label: str, fn, *args, save: bool) -> None:
    try:
        body = fn(*args)
    except httpx.HTTPStatusError as e:
        print(f"\n=== {label} ===\n[!] HTTP {e.response.status_code}: {e.response.text[:300]}")
        return
    except httpx.HTTPError as e:
        print(f"\n=== {label} ===\n[!] request failed: {e}")
        return
    ret = _print_section(label, body)
    if save:
        _save(label, body)
    return ret


def get_patient_info(pid: str) -> dict:
    with AccuroClient() as client:
        ret = _call("search", endpoints.search_patients, client, pid, save=False)
    return ret


#def main() -> None:
#    p = argparse.ArgumentParser(description="Fetch Accuro provider-portal data for a patient.")
#    p.add_argument("--patient-id", help="Patient ID to fetch")
#    p.add_argument("--phn", help="PHN / care-card number to search for instead of a full pull")
#    p.add_argument("--save", action="store_true", help="Also save responses to RESPONSES_DIR")
#    args = p.parse_args()
#
#    if not args.patient_id and not args.phn:
#        p.error("Provide --patient-id or --phn")
#
#    with AccuroClient() as client:
#        if args.phn:
#            _call("search", endpoints.search_patients, client, args.phn, save=args.save)
#
#        if args.patient_id:
#            for label, fn in PATIENT_ENDPOINTS:
#                _call(label, fn, client, args.patient_id, save=args.save)
#

if __name__ == "__main__":
    pass
