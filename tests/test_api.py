"""
Integration tests for API endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns API info"""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Document Insights API"
    assert "docs" in data


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_submit_document_success(client: AsyncClient):
    """Test successful document submission"""
    response = await client.post(
        "/documents",
        json={
            "user_id": "test_user",
            "title": "Test Document",
            "content": "This is test content for the document"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "test_user"
    assert data["title"] == "Test Document"
    assert data["status"] == "queued"
    assert "document_id" in data


@pytest.mark.asyncio
async def test_submit_document_missing_field(client: AsyncClient):
    """Test document submission fails with missing field"""
    response = await client.post(
        "/documents",
        json={
            "user_id": "test_user",
            "title": "Test Document"
            # Missing content
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_document_invalid_data(client: AsyncClient):
    """Test document submission fails with invalid data"""
    response = await client.post(
        "/documents",
        json={
            "user_id": "test_user",
            "title": "",  # Empty title
            "content": "Content"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_document_by_id(client: AsyncClient):
    """Test retrieving document by ID"""
    # First create a document
    create_response = await client.post(
        "/documents",
        json={
            "user_id": "test_user",
            "title": "Test Document",
            "content": "Test content"
        }
    )
    
    document_id = create_response.json()["document_id"]
    
    # Then retrieve it
    get_response = await client.get(f"/documents/{document_id}")
    
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["document_id"] == document_id
    assert data["title"] == "Test Document"


@pytest.mark.asyncio
async def test_get_nonexistent_document(client: AsyncClient):
    """Test retrieving non-existent document returns 404"""
    response = await client.get("/documents/507f1f77bcf86cd799439011")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_user_documents(client: AsyncClient):
    """Test listing user documents"""
    # Create multiple documents
    for i in range(3):
        await client.post(
            "/documents",
            json={
                "user_id": "list_test_user",
                "title": f"Document {i}",
                "content": f"Content {i}"
            }
        )
    
    # List documents
    response = await client.get("/users/list_test_user/documents")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["documents"]) >= 3
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_user_documents_pagination(client: AsyncClient):
    """Test document listing pagination"""
    response = await client.get(
        "/users/list_test_user/documents",
        params={"page": 1, "page_size": 2}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 2


@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient):
    """Test rate limiting blocks 4th request"""
    user_id = "rate_limit_test_user"
    
    # Submit 3 documents (should succeed)
    for i in range(3):
        response = await client.post(
            "/documents",
            json={
                "user_id": user_id,
                "title": f"Doc {i}",
                "content": f"Content {i}"
            }
        )
        assert response.status_code == 201
    
    # 4th should be rate limited
    response = await client.post(
        "/documents",
        json={
            "user_id": user_id,
            "title": "Doc 4",
            "content": "Content 4"
        }
    )
    
    assert response.status_code == 429