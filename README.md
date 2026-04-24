# Document Insights API

Backend service for asynchronous document processing with rate limiting and caching.

## Tech Stack
- **Python 3.11+**
- **FastAPI** - Web framework
- **MongoDB** - Document storage
- **Redis** - Caching & rate limiting
- **Docker Compose** - Container orchestration

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### Running the Application

```bash
# Start all services
docker-compose up --build

# API available at: http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

## API Endpoints

- `POST /documents` - Submit document for processing
- `GET /documents/{document_id}` - Get document status
- `GET /users/{user_id}/documents` - List user documents
- `GET /health` - Health check

## Architecture


## Testing

```bash
pytest
```

## Design Decisions

