import json
import glob
import os
import pandas as pd
import sys
# read metric from command line args, default to mean_similarity
if len(sys.argv) > 1:
    METRIC = sys.argv[1]
else:
    METRIC = "mean_similarity"   # default

print(f"Using metric: {METRIC}")

# resolve results files paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
ARXIV_V1_DIR = os.path.join(RESULTS_DIR, "arxiv_v1_results")

SEMANTIC_FILE = os.path.join(RESULTS_DIR, "semantic_v1v2_eval_results.json")
ARXIV_V2_FILE = os.path.join(RESULTS_DIR, "eval.json")

# load results files 
with open(SEMANTIC_FILE, "r") as f:
    semantic = json.load(f)

with open(ARXIV_V2_FILE, "r") as f:
    arxiv_v2 = json.load(f)

arxiv_v1 = {}

for path in glob.glob(os.path.join(ARXIV_V1_DIR, "*_eval.json")):
    fname = os.path.basename(path)
    topic = fname.replace("_eval.json", "")

    with open(path, "r") as f:
        data = json.load(f)

    arxiv_v1[topic] = data.get("mean_similarity", None)

# combine all results
rows = []

for topic in semantic.keys():
    row = {"topic": topic}

    # semantic scores
    row["semantic_v1"] = semantic[topic]["v1"]["mean_similarity"]
    row["semantic_v2"] = semantic[topic]["v2"]["mean_similarity"]

    # match arxiv_v1 filename naming convention
    normalized_topic = topic.lower().replace(" ", "_")
    row["arxiv_v1"] = arxiv_v1.get(normalized_topic)

    # arxiv_v2 score
    row["arxiv_v2"] = arxiv_v2.get(topic, {}).get("mean_similarity")

    rows.append(row)

# output csv
df = pd.DataFrame(rows)

csv_path = os.path.join(RESULTS_DIR, "combined_scores.csv")

df.to_csv(csv_path, index=False)

print("\n✓ Combined score tables saved:")
print(" -", csv_path)

print("\nPreview:")
print(df)