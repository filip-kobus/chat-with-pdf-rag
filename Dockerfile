FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync

COPY . .

RUN mkdir -p data chroma_db

EXPOSE 8000
EXPOSE 8501

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["streamlit", "run", "src/app.py"]