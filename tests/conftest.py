"""
EspoCRM Python Client Test Configuration

Bu dosya pytest fixtures, mock utilities ve test konfigürasyonunu içerir.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from unittest.mock import Mock, MagicMock, patch
import responses
import requests

from espocrm.client import EspoCRMClient
from espocrm.config import ClientConfig
from espocrm.auth import (
    APIKeyAuth,
    HMACAuth,
    BasicAuth,
    create_api_key_auth,
    create_hmac_auth,
    create_basic_auth
)
from espocrm.models.entities import EntityRecord, Entity
from espocrm.models.responses import (
    ListResponse,
    EntityResponse,
    StreamResponse
)
from espocrm.models.metadata import (
    FieldType,
    RelationshipType,
    FieldMetadata,
    RelationshipMetadata,
    EntityMetadata,
    ApplicationMetadata
)


# Test Configuration
TEST_CONFIG = {
    "base_url": "https://test.espocrm.com",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1.0,
    "rate_limit_per_minute": 100,
    "api_key": "test_api_key_123"
}

# Mock Data Templates
MOCK_ENTITIES = {
    "Account": {
        "id": "675a1b2c3d4e5f6a7",  # 17 characters
        "name": "Test Company",
        "type": "Customer",
        "industry": "Technology",
        "website": "https://test-company.com",
        "phoneNumber": "+1-555-0123",
        "emailAddress": "info@test-company.com",
        "billingAddressStreet": "123 Test St",
        "billingAddressCity": "Test City",
        "billingAddressState": "TS",
        "billingAddressPostalCode": "12345",
        "billingAddressCountry": "Test Country",
        "description": "Test company description",
        "createdAt": "2024-01-01T10:00:00+00:00",
        "modifiedAt": "2024-01-01T10:00:00+00:00",
        "createdById": "675a1b2c3d4e5f6a8",  # 17 characters
        "modifiedById": "675a1b2c3d4e5f6a8"  # 17 characters
    },
    "Contact": {
        "id": "675a1b2c3d4e5f6a9",  # 17 characters
        "firstName": "John",
        "lastName": "Doe",
        "name": "John Doe",
        "emailAddress": "john.doe@test.com",
        "phoneNumber": "+1-555-0124",
        "title": "Software Engineer",
        "accountId": "675a1b2c3d4e5f6a7",  # 17 characters
        "accountName": "Test Company",
        "description": "Test contact description",
        "createdAt": "2024-01-01T11:00:00+00:00",
        "modifiedAt": "2024-01-01T11:00:00+00:00",
        "createdById": "675a1b2c3d4e5f6a8",  # 17 characters
        "modifiedById": "675a1b2c3d4e5f6a8"  # 17 characters
    },
    "Lead": {
        "id": "675a1b2c3d4e5f6b0",  # 17 characters
        "firstName": "Jane",
        "lastName": "Smith",
        "name": "Jane Smith",
        "status": "New",
        "source": "Web Site",
        "industry": "Technology",
        "emailAddress": "jane.smith@prospect.com",
        "phoneNumber": "+1-555-0125",
        "website": "https://prospect.com",
        "description": "Potential customer from website",
        "createdAt": "2024-01-01T12:00:00+00:00",
        "modifiedAt": "2024-01-01T12:00:00+00:00",
        "createdById": "675a1b2c3d4e5f6a8",  # 17 characters
        "modifiedById": "675a1b2c3d4e5f6a8"  # 17 characters
    },
    "Opportunity": {
        "id": "675a1b2c3d4e5f6b1",  # 17 characters
        "name": "Big Deal",
        "stage": "Prospecting",
        "amount": 50000.00,
        "probability": 25,
        "closeDate": "2024-06-01",
        "accountId": "675a1b2c3d4e5f6a7",  # 17 characters
        "accountName": "Test Company",
        "description": "Large opportunity with existing customer",
        "createdAt": "2024-01-01T13:00:00+00:00",
        "modifiedAt": "2024-01-01T13:00:00+00:00",
        "createdById": "675a1b2c3d4e5f6a8",  # 17 characters
        "modifiedById": "675a1b2c3d4e5f6a8"  # 17 characters
    }
}

# Mock Metadata
MOCK_METADATA = {
    "entityDefs": {
        "Account": {
            "fields": {
                "name": {
                    "type": "varchar",
                    "required": True,
                    "maxLength": 255
                },
                "type": {
                    "type": "enum",
                    "options": ["Customer", "Investor", "Partner", "Reseller"]
                },
                "industry": {
                    "type": "enum",
                    "options": ["Technology", "Healthcare", "Finance", "Manufacturing"]
                },
                "website": {
                    "type": "url"
                },
                "phoneNumber": {
                    "type": "phone"
                },
                "emailAddress": {
                    "type": "email"
                }
            },
            "links": {
                "contacts": {
                    "type": "oneToMany",
                    "entity": "Contact",
                    "foreign": "account"
                },
                "opportunities": {
                    "type": "oneToMany",
                    "entity": "Opportunity",
                    "foreign": "account"
                }
            }
        },
        "Contact": {
            "fields": {
                "firstName": {
                    "type": "varchar",
                    "maxLength": 100
                },
                "lastName": {
                    "type": "varchar",
                    "required": True,
                    "maxLength": 100
                },
                "emailAddress": {
                    "type": "email"
                },
                "phoneNumber": {
                    "type": "phone"
                },
                "title": {
                    "type": "varchar",
                    "maxLength": 100
                }
            },
            "links": {
                "account": {
                    "type": "belongsTo",
                    "entity": "Account"
                },
                "opportunities": {
                    "type": "manyToMany",
                    "entity": "Opportunity",
                    "relationName": "ContactOpportunity"
                }
            }
        }
    }
}


class MockEspoCRMServer:
    """Mock EspoCRM server for testing."""
    
    def __init__(self):
        self.entities = MOCK_ENTITIES.copy()
        self.metadata = MOCK_METADATA.copy()
        self.request_count = 0
        self.last_request = None
        self.rate_limit_remaining = 100
        self.rate_limit_reset = time.time() + 3600
    
    def reset(self):
        """Reset server state."""
        self.entities = MOCK_ENTITIES.copy()
        self.metadata = MOCK_METADATA.copy()
        self.request_count = 0
        self.last_request = None
        self.rate_limit_remaining = 100
        self.rate_limit_reset = time.time() + 3600
    
    def get_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by type and ID."""
        if entity_type in self.entities and self.entities[entity_type]["id"] == entity_id:
            return self.entities[entity_type].copy()
        return None
    
    def create_entity(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity."""
        entity_id = f"{entity_type.lower()}_{int(time.time())}"
        entity_data = data.copy()
        entity_data.update({
            "id": entity_id,
            "createdAt": datetime.utcnow().isoformat() + "+00:00",
            "modifiedAt": datetime.utcnow().isoformat() + "+00:00",
            "createdById": "user_123",
            "modifiedById": "user_123"
        })
        return entity_data
    
    def update_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing entity."""
        entity = self.get_entity(entity_type, entity_id)
        if not entity:
            return {}
        
        entity.update(data)
        entity["modifiedAt"] = datetime.utcnow().isoformat() + "+00:00"
        entity["modifiedById"] = "user_123"
        return entity
    
    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete entity."""
        return self.get_entity(entity_type, entity_id) is not None
    
    def list_entities(self, entity_type: str, **params) -> Dict[str, Any]:
        """List entities with pagination."""
        # Simulate list response
        entities = [self.entities.get(entity_type, {})] if entity_type in self.entities else []
        
        return {
            "total": len(entities),
            "list": entities
        }


# Pytest Fixtures

@pytest.fixture
def mock_server():
    """Mock EspoCRM server fixture."""
    return MockEspoCRMServer()


@pytest.fixture
def test_config():
    """Test configuration fixture."""
    return ClientConfig(**TEST_CONFIG)


@pytest.fixture
def api_key_auth():
    """API Key authentication fixture."""
    return create_api_key_auth("test_api_key_123")


@pytest.fixture
def hmac_auth():
    """HMAC authentication fixture."""
    return create_hmac_auth("test_api_key", "test_secret_key")


@pytest.fixture
def basic_auth():
    """Basic authentication fixture."""
    return create_basic_auth("testuser", password="testpass")


@pytest.fixture
def mock_client(test_config, api_key_auth):
    """Mock EspoCRM client fixture."""
    client = Mock(spec=EspoCRMClient)
    client.config = test_config
    client.auth = api_key_auth
    client.base_url = test_config.base_url
    client.api_version = "v1"  # API version attribute'u ekle
    client.logger = Mock()  # Logger attribute'u ekle
    return client


@pytest.fixture
def real_client(test_config, api_key_auth):
    """Real EspoCRM client fixture for integration tests."""
    return EspoCRMClient(base_url=test_config.base_url, config=test_config, auth=api_key_auth)


@pytest.fixture
def sample_account():
    """Sample account entity fixture."""
    return EntityRecord.create_from_dict(MOCK_ENTITIES["Account"].copy(), "Account")


@pytest.fixture
def sample_contact():
    """Sample contact entity fixture."""
    return EntityRecord.create_from_dict(MOCK_ENTITIES["Contact"].copy(), "Contact")


@pytest.fixture
def sample_lead():
    """Sample lead entity fixture."""
    return EntityRecord.create_from_dict(MOCK_ENTITIES["Lead"].copy(), "Lead")


@pytest.fixture
def sample_opportunity():
    """Sample opportunity entity fixture."""
    return EntityRecord.create_from_dict(MOCK_ENTITIES["Opportunity"].copy(), "Opportunity")


@pytest.fixture
def sample_entities(sample_account, sample_contact, sample_lead, sample_opportunity):
    """All sample entities fixture."""
    return {
        "Account": sample_account,
        "Contact": sample_contact,
        "Lead": sample_lead,
        "Opportunity": sample_opportunity
    }


@pytest.fixture
def mock_metadata():
    """Mock metadata fixture."""
    return ApplicationMetadata(
        entityDefs={
            "Account": EntityMetadata(
                fields={
                    "name": FieldMetadata(type=FieldType.VARCHAR, required=True, maxLength=255),
                    "type": FieldMetadata(type=FieldType.ENUM, options=["Customer", "Investor", "Partner"]),
                    "industry": FieldMetadata(type=FieldType.ENUM, options=["Technology", "Healthcare"]),
                    "website": FieldMetadata(type=FieldType.URL),
                    "phoneNumber": FieldMetadata(type=FieldType.PHONE),
                    "emailAddress": FieldMetadata(type=FieldType.EMAIL)
                },
                links={
                    "contacts": RelationshipMetadata(
                        type=RelationshipType.ONE_TO_MANY,
                        entity="Contact",
                        foreign="account"
                    ),
                    "opportunities": RelationshipMetadata(
                        type=RelationshipType.ONE_TO_MANY,
                        entity="Opportunity",
                        foreign="account"
                    )
                }
            ),
            "Contact": EntityMetadata(
                fields={
                    "firstName": FieldMetadata(type=FieldType.VARCHAR, maxLength=100),
                    "lastName": FieldMetadata(type=FieldType.VARCHAR, required=True, maxLength=100),
                    "emailAddress": FieldMetadata(type=FieldType.EMAIL),
                    "phoneNumber": FieldMetadata(type=FieldType.PHONE),
                    "title": FieldMetadata(type=FieldType.VARCHAR, maxLength=100)
                },
                links={
                    "account": RelationshipMetadata(
                        type=RelationshipType.BELONGS_TO,
                        entity="Account"
                    )
                }
            )
        }
    )


@pytest.fixture
def responses_mock():
    """Responses mock fixture for HTTP mocking."""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mock_http_responses(responses_mock, mock_server):
    """Setup mock HTTP responses."""
    base_url = TEST_CONFIG["base_url"]
    api_version = "v1"  # Fixed API version
    
    # GET entity
    def get_entity_callback(request):
        path_parts = request.url.split('/')
        entity_type = path_parts[-2]
        entity_id = path_parts[-1]
        
        entity = mock_server.get_entity(entity_type, entity_id)
        if entity:
            return (200, {}, json.dumps(entity))
        else:
            return (404, {}, json.dumps({"error": "Not Found"}))
    
    # POST entity (create)
    def create_entity_callback(request):
        path_parts = request.url.split('/')
        entity_type = path_parts[-1]
        
        data = json.loads(request.body)
        entity = mock_server.create_entity(entity_type, data)
        return (201, {}, json.dumps(entity))
    
    # PUT entity (update)
    def update_entity_callback(request):
        path_parts = request.url.split('/')
        entity_type = path_parts[-2]
        entity_id = path_parts[-1]
        
        data = json.loads(request.body)
        entity = mock_server.update_entity(entity_type, entity_id, data)
        if entity:
            return (200, {}, json.dumps(entity))
        else:
            return (404, {}, json.dumps({"error": "Not Found"}))
    
    # DELETE entity
    def delete_entity_callback(request):
        path_parts = request.url.split('/')
        entity_type = path_parts[-2]
        entity_id = path_parts[-1]
        
        if mock_server.delete_entity(entity_type, entity_id):
            return (200, {}, json.dumps({"deleted": True}))
        else:
            return (404, {}, json.dumps({"error": "Not Found"}))
    
    # GET entity list
    def list_entities_callback(request):
        path_parts = request.url.split('/')
        entity_type = path_parts[-1]
        
        result = mock_server.list_entities(entity_type)
        return (200, {}, json.dumps(result))
    
    # Basit static mock'lar kullan
    # POST /api/v1/Account (create)
    responses_mock.add(
        responses.POST,
        f"{base_url}/api/{api_version}/Account",
        json={
            "id": "account_1751483609360",
            "name": "Integration Test Company",
            "type": "Customer",
            "industry": "Technology",
            "createdAt": "2024-01-01T10:00:00+00:00",
            "modifiedAt": "2024-01-01T10:00:00+00:00"
        },
        status=201
    )
    
    # GET /api/v1/Account/{id} (read)
    responses_mock.add(
        responses.GET,
        f"{base_url}/api/{api_version}/Account/account_1751483609360",
        json={
            "id": "account_1751483609360",
            "name": "Integration Test Company",
            "type": "Customer",
            "industry": "Technology",
            "createdAt": "2024-01-01T10:00:00+00:00",
            "modifiedAt": "2024-01-01T10:00:00+00:00"
        },
        status=200
    )
    
    # PUT /api/v1/Account/{id} (update)
    responses_mock.add(
        responses.PUT,
        f"{base_url}/api/{api_version}/Account/account_1751483609360",
        json={
            "id": "account_1751483609360",
            "name": "Integration Test Company",
            "type": "Customer",
            "industry": "Healthcare",  # Updated
            "createdAt": "2024-01-01T10:00:00+00:00",
            "modifiedAt": "2024-01-01T11:00:00+00:00"
        },
        status=200
    )
    
    # PATCH /api/v1/Account/{id} (partial update)
    responses_mock.add(
        responses.PATCH,
        f"{base_url}/api/{api_version}/Account/account_1751483609360",
        json={
            "id": "account_1751483609360",
            "name": "Integration Test Company",
            "type": "Customer",
            "industry": "Healthcare",  # Updated
            "createdAt": "2024-01-01T10:00:00+00:00",
            "modifiedAt": "2024-01-01T11:00:00+00:00"
        },
        status=200
    )
    
    # DELETE /api/v1/Account/{id} (delete)
    responses_mock.add(
        responses.DELETE,
        f"{base_url}/api/{api_version}/Account/account_1751483609360",
        json={"deleted": True},
        status=200
    )
    
    # GET /api/v1/Account (list)
    responses_mock.add(
        responses.GET,
        f"{base_url}/api/{api_version}/Account",
        json={
            "total": 1,
            "list": [{
                "id": "account_1751483609360",
                "name": "Integration Test Company",
                "type": "Customer",
                "industry": "Healthcare"
            }]
        },
        status=200
    )
    
    # GET /api/v1/Metadata
    responses_mock.add(
        responses.GET,
        f"{base_url}/api/{api_version}/Metadata",
        json=MOCK_METADATA,
        status=200
    )
    
    # Stream endpoints
    # GET /api/v1/Stream (user stream) - with query parameters
    import re
    responses_mock.add(
        responses.GET,
        re.compile(f"{base_url}/api/{api_version}/Stream.*"),
        json={
            "total": 2,
            "list": [
                {
                    "id": "675a1b2c3d4e5f6a7",
                    "type": "Post",
                    "data": {"post": "User stream post"},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T10:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6a9"
                },
                {
                    "id": "675a1b2c3d4e5f6b0",
                    "type": "Update",
                    "data": {"fields": {"name": "Updated Name"}},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T09:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6b1"
                }
            ]
        },
        status=200
    )
    
    # GET /api/v1/Account/{id}/stream (entity stream) - with query parameters
    responses_mock.add(
        responses.GET,
        re.compile(f"{base_url}/api/{api_version}/Account/675a1b2c3d4e5f6a8/stream.*"),
        json={
            "total": 1,
            "list": [
                {
                    "id": "675a1b2c3d4e5f6a7",
                    "type": "Post",
                    "data": {"post": "Entity stream post"},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T10:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6a9"
                }
            ]
        },
        status=200
    )
    
    # POST /api/v1/Note (create stream post)
    responses_mock.add(
        responses.POST,
        f"{base_url}/api/{api_version}/Note",
        json={
            "id": "675a1b2c3d4e5f6c0",
            "type": "Post",
            "post": "Integration test post",
            "data": {"post": "Integration test post"},
            "parentType": "Account",
            "parentId": "675a1b2c3d4e5f6a8",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        },
        status=201
    )
    
    # GET /api/v1/Note/{id} (get stream note)
    responses_mock.add(
        responses.GET,
        f"{base_url}/api/{api_version}/Note/675a1b2c3d4e5f6c0",
        json={
            "id": "675a1b2c3d4e5f6c0",
            "type": "Post",
            "post": "Retrieved note",
            "data": {"post": "Retrieved note"},
            "parentType": "Account",
            "parentId": "675a1b2c3d4e5f6a8",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        },
        status=200
    )
    
    # DELETE /api/v1/Note/{id} (delete stream note)
    responses_mock.add(
        responses.DELETE,
        f"{base_url}/api/{api_version}/Note/675a1b2c3d4e5f6c0",
        json={"success": True},
        status=200
    )
    
    # PUT /api/v1/Account/{id}/subscription (follow entity)
    responses_mock.add(
        responses.PUT,
        f"{base_url}/api/{api_version}/Account/675a1b2c3d4e5f6a8/subscription",
        json={"success": True},
        status=200
    )
    
    # DELETE /api/v1/Account/{id}/subscription (unfollow entity)
    responses_mock.add(
        responses.DELETE,
        f"{base_url}/api/{api_version}/Account/675a1b2c3d4e5f6a8/subscription",
        json={"success": True},
        status=200
    )
    
    # GET /api/v1/Account/{id}/subscription (check follow status)
    responses_mock.add(
        responses.GET,
        f"{base_url}/api/{api_version}/Account/675a1b2c3d4e5f6a8/subscription",
        json={"isFollowing": True},
        status=200
    )
    
    # Attachment endpoints
    # POST /api/v1/Attachment (upload attachment) - Generic mock for all uploads
    def attachment_upload_callback(request):
        # Parse request to get filename and other details
        import base64
        try:
            if hasattr(request, 'body') and request.body:
                data = json.loads(request.body)
                filename = data.get('name', 'uploaded_file.txt')
                file_content = data.get('file', '')
                mime_type = data.get('type', 'text/plain')
                
                # Calculate size from base64 content
                try:
                    decoded_content = base64.b64decode(file_content)
                    size = len(decoded_content)
                except:
                    size = len(file_content)
                
                # Generate unique ID based on filename
                if filename == "integration_test.txt":
                    attachment_id = "675a1b2c3d4e5f6d0"
                elif "unicode" in filename or "файл" in filename:
                    attachment_id = "attachment_unicode"
                elif filename == "README":
                    attachment_id = "attachment_no_ext"
                else:
                    attachment_id = "mock_id"
                
                return (201, {}, json.dumps({
                    "id": attachment_id,
                    "name": filename,
                    "type": mime_type,
                    "size": size,
                    "role": "Attachment",
                    "createdAt": "2024-01-01T12:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6a9"
                }))
        except:
            pass
        
        # Default response
        return (201, {}, json.dumps({
            "id": "mock_id",
            "name": "uploaded_file.txt",
            "type": "text/plain",
            "size": 100,
            "role": "Attachment",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        }))
    
    responses_mock.add_callback(
        responses.POST,
        f"{base_url}/api/{api_version}/Attachment",
        callback=attachment_upload_callback
    )
    
    # GET /api/v1/Attachment/{id} (get attachment info) - Multiple IDs
    attachment_info_responses = {
        "675a1b2c3d4e5f6d0": {
            "id": "675a1b2c3d4e5f6d0",
            "name": "integration_test.txt",
            "type": "text/plain",
            "size": 33,
            "role": "Attachment",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        },
        "attachment_0": {
            "id": "attachment_0",
            "name": "Mock_Entity.txt",
            "type": "text/plain",
            "size": 18,  # "Downloaded content" = 18 bytes
            "role": "Attachment",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        },
        "attachment_1": {
            "id": "attachment_1",
            "name": "test_file_1.txt",
            "type": "text/plain",
            "size": 100,
            "role": "Attachment",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        },
        "attachment_2": {
            "id": "attachment_2",
            "name": "test_file_2.txt",
            "type": "text/plain",
            "size": 100,
            "role": "Attachment",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        },
        "attachment_123": {
            "id": "attachment_123",
            "name": "document.pdf",
            "type": "application/pdf",
            "size": 1024,
            "role": "Attachment",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        },
        "mock_id": {
            "id": "mock_id",
            "name": "uploaded_file.txt",
            "type": "text/plain",
            "size": 100,
            "role": "Attachment",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        },
        "attachment_unicode": {
            "id": "attachment_unicode",
            "name": "файл.txt",
            "type": "text/plain",
            "size": 12,
            "role": "Attachment",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        },
        "attachment_no_ext": {
            "id": "attachment_no_ext",
            "name": "README",
            "type": "text/plain",
            "size": 19,
            "role": "Attachment",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        }
    }
    
    def attachment_info_callback(request):
        # Extract attachment ID from URL
        path_parts = request.url.split('/')
        attachment_id = path_parts[-1].split('?')[0]  # Remove query params
        
        if attachment_id in attachment_info_responses:
            return (200, {}, json.dumps(attachment_info_responses[attachment_id]))
        else:
            return (404, {}, json.dumps({"error": "Attachment not found"}))
    
    responses_mock.add_callback(
        responses.GET,
        re.compile(f"{base_url}/api/{api_version}/Attachment/[^/]+$"),
        callback=attachment_info_callback
    )
    
    # GET /api/v1/Attachment/file/{id} (download attachment) - Multiple IDs
    attachment_file_responses = {
        "675a1b2c3d4e5f6d0": b"Test file content for integration",
        "attachment_0": b"Downloaded content",  # 18 bytes exactly
        "attachment_1": b"Test file 1 content",
        "attachment_2": b"Test file 2 content",
        "attachment_123": b"PDF content here",
        "mock_id": b"Mock file content",
        "attachment_unicode": b"Unicode content",
        "attachment_no_ext": b"README file content"
    }
    
    def attachment_download_callback(request):
        # Extract attachment ID from URL
        path_parts = request.url.split('/')
        attachment_id = path_parts[-1].split('?')[0]  # Remove query params
        
        if attachment_id in attachment_file_responses:
            content = attachment_file_responses[attachment_id]
            return (200, {"Content-Type": "application/octet-stream"}, content)
        else:
            return (404, {}, b"File not found")
    
    responses_mock.add_callback(
        responses.GET,
        re.compile(f"{base_url}/api/{api_version}/Attachment/file/[^/]+$"),
        callback=attachment_download_callback
    )
    
    # DELETE /api/v1/Attachment/{id} (delete attachment) - Multiple IDs
    def attachment_delete_callback(request):
        # Extract attachment ID from URL
        path_parts = request.url.split('/')
        attachment_id = path_parts[-1].split('?')[0]  # Remove query params
        
        # Always return success for delete operations in tests
        return (200, {}, json.dumps({"success": True}))
    
    responses_mock.add_callback(
        responses.DELETE,
        re.compile(f"{base_url}/api/{api_version}/Attachment/[^/]+$"),
        callback=attachment_delete_callback
    )
    
    return responses_mock


# Test Utilities

class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_account(**overrides) -> Dict[str, Any]:
        """Create account test data."""
        data = MOCK_ENTITIES["Account"].copy()
        data.update(overrides)
        return data
    
    @staticmethod
    def create_contact(**overrides) -> Dict[str, Any]:
        """Create contact test data."""
        data = MOCK_ENTITIES["Contact"].copy()
        data.update(overrides)
        return data
    
    @staticmethod
    def create_lead(**overrides) -> Dict[str, Any]:
        """Create lead test data."""
        data = MOCK_ENTITIES["Lead"].copy()
        data.update(overrides)
        return data
    
    @staticmethod
    def create_opportunity(**overrides) -> Dict[str, Any]:
        """Create opportunity test data."""
        data = MOCK_ENTITIES["Opportunity"].copy()
        data.update(overrides)
        return data
    
    @staticmethod
    def create_list_response(entities: List[Dict[str, Any]], total: Optional[int] = None) -> Dict[str, Any]:
        """Create list response test data."""
        return {
            "total": total or len(entities),
            "list": entities
        }
    
    @staticmethod
    def create_error_response(message: str, code: int = 400) -> Dict[str, Any]:
        """Create error response test data."""
        return {
            "error": message,
            "code": code
        }


class MockResponseBuilder:
    """Builder for creating mock HTTP responses."""
    
    def __init__(self):
        self.status_code = 200
        self.headers = {}
        self.json_data = {}
        self.text_data = ""
    
    def with_status(self, status_code: int) -> 'MockResponseBuilder':
        """Set response status code."""
        self.status_code = status_code
        return self
    
    def with_header(self, key: str, value: str) -> 'MockResponseBuilder':
        """Add response header."""
        self.headers[key] = value
        return self
    
    def with_json(self, data: Dict[str, Any]) -> 'MockResponseBuilder':
        """Set JSON response data."""
        self.json_data = data
        return self
    
    def with_text(self, text: str) -> 'MockResponseBuilder':
        """Set text response data."""
        self.text_data = text
        return self
    
    def build(self) -> Mock:
        """Build mock response."""
        response = Mock()
        response.status_code = self.status_code
        response.headers = self.headers
        response.json.return_value = self.json_data
        response.text = self.text_data
        response.content = self.text_data.encode('utf-8')
        response.ok = 200 <= self.status_code < 300
        return response


# Performance Test Utilities

@pytest.fixture
def performance_timer():
    """Performance timer fixture."""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Security Test Utilities

@pytest.fixture
def security_test_data():
    """Security test data fixture."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd"
        ],
        "large_payloads": [
            "A" * 10000,  # Large string
            {f"key_{i}": f"value_{i}" for i in range(1000)},  # Large object
            list(range(10000))  # Large array
        ]
    }


