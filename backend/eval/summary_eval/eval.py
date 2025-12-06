"""
Summary evaluation system for QuickLit.

This module reads section-by-section paper summaries, sends them to an LLM
grader, and records structured scores using a fixed rubric. Each summary is
evaluated on section coverage (capturing the main ideas of every primary
section), concision (clear and compact phrasing), faithfulness (alignment with
the source paper without hallucinations), writing quality (grammar and
readability), and an overall score that reflects holistic quality across the
criteria.
"""
import json
import os
import re
from typing import Dict, List

from openai import OpenAI
# run in terminal:export OPENAI_API_KEY="your_api_key_here"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/eval/summary_eval
BACKEND_DIR = os.path.dirname(os.path.dirname(BASE_DIR))  # backend/
SUMMARIES_DIR = os.path.join(BACKEND_DIR, "log", "summaries")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

os.makedirs(RESULTS_DIR, exist_ok=True)


def filename_to_arxiv_id(fname: str) -> str:
    """
    Convert filenames like "1234_56789_summary.txt" or "1234.56789.txt" into "1234.56789".
    Falls back to replacing the first underscore with a dot.
    """
    stem = fname.replace(".txt", "")
    stem = stem.replace("_summary", "")
    if re.match(r"^\d{4}_\d{5}$", stem):
        return stem.replace("_", ".")
    if re.match(r"^\d{4}\.\d{5}$", stem):
        return stem
    return stem.replace("_", ".", 1)


def build_prompt(arxiv_id: str, pdf_url: str, summary_text: str) -> str:
    return f"""
You are grading a section-by-section summary for an academic paper.

Paper PDF: {pdf_url}
arXiv ID: {arxiv_id}

Summary provided:
<<<SUMMARY
{summary_text.strip()}
SUMMARY

Evaluate using this rubric (score each 1-10):
- section_coverage: covers all first-level sections except Acknowledgements/References/Abstract. Captures the core ideas of each section. 
- concision: each section is concise while maintaining clarity and completeness.
- faithfulness: ideas mentioned in summary have direct references in the original paper; no hallucinations.
- writing_quality: grammar, clarity, coherence.
- overall: weighted holistic score.

Emphasize factual accuracy and coverage over writing quality.

Respond ONLY with strict JSON:
{{
  "arxiv_id": "{arxiv_id}",
  "pdf_url": "{pdf_url}",
  "criteria": [
    {{"name": "section_coverage", "score": <number>, "reason": "<short note>"}},
    {{"name": "concision", "score": <number>, "reason": "<short note>"}},
    {{"name": "faithfulness", "score": <number>, "reason": "<short note>"}},
    {{"name": "writing_quality", "score": <number>, "reason": "<short note>"}}
  ],
  "overall_score": <number>,
  "overall_reason": "<short note>"
}}
"""


def evaluate_summary(arxiv_id: str, summary_text: str) -> Dict:
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    prompt = build_prompt(arxiv_id, pdf_url, summary_text)

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search"}],
        input=prompt,
    )

    raw = response.output_text.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # attempt to salvage JSON if model wrapped text
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end != -1:
            result = json.loads(raw[start:end])
        else:
            raise

    # ensure required fields exist
    result.setdefault("arxiv_id", arxiv_id)
    result.setdefault("pdf_url", pdf_url)
    return result


def evaluate_all() -> List[str]:
    written: List[str] = []
    for fname in os.listdir(SUMMARIES_DIR):
        if not fname.endswith(".txt"):
            continue
        summary_path = os.path.join(SUMMARIES_DIR, fname)
        result_path = os.path.join(RESULTS_DIR, fname.replace(".txt", ".json"))

        # skip existing evaluations
        if os.path.exists(result_path):
            continue

        with open(summary_path, "r", encoding="utf-8") as f:
            summary_text = f.read()

        arxiv_id = filename_to_arxiv_id(fname)
        result = evaluate_summary(arxiv_id, summary_text)

        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        written.append(result_path)
    return written


if __name__ == "__main__":
    saved = evaluate_all()
    print(f"Saved {len(saved)} evaluation(s):")
    for path in saved:
        print(f"- {path}")
