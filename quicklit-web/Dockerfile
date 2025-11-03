# frontend/Dockerfile
FROM node:24-bookworm-slim

WORKDIR /app

COPY package*.json ./

RUN npm install

RUN npm install -g serve

COPY . .

RUN npm run build

# Serve build
EXPOSE 8080

CMD ["serve", "-s", "build", "-p", "8080"]
