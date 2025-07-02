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
from espocrm.config import EspoCRMConfig
from espocrm.auth import (
    ApiKeyAuthentication,
    HMACAuthentication,
    BasicAuthentication,
    create_api_key_auth,
    create_hmac_auth,
    create_basic_auth
)
from espocrm.models.entities import Entity
from espocrm.models.responses import (
    ListResponse,
    EntityResponse,
    DeleteResponse,
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
    "api_version": "v1",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1.0,
    "rate_limit": 100,
    "rate_limit_window": 60
}

# Mock Data Templates
MOCK_ENTITIES = {
    "Account": {
        "id": "account_123",
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
        "createdById": "user_123",
        "modifiedById": "user_123"
    },
    "Contact": {
        "id": "contact_123",
        "firstName": "John",
        "lastName": "Doe",
        "name": "John Doe",
        "emailAddress": "john.doe@test.com",
        "phoneNumber": "+1-555-0124",
        "title": "Software Engineer",
        "accountId": "account_123",
        "accountName": "Test Company",
        "description": "Test contact description",
        "createdAt": "2024-01-01T11:00:00+00:00",
        "modifiedAt": "2024-01-01T11:00:00+00:00",
        "createdById": "user_123",
        "modifiedById": "user_123"
    },
    "Lead": {
        "id": "lead_123",
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
        "createdById": "user_123",
        "modifiedById": "user_123"
    },
    "Opportunity": {
        "id": "opportunity_123",
        "name": "Big Deal",
        "stage": "Prospecting",
        "amount": 50000.00,
        "probability": 25,
        "closeDate": "2024-06-01",
        "accountId": "account_123",
        "accountName": "Test Company",
        "description": "Large opportunity with existing customer",
        "createdAt": "2024-01-01T13:00:00+00:00",
        "modifiedAt": "2024-01-01T13:00:00+00:00",
        "createdById": "user_123",
        "modifiedById": "user_123"
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
            return None
        
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
    return EspoCRMConfig(**TEST_CONFIG)


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
    client.api_version = test_config.api_version
    return client


@pytest.fixture
def real_client(test_config, api_key_auth):
    """Real EspoCRM client fixture for integration tests."""
    return EspoCRMClient(config=test_config, auth=api_key_auth)


@pytest.fixture
def sample_account():
    """Sample account entity fixture."""
    return Entity("Account", MOCK_ENTITIES["Account"].copy())


@pytest.fixture
def sample_contact():
    """Sample contact entity fixture."""
    return Entity("Contact", MOCK_ENTITIES["Contact"].copy())


@pytest.fixture
def sample_lead():
    """Sample lead entity fixture."""
    return Entity("Lead", MOCK_ENTITIES["Lead"].copy())


@pytest.fixture
def sample_opportunity():
    """Sample opportunity entity fixture."""
    return Entity("Opportunity", MOCK_ENTITIES["Opportunity"].copy())


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
        entity_defs={
            "Account": EntityMetadata(
                fields={
                    "name": FieldMetadata(type=FieldType.VARCHAR, required=True, max_length=255),
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
                    "firstName": FieldMetadata(type=FieldType.VARCHAR, max_length=100),
                    "lastName": FieldMetadata(type=FieldType.VARCHAR, required=True, max_length=100),
                    "emailAddress": FieldMetadata(type=FieldType.EMAIL),
                    "phoneNumber": FieldMetadata(type=FieldType.PHONE),
                    "title": FieldMetadata(type=FieldType.VARCHAR, max_length=100)
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
    api_version = TEST_CONFIG["api_version"]
    
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
    
    # Setup URL patterns
    responses_mock.add_callback(
        responses.GET,
        f"{base_url}/api/{api_version}/Account/account_123",
        callback=get_entity_callback
    )
    
    responses_mock.add_callback(
        responses.POST,
        f"{base_url}/api/{api_version}/Account",
        callback=create_entity_callback
    )
    
    responses_mock.add_callback(
        responses.PUT,
        f"{base_url}/api/{api_version}/Account/account_123",
        callback=update_entity_callback
    )
    
    responses_mock.add_callback(
        responses.DELETE,
        f"{base_url}/api/{api_version}/Account/account_123",
        callback=delete_entity_callback
    )
    
    responses_mock.add_callback(
        responses.GET,
        f"{base_url}/api/{api_version}/Account",
        callback=list_entities_callback
    )
    
    # Metadata endpoint
    responses_mock.add(
        responses.GET,
        f"{base_url}/api/{api_version}/Metadata",
        json=MOCK_METADATA,
        status=200
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
            {"key": "value"} * 1000,  # Large object
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