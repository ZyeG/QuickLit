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
    return f"./data/query_single_out_{slug}_{timestamp}.json"


def single_prompt_tool (topic, max_results):
    prompt_retrieval = f"""Find recent papers on{topic} and provide their titles and PDF links for {max_results} results. Ranked by relevance
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
    
    # save response.output_text to ./data
    with open(output_path, "w") as f:
        f.write(response.output_text)

    # return dict with url and papers
    return json.loads(response.output_text)


if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     print("Usage: python query_pipe.py '<research topic>' [max_results]")
    #     sys.exit(1)
    
    topic = "edge computing systems and tools"
    max_results = 20
    output_path = get_output_path(topic)
    single_prompt_tool(topic, max_results)
    print(f"Saved fallback response to {output_path}")
