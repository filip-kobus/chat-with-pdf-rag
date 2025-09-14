# Chat with PDF RAG Application

Aplikacja umożliwiająca prowadzenie konwersacji z dokumentami PDF przy użyciu technologii RAG (Retrieval Augmented Generation).

## Tryby działania

Aplikacja obsługuje dwa tryby działania, wybierane na podstawie zmiennej środowiskowej `APP_ENV`:

### Development Mode (`APP_ENV=development`)
- Menedżer sesji oparty na pliku JSON
- ChromaDB zapisuje dane w lokalnym systemie plików
- Brak zależności na zewnętrzne serwisy

### Production Mode (`APP_ENV=production`)
- Redis jako backend dla menedżera sesji
- ChromaDB jako zewnętrzny serwis
- Wszystkie serwisy działają w kontenerach Docker

## Uruchomienie

### Tryb Development

#### Lokalnie (Streamlit)
```bash
# Ustaw zmienną środowiskową
$env:APP_ENV="development"

# Zainstaluj zależności
uv sync

# Uruchom aplikację Streamlit
uv run streamlit run streamlit/app.py
```

#### Lokalnie (Konsola)
```bash
# Ustaw zmienną środowiskową
$env:APP_ENV="development"

# Uruchom skrypt konsolowy
uv run python main.py
```

#### Docker (development)
```bash
# Użyj pliku docker-compose dla trybu development
docker-compose -f docker-compose.dev.yml up --build

# Aplikacja będzie dostępna na: http://localhost:8501
```

### Tryb Production

```bash
# Uruchom wszystkie serwisy (Redis, ChromaDB, Aplikacja)
docker-compose up --build

# Aplikacja będzie dostępna na: http://localhost:8501
```

## Porty

- **8501** - Aplikacja Streamlit
- **6379** - Redis (tylko w trybie production)
- **8000** - ChromaDB (tylko w trybie production)

## Struktura projektu

- `factories.py` - Fabryki dla różnych implementacji serwisów
- `config.py` - Konfiguracja globalna
- `main.py` - Skrypt konsolowy
- `streamlit/` - Aplikacja webowa Streamlit
- `docker-compose.yml` - Konfiguracja production
- `docker-compose.dev.yml` - Konfiguracja development
- `Dockerfile` - Kontener dla skryptu konsolowego
- `Dockerfile.streamlit` - Kontener dla aplikacji Streamlit

## Zmienne środowiskowe

### Podstawowe
- `APP_ENV` - tryb działania (`development` / `production`)
- `OPENAI_API_KEY` - klucz API OpenAI
- `EMBEDDING_MODEL` - model embeddings (domyślnie: `text-embedding-ada-002`)
- `LLM_MODEL` - model LLM (domyślnie: `gpt-3.5-turbo`)

### Redis (production)
- `REDIS_HOST` - host Redis (domyślnie: `redis`)
- `REDIS_PORT` - port Redis (domyślnie: `6379`)
- `REDIS_DB` - baza danych Redis (domyślnie: `0`)

### ChromaDB (production)
- `CHROMADB_HOST` - host ChromaDB (domyślnie: `chromadb`)
- `CHROMADB_PORT` - port ChromaDB (domyślnie: `8000`)

### Development
- `SESSION_MANAGER_JSON` - ścieżka do pliku JSON z sesjami
- `CHROMA_DB_PATH` - ścieżka do lokalnej bazy ChromaDB

## Testowanie

```bash
# Test fabryki w trybie development
$env:APP_ENV="development"
uv run python -c "from factories import ServiceFactory; print('Development mode OK')"

# Test fabryki w trybie production (wymaga uruchomienia Redis i ChromaDB)
$env:APP_ENV="production"
uv run python -c "from factories import ServiceFactory; print('Production mode OK')"
```
