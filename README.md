# Chat with PDF RAG Application

An application that enables conversations with PDF documents using RAG (Retrieval Augmented Generation) technology.

![alt text](README/main-view.png)

## Features

- **PDF Document Upload** - Upload and index PDF documents for questioning
- **Chat with Documents** - Ask questions and get answers based on document content
- **Session Management** - Maintains conversation history across sessions
- **Development and Production Modes** - Different configurations for development and production environments
- **Responsive Interface** - Adapts to different screen sizes

## Quick Start

### Development Mode

```bash
# Install dependencies
uv sync

# Run the Streamlit application
streamlit run src/app.py
```

The application will be available at: http://localhost:8501

### Production Mode

```bash
# Run all services (Redis, ChromaDB, Application)
docker-compose up --build
# or using podman
podman compose up --build
```


## How It Works

### Development Mode
- JSON file-based session manager
- Local ChromaDB storage
- No external service dependencies

### Production Mode
- Redis backend for session management
- ChromaDB as external service
- All services run in Docker containers

## Ports

- **8501** - Streamlit Application
- **6379** - Redis (production mode only)
- **8000** - ChromaDB (production mode only)

## Technologies

- **Python 3.12+** - Programming language
- **Streamlit** - Web application framework
- **LangChain** - Framework for working with language models
- **ChromaDB** - Vector database
- **Redis** - Session storage and caching (production)
- **OpenAI API** - Language models and embeddings
- **UV** - Python dependency management
- **Docker/podman** - Containerization (production)

## API Configuration

The application requires an OpenAI API key which can be provided either:
- Through the web interface (recommended for development)
- As an environment variable `OPENAI_API_KEY`

## Testing

```bash
# Test development mode
streamlit run src/app.py

# Test production mode (requires Docker)
docker-compose up --build
```
