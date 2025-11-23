import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

EVAL_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# go up to backend/
BACKEND_DIR = os.path.dirname(BASE_DIR)
# logs directory under backend/
LOG_DIR = os.path.join(BACKEND_DIR, "log", "query_out")   # goes to backend/log/query_out/
EVAL_JSON = os.path.join(BACKEND_DIR, "eval", "results", "query_eval", "eval.json")   # goes to backend/eval/eval.json
def evaluate_one_topic(topic, papers):
    """
    Evaluate similarity between a topic and abstracts of its papers.
    No topic_idx included.
    """

    topic_vec = EVAL_MODEL.encode([topic], convert_to_tensor=True)

    sims = []
    per_paper = []

    for p in papers:
        pid = p["paper_id"]
        title = p["title"]
        abstract = p.get("abstract", "")

        if not abstract:
            sim = 0.0
        else:
            # make title + abstract vector
            abs_vec = EVAL_MODEL.encode([title + " " + abstract], convert_to_tensor=True)
            sim = util.cos_sim(topic_vec, abs_vec).item()

        sims.append(sim)
        per_paper.append({
            "paper_id": pid,
            "title": title,
            "similarity": float(sim)
        })

    sims = np.array(sims)

    mean_sim = float(np.mean(sims)) if len(sims) else 0.0
    median_sim = float(np.median(sims)) if len(sims) else 0.0
    precision_06 = float(np.mean(sims >= 0.4)) if len(sims) else 0.0

    top10_vals = np.array(sorted(sims, reverse=True)[:10])
    top10_precision = float(np.mean(top10_vals >= 0.4)) if len(top10_vals) else 0.0

    return {
        "topic": topic,
        "num_papers": len(papers),
        "mean_similarity": mean_sim,
        "median_similarity": median_sim,
        "precision_above_0.4": precision_06,
        "top10_precision": top10_precision,
        "papers": per_paper
    }


def evaluate_all(query_dir=LOG_DIR, out_path=EVAL_JSON):
    """
    Reads all topic JSON files from query_out/, evaluates each topic,
    prints summary, and saves combined eval results to eval.json.
    NO topic_idx anywhere.
    """

    results = {}

    for fname in os.listdir(query_dir):
        if not fname.endswith(".json"):
            continue

        fpath = os.path.join(query_dir, fname)

        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        topic = data["topic"]
        papers = data.get("papers", [])

        eval_res = evaluate_one_topic(topic, papers)

        # print summary
        print(f"\n=== {topic} ===")
        print("num_papers:", eval_res["num_papers"])
        print("mean_similarity:", eval_res["mean_similarity"])
        print("median_similarity:", eval_res["median_similarity"])
        print("precision_above_0.4:", eval_res["precision_above_0.4"])
        print("top10_precision:", eval_res["top10_precision"])

        results[topic] = eval_res

    # save combined results
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nSaved evaluation to:", out_path)
    return results

if __name__ == "__main__":
    evaluate_all()