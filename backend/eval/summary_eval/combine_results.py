"""
Combine summary evaluation JSON files into a flat table.

Reads all *.json under backend/eval/summary_eval/results and emits a CSV
with columns:
arxiv_id, section_coverage, concision, faithfulness, writing_quality, overall_score

Usage:
  python combine_results.py
"""
import csv
import json
import os
from typing import Dict, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/eval/summary_eval
RESULTS_DIR = os.path.join(BASE_DIR, "results")
OUT_CSV = os.path.join(RESULTS_DIR, "combined_summary_scores.csv")

CRITERIA_ORDER = ["section_coverage", "concision", "faithfulness", "writing_quality"]


def load_result(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def extract_scores(data: Dict) -> Dict:
    row: Dict[str, float] = {"arxiv_id": data.get("arxiv_id", "")}
    criteria: List[Dict] = data.get("criteria", [])
    for crit in criteria:
        name = crit.get("name")
        if name in CRITERIA_ORDER:
            row[name] = crit.get("score", None)
    row["overall_score"] = data.get("overall_score", None)
    return row


def combine_results(results_dir: str = RESULTS_DIR, out_csv: str = OUT_CSV) -> List[Dict]:
    rows: List[Dict] = []
    for fname in sorted(os.listdir(results_dir)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(results_dir, fname)
        try:
            data = load_result(fpath)
            rows.append(extract_scores(data))
        except Exception as exc:
            print(f"Skipping {fname}: {exc}")
            continue

    fieldnames = ["arxiv_id", *CRITERIA_ORDER, "overall_score"]
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    return rows


if __name__ == "__main__":
    combined = combine_results()
    print(f"Wrote {len(combined)} rows to {OUT_CSV}")
    for r in combined:
        print(r)
