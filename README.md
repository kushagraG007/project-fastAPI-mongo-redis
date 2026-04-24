markdown# Document Insights API

Backend service for asynchronous document processing with rate limiting and content-based caching.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development/testing)

### Running the Application

```bash
# Clone the repository
git clone 
cd document-insights-api

# Start all services
docker-compose up --build

# API will be available at:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

### Stopping the Application

```bash
# Stop services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

---

## 📚 API Documentation

### Interactive Documentation

Visit http://localhost:8000/docs for Swagger UI (interactive API documentation).

### Endpoints

#### 1. Submit Document
**POST** `/documents`

Submit a document for asynchronous processing.

**Request Body:**
```json
{
  "user_id": "user_123",
  "title": "Q4 Sales Report",
  "content": "Document content here..."
}
```

**Response (201 Created):**
```json
{
  "document_id": "507f1f77bcf86cd799439011",
  "user_id": "user_123",
  "title": "Q4 Sales Report",
  "status": "queued",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "summary": null,
  "error_message": null
}
```

**Rate Limit:** Maximum 3 active jobs (queued + processing) per user.

**Response (429 Too Many Requests):**
```json
{
  "detail": "Rate limit exceeded: max 3 active jobs"
}
```

---

#### 2. Get Document Status
**GET** `/documents/{document_id}`

Retrieve document status and summary (if completed).

**Response (200 OK):**
```json
{
  "document_id": "507f1f77bcf86cd799439011",
  "user_id": "user_123",
  "title": "Q4 Sales Report",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:25Z",
  "summary": "Document Summary: 'Q4 Sales Report'...",
  "error_message": null
}
```

**Possible statuses:**
- `queued` - Waiting for processing
- `processing` - Currently being processed
- `completed` - Processing successful
- `failed` - Processing failed

**Response (404 Not Found):**
```json
{
  "detail": "Document not found"
}
```

---

#### 3. List User Documents
**GET** `/users/{user_id}/documents`

List all documents for a user with pagination.

**Query Parameters:**
- `page` (optional): Page number, default: 1
- `page_size` (optional): Items per page, default: 10, max: 100
- `status` (optional): Filter by status (queued, processing, completed, failed)

**Example:**
GET /users/user_123/documents?page=1&page_size=10&status=completed

**Response (200 OK):**
```json
{
  "documents": [
    {
      "document_id": "507f1f77bcf86cd799439011",
      "user_id": "user_123",
      "title": "Q4 Sales Report",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:25Z",
      "summary": "...",
      "error_message": null
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

---

#### 4. Health Check
**GET** `/health`

Check service health status.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "services": {
    "mongodb": "connected",
    "redis": "connected"
  }
}
```

---

## 🧪 Testing

### Run Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Test Coverage

Tests cover:
- API endpoints (create, get, list)
- Rate limiting
- Caching
- Validation
- Error handling
- Pagination

---

## 🏗️ Tech Stack

- **FastAPI** - Web framework
- **MongoDB** - Document storage
- **Redis** - Caching & rate limiting
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation
- **Docker** - Containerization

---

## 📁 Project Structure
document-insights-api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models/
│   │   └── document.py      # Pydantic models
│   ├── routers/
│   │   └── documents.py     # API endpoints
│   ├── services/
│   │   ├── document_service.py
│   │   ├── cache_service.py
│   │   └── rate_limiter.py
│   └── database/
│       ├── mongodb.py       # MongoDB connection
│       └── redis.py         # Redis connection
├── worker/
│   └── processor.py         # Background worker
├── tests/
│   ├── test_api.py
│   ├── test_models.py
│   └── test_services.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md

---

## 🔧 Configuration

Environment variables (set in `.env` file):

```bash
# MongoDB
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB_NAME=document_insights

# Redis
REDIS_URL=redis://redis:6379
REDIS_CACHE_TTL=3600

# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Rate Limiting
MAX_ACTIVE_JOBS_PER_USER=3

# Worker
WORKER_POLL_INTERVAL=2
WORKER_MIN_PROCESS_TIME=10
WORKER_MAX_PROCESS_TIME=30
WORKER_FAILURE_RATE=0.1
```

---

## 🐛 Troubleshooting

### Issue: Docker services won't start

**Solution:**
```bash
docker-compose down -v
docker-compose up --build
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Change API_PORT in .env file or docker-compose.yml
# Or stop the process using port 8000
```

### Issue: Tests failing

**Solution:**
```bash
# Make sure Docker is running
docker-compose up -d

# Redis and MongoDB must be accessible at localhost
```

---

## 📝 Example Usage

### Using cURL

```bash
# Submit a document
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "title": "My Document",
    "content": "Document content here"
  }'

# Get document status
curl http://localhost:8000/documents/{document_id}

# List user documents
curl "http://localhost:8000/users/user_123/documents?page=1&page_size=10"

# Health check
curl http://localhost:8000/health
```

### Using Python

```python
import requests

# Submit document
response = requests.post(
    "http://localhost:8000/documents",
    json={
        "user_id": "user_123",
        "title": "My Document",
        "content": "Document content"
    }
)
document_id = response.json()["document_id"]

# Check status
status = requests.get(f"http://localhost:8000/documents/{document_id}")
print(status.json())
```

---

## 📦 Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Docker services
docker-compose up mongodb redis

# Run API locally
uvicorn app.main:app --reload

# Run worker locally
python -m worker.processor
```

---

## 🚀 Features

- ✅ Asynchronous document processing
- ✅ Per-user rate limiting (max 3 concurrent jobs)
- ✅ Content-based caching (duplicate content returns cached result)
- ✅ Pagination support for document listing
- ✅ Status filtering
- ✅ Auto-generated API documentation
- ✅ Health check endpoint
- ✅ Comprehensive test suite

---

## 📄 License

MIT License