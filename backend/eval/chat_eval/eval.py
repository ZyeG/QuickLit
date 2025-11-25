"""
LLM-driven evaluation of chat histories against a source paper.

The module builds a rubric, renders a prompt that includes the paper text,
the full chat history, and asks a model to score each criterion.
"""

import json
import os, sys
import dotenv
dotenv.load_dotenv()
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
from typing import Any, Dict, Iterable, List, Sequence

from openai import OpenAI
from app.pdf_parser import get_pdf_raw_content
# Expect the same API key setup as the main app.
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)
DEFAULT_EVAL_MODEL = os.environ.get("EVAL_MODEL_NAME", "gpt-5")

# ---- Rubric -----------------------------------------------------------------
# Weights sum to 1.0. Scores are 0-5 integers unless otherwise specified.
RUBRIC: List[Dict[str, Any]] = [
    {
        "id": "grounding",
        "name": "Grounded accuracy",
        "weight": 0.35,
        "focus": "Responses must align with the provided paper text; penalize hallucinations and contradictions.",
        "levels": {
            "5": "All claims trace directly to the paper; no hallucinations or conflicts.",
            "3": "Mostly grounded with minor speculation or missing citations.",
            "0": "Major inaccuracies or invented content relative to the paper.",
        },
    },
    {
        "id": "responsiveness",
        "name": "Responsiveness",
        "weight": 0.20,
        "focus": "Addresses the user's questions and context without deflection or off-topic content.",
        "levels": {
            "5": "Direct, complete answers to the user's asks.",
            "3": "Partial coverage or noticeable gaps.",
            "0": "Ignores or misinterprets the user's intent.",
        },
    },
    {
        "id": "evidence",
        "name": "Evidence and citation",
        "weight": 0.15,
        "focus": "Uses specifics from the paper (figures, data, quotes) and cites them clearly.",
        "levels": {
            "5": "Consistently cites or quotes concrete details from the paper.",
            "3": "Some evidence is used but is vague or sparse.",
            "0": "No evidence or fabricated references.",
        },
    },
    {
        "id": "reasoning",
        "name": "Reasoning quality",
        "weight": 0.15,
        "focus": "Logical coherence, correct chain-of-thought, and faithful summary of nuanced points.",
        "levels": {
            "5": "Coherent, logically sound reasoning that preserves nuance.",
            "3": "Reasonable but shallow or slightly disorganized reasoning.",
            "0": "Illogical, inconsistent, or misleading reasoning.",
        },
    },
    {
        "id": "communication_safety",
        "name": "Communication and safety",
        "weight": 0.15,
        "focus": "Clear communication, calibrates uncertainty, avoids unsafe or speculative claims.",
        "levels": {
            "5": "Clear, cautious wording with honest uncertainty and no unsafe content.",
            "3": "Generally clear but with occasional overclaiming.",
            "0": "Speculative, unsafe, or overconfident statements.",
        },
    },
]

EVAL_SYSTEM_PROMPT = """
You are an impartial judge scoring a research assistant conversation.
Be strict but fair, reward grounding in the provided paper, and penalize hallucinations.
Use the rubric as written; do not invent extra criteria.
"""


def render_rubric(rubric: Sequence[Dict[str, Any]] = RUBRIC) -> str:
    """Human-readable rubric block embedded in the evaluation prompt."""
    lines: List[str] = []
    for idx, item in enumerate(rubric, start=1):
        lines.append(
            f"{idx}. {item['name']} ({item['weight']*100:.0f}% weight) - {item['focus']}"
        )
        levels = item.get("levels") or {}
        if levels:
            parts = [f"{k}/5: {v}" for k, v in sorted(levels.items(), key=lambda kv: float(kv[0]))]
            lines.append("   Scoring guide: " + "; ".join(parts))
    return "\n".join(lines)


def render_chat_history(chat_history: Iterable[Dict[str, str]]) -> str:
    """Serialize chat turns into a concise, model-friendly text block."""
    rendered: List[str] = []
    for turn in chat_history:
        if isinstance(turn, dict):
            role = turn.get("role", "user")
            content = turn.get("content", "")
        elif isinstance(turn, (list, tuple)) and len(turn) >= 2:
            role, content = turn[0], turn[1]
        else:
            role, content = "user", str(turn)
        rendered.append(f"{role.upper()}: {content}")
    return "\n".join(rendered)


def build_evaluation_prompt(
    paper_text: str,
    chat_history: Iterable[Dict[str, str]],
    rubric: Sequence[Dict[str, Any]] = RUBRIC,
) -> str:
    """Combine rubric, paper text, and chat history into a single evaluation prompt."""
    rubric_block = render_rubric(rubric)
    chat_block = render_chat_history(chat_history)
    prompt = f"""
You are grading how well the assistant handled this conversation about the paper.

Rubric (0-5 integer scores, apply weights exactly): 
{rubric_block}

Paper text (verbatim source of truth):
<<<PAPER>>>
{paper_text}
<<<END PAPER>>>

Chat history (chronological):
<<<CHAT>>>
{chat_block}
<<<END CHAT>>>

Scoring instructions:
- Use the paper as ground truth. Unsupported claims should score near 0 on grounding/evidence.
- Prefer concise rationales (1-3 sentences) and cite lines or sections when possible.
- Compute a weighted score: sum(score_i * weight_i) using the rubric weights.
- If information is missing from the paper, reward honesty over speculation.

Return ONLY a JSON object with this schema:
{{
  "scores": [
    {{"criterion": "<id>", "score": 0-5, "justification": "brief reason referencing the paper"}}
  ],
  "weighted_score": <float 0-5>,
  "overall_comment": "one short paragraph synthesizing the result",
  "issues": ["hallucination" | "coverage" | "reasoning" | "safety" | "other"]
}}
"""
    return prompt.strip()


