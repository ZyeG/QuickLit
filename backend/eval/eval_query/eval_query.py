import re, os, json
from difflib import SequenceMatcher
# txt file
def extract_titles_from_text(path):
    """
    Extract and write IEEE-style paper titles enclosed in double quotes.
    """
    # Regex: capture text between quotes (non-greedy)
    pattern = r'"(.*?)"'
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    matches = re.findall(pattern, text)

    # append to survey title list
    cleaned = []
    for title in matches:
        t = title.strip().rstrip(",.")            # remove trailing punctuation
        t = re.sub(r'\s+', ' ', t)                # collapse whitespace
        cleaned.append(t)
    return cleaned

# json file
def load_retrieved_titles(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Retrieved JSON not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    titles = []
    for p in data.get("retrieved_papers_initial", []):
        title = p.get("title", "").strip()
        if title:
            titles.append(title)
    if not titles:
        for p in data.get("retrieved_papers_fallback", []):
            title = p.get("title", "").strip()
            if title:
                titles.append(title)
    return titles


def compare_titles_fuzzy(gold_titles, retrieved_titles, threshold=0.85):
    """Fuzzy compare two lists of titles and print matches."""
    matches = []

    for g in gold_titles:
        for r in retrieved_titles:
            score = SequenceMatcher(None, g.lower(), r.lower()).ratio()
            if score >= threshold:
                matches.append((g, r, score))

    print("Matched Pairs:")
    for g, r, s in matches:
        print(f"- GOLD: {g}\n  RETR: {r}\n  SCORE: {s:.3f}\n")
    return matches


import os
import sys
import json
import re
from datetime import datetime

# Assume extract_titles_from_text and load_retrieved_titles and compare_titles_fuzzy exist

def save_output_file(path, gold_list, retrieved_list, matches):
    # Create output directory
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("GOLD TITLES (from survey):\n")
        f.write("-----------------------------\n")
        for t in gold_list:
            f.write(f" - {t}\n")

        f.write("\nRETRIEVED TITLES (system):\n")
        f.write("-----------------------------\n")
        for t in retrieved_list:
            f.write(f" - {t}\n")

        f.write("\nMATCHES:\n")
        f.write("-----------------------------\n")
        for m in matches:
            f.write(f" - Retrieved: {m[0]}\n   Gold:      {m[1]}\n")

    print(f"\n Saved evaluation output → {path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 eval_query.py <./goldlists/survey_text_file.txt> <../app/data/retrieved_json_file.json>")
        sys.exit(1)

    gold_path = sys.argv[1].strip()
    retrieved_path = sys.argv[2].strip()

    # Extract lists
    gold_title_lst = extract_titles_from_text(gold_path)
    retrieved_title_lst = load_retrieved_titles(retrieved_path)

    # Compute matches
    matches = compare_titles_fuzzy(gold_title_lst, retrieved_title_lst)
    print(f"\n{len(matches)} matches found.")

    # Create slug from survey filename
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", os.path.splitext(os.path.basename(gold_path))[0]).strip("_")

    # Save output to file
    save_output_file(os.path.join('./eval_out', slug), gold_title_lst, retrieved_title_lst, matches)

    # print save confirmation: to where
    #print(f"\nSaved evaluation output → {os.path.join('./eval_out', slug + '_<timestamp>.txt')}")






    


    