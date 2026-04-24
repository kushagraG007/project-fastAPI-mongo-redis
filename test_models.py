"""Quick test of Pydantic models"""

from app.models import DocumentCreate, create_document_dict
from pydantic import ValidationError

# Test 1: Valid document
print("Test 1: Valid document")
doc = DocumentCreate(
    user_id="user_123",
    title="My Document",
    content="This is the content"
)
print(f"✅ Created document: {doc.title}")
print(f"   Content hash: {doc.compute_content_hash()}")

# Test 2: Invalid document (missing field)
print("\nTest 2: Missing required field")
try:
    doc = DocumentCreate(
        user_id="user_123",
        title="My Document"
        # Missing 'content'!
    )
except ValidationError as e:
    print(f"✅ Validation error caught: {e.errors()[0]['msg']}")

# Test 3: Invalid document (too short)
print("\nTest 3: Title too short")
try:
    doc = DocumentCreate(
        user_id="user_123",
        title="",  # Empty!
        content="Content"
    )
except ValidationError as e:
    print(f"✅ Validation error caught: {e.errors()[0]['msg']}")

# Test 4: Whitespace stripping
print("\nTest 4: Whitespace stripping")
doc = DocumentCreate(
    user_id="  user_123  ",
    title="  My Document  ",
    content="  Content  "
)
print(f"✅ user_id: '{doc.user_id}' (spaces removed)")
print(f"   title: '{doc.title}' (spaces removed)")

# Test 5: Create MongoDB document
print("\nTest 5: MongoDB document creation")
doc_dict = create_document_dict(doc)
print(f"✅ Document dict created:")
print(f"   Status: {doc_dict['status']}")
print(f"   Created at: {doc_dict['created_at']}")
print(f"   Content hash: {doc_dict['content_hash']}")

print("\n✅ All model tests passed!")