def _clean_json_output(raw_text: str) -> str:
    """Remove Markdown fences the model might return."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    return cleaned


def compute_weighted_score(
    scores: Sequence[Dict[str, Any]],
    rubric: Sequence[Dict[str, Any]] = RUBRIC,
) -> float:
    weights = {item["id"]: float(item["weight"]) for item in rubric}
    total = 0.0
    for entry in scores:
        crit = entry.get("criterion")
        score = float(entry.get("score", 0))
        weight = weights.get(crit, 0.0)
        total += weight * score
    return total


def load_json_utf8(path: str) -> Any:
    """Load a JSON file with UTF-8 encoding regardless of OS defaults."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_chat_history(
    paper_text: str,
    chat_history: Iterable[Dict[str, str]],
    model: str | None = None,
    rubric: Sequence[Dict[str, Any]] = RUBRIC,
) -> Dict[str, Any]:
    """
    Run the LLM judge. Returns raw text, parsed JSON (best-effort), and weighted score.
    """
    prompt = build_evaluation_prompt(paper_text, chat_history, rubric)
    model_name = model or DEFAULT_EVAL_MODEL

    response = client.responses.create(
        model=model_name,
        instructions=EVAL_SYSTEM_PROMPT,
        input=prompt,
    )

    raw_output = response.output_text
    cleaned = _clean_json_output(raw_output)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = {"parse_error": "Could not decode JSON", "raw_output": raw_output}

    if isinstance(parsed, dict) and "scores" in parsed and "weighted_score" not in parsed:
        parsed["weighted_score"] = compute_weighted_score(parsed["scores"], rubric)

    return {
        "raw_output": raw_output,
        "parsed": parsed,
    }


if __name__ == "__main__":
    # Minimal smoke test stub; replace with real paper text and chat data.
    # sample_paper = "Abstract: Example paper text about a new model for neural ranking."
    # sample_chat = [
    #     {"role": "user", "content": "What is the main contribution?"},
    #     {"role": "assistant", "content": "It proposes a neural ranking architecture with better recall."},
    # ]
    # result = evaluate_chat_history(sample_paper, sample_chat)
    # print(json.dumps(result, indent=2))
    # print(get_pdf_raw_content("https://arxiv.org/pdf/2406.19226.pdf")[:500])

    # Test 1
    # paper = get_pdf_raw_content("https://arxiv.org/pdf/2406.19226.pdf")
    # chat = load_json_utf8("./chat_history/11-25_2-papers.json")
    # result = evaluate_chat_history(paper, chat)
    # out_path = "./eval_history/11-25-eval.json"
    # with open(out_path, "w", encoding="utf-8") as f:
    #     json.dump(result, f, indent=2, ensure_ascii=False)

    # Test 2
    # paper_urls = ["https://arxiv.org/pdf/2508.00717.pdf",
    #               "https://arxiv.org/pdf/2404.10551.pdf",
    #               "https://arxiv.org/pdf/2402.01659.pdf",
    #               "https://arxiv.org/pdf/2406.01930.pdf",
    #               "https://arxiv.org/pdf/2403.19245.pdf",
    #               "https://arxiv.org/pdf/2407.05810.pdf",
    #               "https://arxiv.org/pdf/2412.02653.pdf",
    #               "https://arxiv.org/pdf/2502.07401.pdf",
    #               "https://arxiv.org/pdf/2503.05760.pdf",
    #               "https://arxiv.org/pdf/2505.24126.pdf",
    #               "https://arxiv.org/pdf/2305.18616.pdf",
    #               "https://arxiv.org/pdf/2304.14993.pdf",
    #               "https://arxiv.org/pdf/2309.03087.pdf",
    #               "https://arxiv.org/pdf/2305.18617.pdf",
    #               "https://arxiv.org/pdf/2305.00290.pdf",
    #               "https://arxiv.org/pdf/2504.08846.pdf",
    #               "https://arxiv.org/pdf/2502.09651.pdf"]
    # papers = [get_pdf_raw_content(url) for url in paper_urls]
    # paper = "\n\n\n".join(papers)
    # chat = load_json_utf8("./chat_history/11-25-multi-papers_0.json")
    # result = evaluate_chat_history(paper, chat)
    # out_path = "./eval_history/11-25-multi-papers-eval.json"
    # with open(out_path, "w", encoding="utf-8") as f:
    #     json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Test 3
    # paper = get_pdf_raw_content("https://arxiv.org/pdf/2403.19245.pdf")
    # chat = load_json_utf8("./chat_history/11-25-multi-papers_1.json")
    # result = evaluate_chat_history(paper, chat)
    # out_path = "./eval_history/11-25-multi-papers-1-eval.json"
    # with open(out_path, "w", encoding="utf-8") as f:
    #     json.dump(result, f, indent=2, ensure_ascii=False)

    pass
