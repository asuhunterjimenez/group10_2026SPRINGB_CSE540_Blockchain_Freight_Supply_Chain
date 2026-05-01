# Use official Python image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY blockchain/package*.json ./blockchain/

WORKDIR /app/blockchain
RUN npm install

WORKDIR /app

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["sh", "docker/entrypoint.sh"]
