# QuickLit

## run project with docker
- prereq:
create .env at root, put openai api key

- start all services
`docker compose up --build -d`

- stop & remove all
`docker compose down -v`

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

## 
Graph Retrieval-Augmented Generation for Large Language Models

Generative AI Application in Education