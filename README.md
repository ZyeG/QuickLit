# QuickLit

## run project with docker

- prereq:
  create `.env` at root, put openai api key

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

- access frontend:localhost:8080 & backend: localhost:3001

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
