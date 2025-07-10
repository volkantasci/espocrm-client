"""
EspoCRM Python Client Test Configuration.

This module provides pytest fixtures, mock utilities, and test configuration.
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

import pytest
import requests
import responses

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
    
    def __init__(self) -> None:
        """Initialize the mock server."""
        self.entities: Dict[str, Dict[str, Any]] = MOCK_ENTITIES.copy()
        self.metadata: Dict[str, Any] = MOCK_METADATA.copy()
        self.request_count: int = 0
        self.last_request: Optional[Any] = None
        self.rate_limit_remaining: int = 100
        self.rate_limit_reset: float = time.time() + 3600
    
    def reset(self) -> None:
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
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def mock_http_responses(request, responses_mock, mock_server):
    """Setup mock HTTP responses with optional Metadata endpoint.
    
    This fixture can be parameterized to control which endpoints are mocked.
    
    Args:
        request: pytest request object that may contain parameters
        responses_mock: The responses mock fixture
        mock_server: The mock server fixture
    
    Returns:
        The configured responses mock object
    """
    # Extract parameters from request - metadata is True by default
    mock_metadata: bool = getattr(request, "param", {}).get("metadata", True)
    
    base_url = TEST_CONFIG["base_url"]
    api_version = "v1"  # Fixed API version
    
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
    
    # Conditionally add Metadata endpoint only if mock_metadata is True
    if mock_metadata:
        responses_mock.add(
            responses.GET,
            f"{base_url}/api/{api_version}/Metadata",
            json=MOCK_METADATA,
            status=200
        )
    
    return responses_mock


# Performance Test Utilities

@pytest.fixture
def performance_timer():
    """Performance timer fixture."""
    class Timer:
        def __init__(self) -> None:
            self.start_time: Optional[float] = None
            self.end_time: Optional[float] = None
        
        def start(self) -> None:
            self.start_time = time.time()
        
        def stop(self) -> None:
            self.end_time = time.time()
        
        @property
        def elapsed(self) -> Optional[float]:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Test Utilities

class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_account(**overrides: Any) -> Dict[str, Any]:
        """Create account test data."""
        data = MOCK_ENTITIES["Account"].copy()
        data.update(overrides)
        return data
    
    @staticmethod
    def create_contact(**overrides: Any) -> Dict[str, Any]:
        """Create contact test data."""
        data = MOCK_ENTITIES["Contact"].copy()
        data.update(overrides)
        return data
    
    @staticmethod
    def create_lead(**overrides: Any) -> Dict[str, Any]:
        """Create lead test data."""
        data = MOCK_ENTITIES["Lead"].copy()
        data.update(overrides)
        return data
    
    @staticmethod
    def create_opportunity(**overrides: Any) -> Dict[str, Any]:
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
    
    def __init__(self) -> None:
        """Initialize the mock response builder."""
        self.status_code: int = 200
        self.headers: Dict[str, str] = {}
        self.json_data: Dict[str, Any] = {}
        self.text_data: str = ""
    
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
            "A" * 1500000,  # Large string - 1.5MB, exceeds 1MB limit
            {f"key_{i}": f"value_{i}" * 1000 for i in range(1000)},  # Large object - each value is 1000 chars
            list(range(100000))  # Large array - 100,000 elements
        ]
    }


# Error Simulation Utilities

class ErrorSimulator:
    """Utility for simulating various error conditions."""
    
    @staticmethod
    def network_error() -> requests.exceptions.ConnectionError:
        """Simulate network error."""
        return requests.exceptions.ConnectionError("Network error")
    
    @staticmethod
    def timeout_error() -> requests.exceptions.Timeout:
        """Simulate timeout error."""
        return requests.exceptions.Timeout("Request timeout")
    
    @staticmethod
    def http_error(status_code: int, message: str = "HTTP Error") -> requests.exceptions.HTTPError:
        """Simulate HTTP error."""
        response = Mock()
        response.status_code = status_code
        response.text = message
        response.json.return_value = {"error": message}
        error = requests.exceptions.HTTPError(message)
        error.response = response
        return error
    
    @staticmethod
    def rate_limit_error() -> requests.exceptions.HTTPError:
        """Simulate rate limit error."""
        return ErrorSimulator.http_error(429, "Rate limit exceeded")
    
    @staticmethod
    def auth_error() -> requests.exceptions.HTTPError:
        """Simulate authentication error."""
        return ErrorSimulator.http_error(401, "Unauthorized")
    
    @staticmethod
    def not_found_error() -> requests.exceptions.HTTPError:
        """Simulate not found error."""
        return ErrorSimulator.http_error(404, "Not found")
    
    @staticmethod
    def server_error() -> requests.exceptions.HTTPError:
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