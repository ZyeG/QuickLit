import json
import feedparser
from openai import OpenAI
import re
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SMITHERY_API_KEY = os.environ["SMITHERY_API_KEY"]
if not OPENAI_API_KEY or not SMITHERY_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY or/and SMITHERY_API_KEY not found in .env.txt")

client = OpenAI(api_key=OPENAI_API_KEY)
os.makedirs("./data", exist_ok=True)

def get_output_path(topic: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.lower()).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"./data/query_mcp_out_{slug}_{timestamp}.json"

# prompt download
# specify path, since mcp server expects path as download/read tool argument

def query_mcp(topic, max_results):
    prompt_retrieval = f"""
        Use the MCP tool 'search_arxiv' from the paper_search server to retrieve papers on: {topic}.

        YOU MUST call the MCP tool to fetch real results.

        For each tool call, use:
        - "query": "{topic}"
        - "max_results": {3* max_results}

        After the tool call completes:

        1. Remove repetitive, duplicate, or irrelevant papers.
        2. For each remaining paper:
        - Extract "title"
        - Extract "pdf_url"
        - Extract "source" (e.g. arxiv, pubmed)
        - If any field is missing, filter out that paper.
        3. Sort all papers by relevance to "{topic}".

        Then output ONLY the following JSON format:

        {{
        "papers": [
            {{
            "title": "Paper Title 1",
            "pdf_url": "url_to_pdf",
            "source": "source_name"
            }}
        ],
        "tool_calls": []
        }}

        Additionally, list **all MCP tool calls you made** in the "tool_calls" field as:

        {{
        "tool_calls": [
            {{
            "tool_name": "search_arxiv",
            "arguments": {{"query": "...", "max_results": ...}},
            "raw_response": {{}}
            }}
        ]
        }}    
    """

    resp = client.responses.create(
        model="gpt-5",
        input=prompt_retrieval,
        tools=[
            {
                "type": "mcp",
                "server_url": (
                    f"https://server.smithery.ai/@openags/paper-search-mcp/mcp?api_key={SMITHERY_API_KEY}"
                ),
                "server_label": "paper_search",
                "server_description": "Search, download pdf, read academic papers",
                "require_approval": "never",
            }
        ],
    )

    # save to output_path
    with open(output_path, "w") as f:
        f.write(resp.output_text)
    return resp.output_text

if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     print("Usage: python query_pipe.py '<research topic>' [max_results]")
    #     sys.exit(1)
    
    topic = "edge computing systems and tools"
    max_results = 20
    output_path = get_output_path(topic)
    query_mcp(topic, max_results)
    print(f"Saved fallback response to {output_path}")