import json
import feedparser
from openai import OpenAI
import re
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)
os.makedirs("./data", exist_ok=True)

def get_output_path(topic: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.lower()).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"./data/query_pipe_out_{slug}_{timestamp}.json"


def save_stage(output_path: str, stage_name: str, content):
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data[stage_name] = content
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_concepts(topic: str):
    prompt = f"""
    Extract the key **concept clusters** directly from this research topic (use exact words/phrases):

    "{topic}"

    Each cluster should represent a coherent research concept
    (e.g., "retrieval-augmented generation", "large language models", "education").
    For each concept, list 2–3 synonyms or related expressions (including acronyms if applicable).

    Output valid JSON:
    [
      {{"concept": "<main phrase>", "synonyms": ["<syn1>", "<syn2>", ...]}},
      ...
    ]

    Ensure each concept phrase is meaningful (avoid single adjectives or trivial words).
    """
    resp = client.responses.create(model="gpt-4o-mini", input=prompt, temperature=0.3)
    text = resp.output[0].content[0].text.strip()
    cleaned = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    clusters = json.loads(cleaned)

    # Filter trivial or single-word concepts
    clusters = [c for c in clusters if len(c.get("concept", "").split()) > 1]
    return clusters


def build_boolean_query(concepts):
    prompt = f"""
    You are a professional academic search-query builder.

    Given these concept clusters and synonyms:
    {json.dumps(concepts, indent=2)}

   Create one Boolean search query string that combines all terms with proper quoting and logical operators.
    Use parentheses for groups and connect main concept groups with AND.
    Example format:
    ("generative AI" OR "large language model" OR "ChatGPT") AND ("post-secondary education" OR "undergraduate students" OR "university")

    Output only the final query string.
    """
    resp = client.responses.create(model="gpt-4o-mini", input=prompt, temperature=0.3)
    return resp.output[0].content[0].text.strip()


def build_arxiv_url(boolean_query: str, max_results: int = 10) -> str:
    """
    Use an LLM to construct a correctly URL-encoded arXiv API query
    from a given Boolean search string.

    Example:
        boolean_query = '("retrieval augmented generation" OR "RAG") AND ("large language models" OR "LLMs")'
        url = build_arxiv_url(boolean_query, 20)
        print(url)
        # -> http://export.arxiv.org/api/query?search_query=all:%28%28%22retrieval+augmented+generation%22+OR+%22RAG%22%29+AND+%28%22large+language+models%22+OR+%22LLMs%22%29%29&start=0&max_results=20
    """

    prompt = f"""
    Given this Boolean search string:
    {boolean_query}

    Return ONLY a valid arXiv API URL that queries for these terms, formatted like:
    http://export.arxiv.org/api/query?search_query=all:(...)&start=0&max_results={max_results}

    Rules:
    - Replace spaces with %20 and quotes with %22.
    - Wrap groups in parentheses and encode them correctly for URLs.
    - Use `all:` before each main concept group.
    - Always include &start=0&max_results={max_results} at the end.
    - Output only the URL, no extra text.
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0.2,
    )

    # Extract raw text
    out_url = response.output[0].content[0].text.strip()

    # Defensive cleanup: remove markdown fences or extra formatting
    out_url = re.sub(r"^```(?:text|url)?|```$", "", out_url, flags=re.MULTILINE).strip()

    return out_url

def retrieve_papers(api_url: str):
    feed = feedparser.parse(api_url)
    return [
        {"title": e.title.strip(), "pdf_url": e.link.replace("/abs/", "/pdf/"), "paper_id": e.id.split("/")[-1]}
        for e in feed.entries
    ] # list of dicts

# Fallback: Simple query with user input
def single_prompt_tool (topic, max_results):
    prompt_retrieval = f"""Find recent papers on {topic} and provide their titles and PDF links for {max_results} results. Ranked by relevance
    Output json with format:
    {{
      "papers": [
        {{
          "title": "Paper Title 1",
          "pdf_url": "https://arxiv.org/pdf/xxxx.xxxxx.pdf"
          "paper_id": "xxxx.xxxxx"
        }},
        ...
      ]
    }}
    """
    response = client.responses.create(
        model="gpt-5",
        tools=[{"type": "web_search"}],
        input = prompt_retrieval)
    
    # return dict with url and papers
    return json.loads(response.output_text) # dict of papers

def run_pipeline(topic: str, max_results: int = 20):
    output_path = get_output_path(topic)
    print(f"Starting pipeline for topic: {topic}")

    # 1. Extract Concepts
    concepts = extract_concepts(topic)
    save_stage(output_path, "concept_clusters", concepts)
    print(f"Extracted {len(concepts)} concept clusters")

    # 2. Build Boolean Query
    boolean_query = build_boolean_query(concepts)
    save_stage(output_path, "boolean_query", boolean_query)
    print(f"Built Boolean query: {boolean_query}")

    # 3. Generate API URL
    api_url = build_arxiv_url(boolean_query, max_results)
    save_stage(output_path, "api_url", api_url)
    print("Generated API URL")

    # 4. Retrieve Papers
    papers = retrieve_papers(api_url) # list of dicts
    if papers and len(papers) == max_results:
        save_stage(output_path, "retrieved_papers_initial", papers)
        print(f"Retrieved {len(papers)} papers")
    else:
        print("No (fewer) papers found — retrying fallback...")
        single_out = single_prompt_tool(topic, max_results)
        save_stage(output_path, "retrieved_papers_fallback", single_out["papers"])
        papers = single_out["papers"] # list of dicts
        print(f"Fallback retrieved {len(single_out['papers'])} papers")

    print(f"Output saved to: {output_path}")

    # return papers
    return papers # list of dicts [{"title":..., "pdf_link":..., "paper_id":...}, ...]
    # json.loads(response.output_text); 
    # return [
    #     {"title": e.title.strip(), "pdf_link": e.link.replace("/abs/", "/pdf/"), "paper_id": e.id.split("/")[-1]}
    #     for e in feed.entries
    # ]

if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     print("Usage: python query_pipe.py '<research topic>' [max_results]")
    #     sys.exit(1)

    topic = "Predictive maintenance models using sensor fusion and deep learning for industrial equipment monitoring"
    max_results = 20

    run_pipeline(topic, max_results)