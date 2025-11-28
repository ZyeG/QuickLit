# QuickLit

## run project with docker

- prereq:
  create `.env` or change `.env.example` to `.env` at root, put openai api key

  ```.env
  OPENAI_API_KEY="YOUR_OPENAI_KEY"
  QDRANT_PORT=6333
  QDRANT_HOST="qdrant"
  ```

- verify individual service runs
  `docker build -t quicklit-frontend ./quicklit-web`
  `docker build -t quicklit-backend ./backend`

- start all services
  `docker compose up --build -d`

- stop & remove all
  `docker compose down -v`

- access frontend:localhost:8080
  & backend: `curl http://localhost:3001/api/health`, expect: `{"status":"ok","openai_api_key_set":true}`

- see service live log: `docker compose logs -f backend`

## Backend APIs

### @app.post("/api/query")

- input param: topic
- expected output:

```
{
  "nums_papers": <int> # how many papers are retrieved
  "papers": [
    {
      "title": "<string>",
      "pdf_url": "<string>",
      "paper_id": "<string>"
    }
  ]
}
```
- test with curl 
`curl -X POST "http://localhost:3001/api/query" \
  -H "Content-Type: application/json" \
  -d '{
        "topic": "Security Risk and Attacks in AI"
      }'`

### @app.post("/api/summary/by-id")
- input param: arxiv paper id
- expected output:
```
{
  "arxiv_id":"<string>",
  "cached":"<string>",
  "summary":"<string>"
}
```
- test with
curl -X POST "http://localhost:3001/api/summary/by-id" \
  -H "Content-Type: application/json" \
  -d '{"arxiv_id": "2405.16506"}'

## Eval
### Topics for Evaluation
Deep Reinforcement Learning for Data Processing and Analytics
Security Risk and Attacks in AI
Graph Retrieval-Augmented Generation for Large Language Models
Machine Learning Approaches and Its Techniques
Edge Computing Systems and Tools

### Eval Query
#### Retrival Relevance
To evaluate relevance of papers retrieved with a topic, compute the relevance scores by cosine similiarity between each paper's abstract and the topic, then compute the mean, median, precision_above_0.4, and top10_precision across all papers, as the overall relevance score for papers retrieved with that topic. 

Evaluated the query results of 4 differnt query approaches: source - prompt version
- Semantic - v1: single prompt (with tool: web search)
- Semantic - v2: pipe (extract concept clusters, buld search queries, acamedic web retrival, rank by relevance)
- Arxiv - v1: single prompt, arxiv only (for pdf), rank by title similarity, no hard limit on number of papers retrieved 
- Arxiv - v2: Cap at 60% similiarty of titles, cap at 30 papers (if fetch more papers), ensure id, title, url match; model matters; also user input topic should be specific e.g. machine learning approaches and its techniques (too broad)

##### eval.py
- `python eval.py`
- loads all query result files from backend/log/query_out/, computes semantic similarity metrics (mean, median, precision, top-10 precision) between each topic and its retrieved papers using the MiniLM embedding model, and saves eval results to backend/eval/results/query_eval/eval.json.

##### compare_results.py
- run with `python compare_results.py mean_similarity` or `python compare_results.py median_similarity`
- loads query eval results (mean or median similarity) for 5 versions of prompts (listed below, in source - version format)
  `semantic-v1: semantic_v1v2_eval_results.json, 
  `semantic-v2: semantic_v1v2_eval_results.json, 
  `arXiv-v1:folder arxiv_v1_results, 
  `arXiv-v2:arxiv_v2_results_eval.json, 
  `arXiv-v3:eval.json. 
and outputs a comparison table in csv: "combined_scores.csv"
- note code for generating semantic-v1, semantic-v2, arXiv-v1, arXiv-v2 reuslts is not included in the repo, they were executed in a notebook, since they are experimental code. 

#### pdf url match & correctness 
manually verfied all papers fetched for each of the 5 example topics have valid pdf urls. 

### Eval Summary
#### LLM Judge based on rubrics
- input: text files from backend/log/summaries
- output: json files in backend/eval/summary_eval/results
- checks: coverage, concision, faithfulness, writing quality, and overall quality—each scored 1–10
