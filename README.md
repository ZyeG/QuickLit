# QuickLit

## run project with docker
- prereq:
create `/backend/.env.txt` to store opanai API key: `OPENAI_API_KEY=your_key_no_quotes`

- verify individual service runs
`docker build -t quicklit-frontend ./quicklit-web`
`docker build -t quicklit-frontend ./quicklit-web`

- start all services
`docker compose up --build -d`

- stop & remove all
`docker compose down`

- access frontend:localhost:8080 
& backend: `curl http://localhost:3001`, expect: {"detail":"Not Found"}