# Error Simulation Utilities

class ErrorSimulator:
    """Utility for simulating various error conditions."""
    
    @staticmethod
    def network_error():
        """Simulate network error."""
        return requests.exceptions.ConnectionError("Network error")
    
    @staticmethod
    def timeout_error():
        """Simulate timeout error."""
        return requests.exceptions.Timeout("Request timeout")
    
    @staticmethod
    def http_error(status_code: int, message: str = "HTTP Error"):
        """Simulate HTTP error."""
        response = Mock()
        response.status_code = status_code
        response.text = message
        response.json.return_value = {"error": message}
        error = requests.exceptions.HTTPError(message)
        error.response = response
        return error
    
    @staticmethod
    def rate_limit_error():
        """Simulate rate limit error."""
        return ErrorSimulator.http_error(429, "Rate limit exceeded")
    
    @staticmethod
    def auth_error():
        """Simulate authentication error."""
        return ErrorSimulator.http_error(401, "Unauthorized")
    
    @staticmethod
    def not_found_error():
        """Simulate not found error."""
        return ErrorSimulator.http_error(404, "Not found")
    
    @staticmethod
    def server_error():
        """Simulate server error."""
        return ErrorSimulator.http_error(500, "Internal server error")


@pytest.fixture
def error_simulator():
    """Error simulator fixture."""
    return ErrorSimulator()


