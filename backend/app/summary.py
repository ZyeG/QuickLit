# summarize a paper w/ gpt-4o-mini, if paper too long (page>~20), or gpt call timeout (>60s), extract and return abstract instead
import re, requests, os, signal
from openai import OpenAI
from dotenv import load_dotenv

# Setup
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)
os.makedirs("./data", exist_ok=True)

MODEL = "gpt-4o-mini"
MAX_FILE_BYTES = 1000_000   # cost cap (~20 pages)
TIMEOUT_SECONDS = 60      # timeout for slow API calls

# ---------------------------------------------------------
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Summarization timed out after 60s.")

signal.signal(signal.SIGALRM, timeout_handler)

#  Helpers
from bs4 import BeautifulSoup

def fetch_abstract(pdf_url: str) -> str:
    abs_url = re.sub(r"/pdf/", "/abs/", pdf_url).split(".pdf")[0]
    try:
        html = requests.get(abs_url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        block = soup.find("blockquote", {"class": lambda c: c and "abstract" in c})
        if block:
            return block.get_text(strip=True).replace("Abstract:", "").strip()
    except Exception:
        pass
    return "Abstract not available."

def summarize_or_abstract(pdf_url: str):
    """Summarize if small enough, else abstract; abort if it runs too long."""
    try:
        size = int(requests.head(pdf_url, timeout=10).headers.get("Content-Length", 0))
    except Exception:
        size = 0

    if size > MAX_FILE_BYTES:
        print(f"PDF {size/1024:.1f} KB > {MAX_FILE_BYTES/1024:.1f} KB – returning abstract.")
        return fetch_abstract(pdf_url)

    try:
        # Start timeout timer
        signal.alarm(TIMEOUT_SECONDS)

        print("Summarizing with gpt-4o-mini...")
        resp = client.responses.create(
            model=MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Summarize the paper in ≤ 500 words, "
                                "including methods, datasets, metrics, and findings."
                            ),
                        },
                        {"type": "input_file", "file_url": pdf_url},
                    ],
                }
            ],
        )
        signal.alarm(0)  # cancel timer if finished
        return resp.output_text

    except TimeoutException as e:
        print(f"{e}")
        return fetch_abstract(pdf_url)
    except Exception as e:
        print(f"Summarization failed: {e}")
        return fetch_abstract(pdf_url)
