import json
import feedparser
from openai import OpenAI
import re
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------
load_dotenv(dotenv_path="./.env.txt")
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not found in .env.txt")

# Command-line topic argument
if len(sys.argv) < 2:
    print("Usage: python3 query_pipe.py \"<research topic>\"")
    sys.exit(1)

USER_INPUT_TOPIC = sys.argv[1].strip()

client = OpenAI(api_key=api_key)

# create a safe identifier for filename
slug = re.sub(r"[^a-zA-Z0-9]+", "_", USER_INPUT_TOPIC.lower()).strip("_")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs("./data", exist_ok=True)
OUTPUT_PATH = f"./data/query_pipe_out_{slug}_{timestamp}.json"


def save_stage(stage_name, content):
    """Save or update a specific stage in the pipeline JSON."""
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data[stage_name] = content

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_stage(stage_name):
    """Read specific stage from pipeline JSON."""
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(stage_name)

# Extract Keywords + Synonyms
prompt_keywords = f"""
Extract keywords directly from this topic:
"{USER_INPUT_TOPIC}"

Then for each keyword, provide two close synonyms or related terms.
Output as valid JSON:
[
  {{"keyword": "<keyword>", "synonyms": ["<syn1>", "<syn2>"]}},
  ...
]
"""

resp1 = client.responses.create(
    model="gpt-4o-mini",
    input=prompt_keywords,
    temperature=0.3,
)

keywords_text = resp1.output[0].content[0].text.strip()
cleaned = re.sub(r"^```(?:json)?|```$", "", keywords_text, flags=re.MULTILINE).strip()
keywords = json.loads(cleaned)
save_stage("keywords", keywords)


# Build Boolean Search Query
prompt_query = f"""
You are a search query builder for academic databases.
Given this JSON of keywords and synonyms:
{json.dumps(keywords, indent=2)}

Create one Boolean search query string that combines all terms with proper quoting and logical operators.
Use parentheses for groups and connect main concept groups with AND.
Example format:
("generative AI" OR "large language model" OR "ChatGPT") AND ("post-secondary education" OR "undergraduate students" OR "university")

Output only the final query string.
"""

resp2 = client.responses.create(
    model="gpt-4o-mini",
    input=prompt_query,
    temperature=0.3,
)

search_query = resp2.output[0].content[0].text.strip()
save_stage("search_query", search_query)


# Generate arXiv API URL
prompt_url = f"""
Given this Boolean search string:
{search_query}

Return ONLY a valid arXiv API URL that queries for these terms, formatted like:
http://export.arxiv.org/api/query?search_query=all:(...)&start=0&max_results=100

Rules:
- Replace spaces with %20 and quotes with %22.
- Wrap groups in parentheses and encode them correctly for URLs.
- Use `all:` before each main concept group.
- Always include &start=0&max_results=100 at the end.
- Output only the URL, no extra text.
"""

resp3 = client.responses.create(
    model="gpt-4o-mini",
    input=prompt_url,
    temperature=0.2,
)

api_url = resp3.output[0].content[0].text.strip()
save_stage("api_url", api_url)


# Retrieve Papers from arXiv
feed = feedparser.parse(api_url)
papers = []

for entry in feed.entries:
    papers.append({
        "title": entry.title.strip(),
        "pdf_link": entry.link.replace("/abs/", "/pdf/"),
    })

save_stage("retrieved_papers", papers)


#  Print Summary
# # ---------------------------------------------------------
# print("\n Pipeline completed successfully!")
# print(f" Topic: {USER_INPUT_TOPIC}")
# print(f"Keywords: {len(keywords)}")
# print(f" Papers found: {len(papers)}")
# print(f" Output saved to: {OUTPUT_PATH}")