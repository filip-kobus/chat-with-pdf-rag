# Chat with PDF RAG Application

A Retrieval-Augmented Generation (RAG) chatbot that allows you to chat with PDF documents using OpenAI's language models and ChromaDB for local vector storage.

## Features

- **Local Vector Database**: Uses ChromaDB instead of remote Pinecone for local development
- **PDF Processing**: Converts PDF documents to markdown and chunks them for better retrieval
- **Dual Response Mode**: Provides both augmented (with context) and non-augmented responses
- **Persistent Storage**: ChromaDB data persists between container restarts
- **Dockerized**: Easy deployment with Docker and Docker Compose

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key
- PDF files to chat with

## Setup

1. **Clone the repository** (if applicable) or ensure you have all the files in your project directory.

2. **Create a `.env` file** in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   EMBEDDING_MODEL=text-embedding-ada-002
   LLM_MODEL=gpt-3.5-turbo
   ```

3. **Add your PDF files** to the `data/` directory. The application expects these specific files:
   - `ask_1.pdf`
   - `ask_2.pdf`
   - `ask_3.pdf`
   - `ask_4.pdf`

   You can modify the `FILES_NAMES` list in `main.py` to use different PDF files.

## Usage

### Using Docker Compose (Recommended)

1. **Build and run the application**:
   ```bash
   docker-compose up --build
   ```

2. **Interact with the chatbot**: The application will start in interactive mode. You can type your questions and get responses.

3. **Stop the application**: Press `Ctrl+C` or run:
   ```bash
   docker-compose down
   ```

### Using Docker directly

1. **Build the Docker image**:
   ```bash
   docker build -t chat-with-pdf-rag .
   ```

2. **Run the container**:
   ```bash
   docker run -it --rm \
     -e OPENAI_API_KEY=your_api_key_here \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/chroma_db:/app/chroma_db \
     -v $(pwd)/.env:/app/.env:ro \
     chat-with-pdf-rag
   ```

### Running locally (without Docker)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

## How it works

1. **Document Processing**: PDF files are converted to markdown and split into chunks
2. **Vector Storage**: Text chunks are embedded using OpenAI's embedding model and stored in ChromaDB
3. **Query Processing**: When you ask a question:
   - The system searches for relevant chunks using similarity search
   - Provides both a regular response and an augmented response using the retrieved context
4. **Persistence**: ChromaDB stores the vector embeddings locally, so you don't need to reprocess documents on every restart

## Project Structure

```
.
├── main.py                 # Main application code
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image configuration
├── docker-compose.yml     # Docker Compose configuration
├── .dockerignore          # Files to ignore during Docker build
├── .env                   # Environment variables (create this)
├── data/                  # Directory for PDF files
│   ├── ask_1.pdf
│   ├── ask_2.pdf
│   ├── ask_3.pdf
│   └── ask_4.pdf
└── chroma_db/             # ChromaDB storage (created automatically)
```

## Configuration

You can customize the application by modifying these environment variables in your `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `EMBEDDING_MODEL`: OpenAI embedding model (default: `text-embedding-ada-002`)
- `LLM_MODEL`: OpenAI language model (default: `gpt-3.5-turbo`)

## Customization

To use different PDF files:

1. Add your PDF files to the `data/` directory
2. Update the `FILES_NAMES` list in `main.py`
3. Update the `NO_NEEDED_PAGES` dictionary to specify pages to skip for each file

## Troubleshooting

- **ChromaDB issues**: Delete the `chroma_db/` directory to reset the vector database
- **PDF processing errors**: Ensure your PDF files are readable and not password-protected
- **OpenAI API errors**: Check your API key and ensure you have sufficient credits

## Migration from Pinecone

This application has been migrated from Pinecone to ChromaDB for local development. Key changes:

- Removed Pinecone dependencies and API calls
- Added ChromaDB for local vector storage
- Simplified configuration (no need for Pinecone API key or index management)
- Added persistence for vector embeddings