# Parametrized Test Data

@pytest.fixture(params=["Account", "Contact", "Lead", "Opportunity"])
def entity_type(request):
    """Parametrized entity type fixture."""
    return request.param


@pytest.fixture(params=[
    {"type": "api_key", "auth": lambda: create_api_key_auth("test_key")},
    {"type": "hmac", "auth": lambda: create_hmac_auth("test_key", "test_secret")},
    {"type": "basic", "auth": lambda: create_basic_auth("user", password="pass")}
])
def auth_method(request):
    """Parametrized authentication method fixture."""
    return request.param


@pytest.fixture(params=[200, 201, 400, 401, 403, 404, 429, 500])
def http_status_code(request):
    """Parametrized HTTP status code fixture."""
    return request.param


# Cleanup Fixtures

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatic cleanup after each test."""
    yield
    # Cleanup code here if needed
    pass


# Test Markers

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "crud: CRUD operation tests")
    config.addinivalue_line("markers", "metadata: Metadata tests")
    config.addinivalue_line("markers", "relationships: Relationship tests")
    config.addinivalue_line("markers", "stream: Stream tests")
    config.addinivalue_line("markers", "attachments: Attachment tests")
    config.addinivalue_line("markers", "logging: Logging tests")
    config.addinivalue_line("markers", "validation: Validation tests")
    config.addinivalue_line("markers", "error_handling: Error handling tests")