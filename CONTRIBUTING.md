# Contributing to EspoCRM Python Client

Thank you for considering contributing to the EspoCRM Python Client! This guide will help you understand how to contribute effectively.

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- Git
- pip

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/espocrm/espocrm-python-client.git
   cd espocrm-python-client
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=espocrm

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Test Fixtures

The test suite includes comprehensive fixtures to make testing easier. Here are examples of how to use them:

#### Mock Server Fixture

```python
import pytest

def test_api_endpoint(mock_server):
    """Test using mock server to simulate API responses."""
    # Mock server automatically handles HTTP responses
    mock_server.reset()  # Reset server state
    
    # Create test data
    account = mock_server.create_entity("Account", {
        "name": "Test Company",
        "type": "Customer"
    })
    
    assert account["name"] == "Test Company"
```

#### Sample Entity Fixtures

```python
import pytest

def test_entity_operations(sample_account, sample_contact, sample_lead):
    """Test using pre-configured sample entities."""
    # Use ready-made test entities
    assert sample_account.get("name") == "Test Company"
    assert sample_contact.get("firstName") == "John"
    assert sample_lead.get("status") == "New"
    
    # Access all sample entities at once
    def test_all_entities(sample_entities):
        assert "Account" in sample_entities
        assert "Contact" in sample_entities
        assert "Lead" in sample_entities
        assert "Opportunity" in sample_entities
```

#### Authentication Fixtures

```python
import pytest

def test_authentication_methods(api_key_auth, hmac_auth, basic_auth):
    """Test different authentication methods."""
    # Test API Key authentication
    assert api_key_auth.api_key == "test_api_key_123"
    
    # Test HMAC authentication
    assert hmac_auth.api_key == "test_api_key"
    assert hmac_auth.secret_key == "test_secret_key"
    
    # Test Basic authentication
    assert basic_auth.username == "testuser"
```

#### Mock Client Fixture

```python
import pytest
from espocrm.clients.crud import CrudClient

def test_crud_operations(mock_client, sample_account):
    """Test CRUD operations using mock client."""
    # Setup mock response
    mock_client.post.return_value = sample_account.data
    
    # Create CRUD client
    crud_client = CrudClient(mock_client)
    
    # Test create operation
    result = crud_client.create("Account", {"name": "New Company"})
    
    # Verify
    assert result.data["name"] == sample_account.get("name")
    mock_client.post.assert_called_once()
```

#### Performance Testing Fixtures

```python
import pytest

def test_performance(performance_timer):
    """Test performance using performance timer."""
    performance_timer.start()
    
    # Your code to test
    for i in range(100):
        # Simulate some work
        result = f"Entity {i}"
    
    performance_timer.stop()
    
    # Assert performance requirements
    assert performance_timer.elapsed < 1.0  # Should complete in less than 1 second
```

#### HTTP Mocking Fixtures

```python
import pytest
import responses

def test_http_requests(mock_http_responses):
    """Test HTTP requests using mock responses."""
    # Mock responses are automatically configured
    # Test your HTTP client code here
    from espocrm.client import EspoCRMClient
    from espocrm.auth import create_api_key_auth
    
    auth = create_api_key_auth("test_key")
    client = EspoCRMClient("https://test.espocrm.com", auth)
    
    # This will use the mocked responses
    result = client.crud.create("Account", {"name": "Test"})
    assert result.data["name"] == "Integration Test Company"
```

#### Custom Mock HTTP Responses

```python
import pytest
import responses

@responses.activate
def test_custom_http_responses():
    """Test with custom HTTP responses."""
    responses.add(
        responses.GET,
        "https://test.espocrm.com/api/v1/Account/123",
        json={"id": "123", "name": "Custom Test"},
        status=200
    )
    
    # Your test code here
```

#### Error Simulation Fixtures

```python
import pytest

def test_error_handling(error_simulator):
    """Test error handling using error simulator."""
    # Network error
    network_error = error_simulator.network_error()
    assert isinstance(network_error, ConnectionError)
    
    # HTTP error
    http_error = error_simulator.http_error(404, "Not Found")
    assert http_error.response.status_code == 404
    
    # Rate limit error
    rate_limit_error = error_simulator.rate_limit_error()
    assert rate_limit_error.response.status_code == 429
```

#### Mock Metadata Fixture

```python
import pytest

def test_metadata_operations(mock_metadata):
    """Test metadata operations."""
    # Access entity metadata
    account_metadata = mock_metadata.entityDefs["Account"]
    assert "name" in account_metadata.fields
    assert "contacts" in account_metadata.links
    
    # Test field metadata
    name_field = account_metadata.fields["name"]
    assert name_field.type == "varchar"
    assert name_field.required is True
```

#### Test Data Factory

```python
import pytest

def test_data_factory():
    """Test using data factory for custom test data."""
    from tests.conftest import TestDataFactory
    
    # Create custom account data
    account_data = TestDataFactory.create_account(
        name="Custom Company",
        type="Partner",
        industry="Healthcare"
    )
    
    assert account_data["name"] == "Custom Company"
    assert account_data["type"] == "Partner"
    
    # Create list response
    list_response = TestDataFactory.create_list_response(
        entities=[account_data],
        total=1
    )
    
    assert list_response["total"] == 1
    assert len(list_response["list"]) == 1
```

#### Mock Response Builder

```python
import pytest

def test_response_builder():
    """Test using mock response builder."""
    from tests.conftest import MockResponseBuilder
    
    # Build custom response
    response = MockResponseBuilder() \
        .with_status(200) \
        .with_header("Content-Type", "application/json") \
        .with_json({"id": "123", "name": "Test"}) \
        .build()
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json()["name"] == "Test"
```

#### Security Testing Fixtures

```python
import pytest

def test_security(security_test_data):
    """Test security using security test data."""
    # SQL injection payloads
    for payload in security_test_data["sql_injection"]:
        # Test that your code handles these safely
        assert "DROP TABLE" in payload
    
    # XSS payloads
    for payload in security_test_data["xss_payloads"]:
        # Test XSS prevention
        assert "<script>" in payload
    
    # Path traversal payloads
    for payload in security_test_data["path_traversal"]:
        # Test path traversal prevention
        assert "../" in payload
```

### Optional Metadata Mock

The `mock_http_responses` fixture supports optional metadata mocking:

```python
import pytest

# Test with metadata mocking (default)
def test_with_metadata(mock_http_responses):
    """Test with metadata endpoint mocked."""
    # Metadata endpoint is automatically mocked
    pass

# Test without metadata mocking
@pytest.mark.parametrize("mock_http_responses", [{"metadata": False}], indirect=True)
def test_without_metadata(mock_http_responses):
    """Test without metadata endpoint mocked."""
    # Metadata endpoint is not mocked
    pass
```

## 📝 Code Style

### Formatting

```bash
# Format code
black espocrm tests
isort espocrm tests

# Check formatting
black --check espocrm tests
isort --check-only espocrm tests
```

### Type Checking

```bash
# Run type checking
mypy espocrm
```

### Linting

```bash
# Run linting
flake8 espocrm tests
```

### Security Scanning

```bash
# Run security scan
bandit -r espocrm
```

## 🚀 Submitting Changes

### Commit Message Format

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(crud): add batch update functionality`
- `fix(auth): resolve API key validation issue`
- `docs(readme): update installation instructions`
- `test(crud): add integration tests for delete operations`

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation

3. **Run tests**
   ```bash
   pytest
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat(scope): your feature description"
   ```

5. **Push to GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Provide a clear description
   - Reference any related issues
   - Add screenshots if applicable

## 📋 Testing Guidelines

### Test Structure

```python
import pytest
from unittest.mock import Mock

@pytest.mark.unit
@pytest.mark.crud
class TestCRUDClient:
    """Test class for CRUD operations."""
    
    def test_create_entity_success(self, mock_client, sample_account):
        """Test successful entity creation."""
        # Arrange
        mock_client.post.return_value = sample_account.data
        
        # Act
        result = crud_client.create("Account", {"name": "Test"})
        
        # Assert
        assert result.data["name"] == sample_account.get("name")
        mock_client.post.assert_called_once()
```

### Test Categories

Use appropriate markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.slow` - Slow-running tests

### Test Naming

- Use descriptive names: `test_method_name_scenario`
- Be specific about what you're testing
- Include expected outcome

## 🐛 Reporting Issues

### Bug Reports

Include:
- Python version
- Package version
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

## 📚 Documentation

### Docstrings

Follow Google style docstrings:

```python
def create_entity(self, entity_type: str, data: Dict[str, Any]) -> EntityResponse:
    """Create a new entity.
    
    Args:
        entity_type: The type of entity to create
        data: Entity data dictionary
        
    Returns:
        EntityResponse containing the created entity
        
    Raises:
        EspoCRMValidationError: If data validation fails
        EspoCRMError: If creation fails
    """
```

### Type Hints

Always include type hints:

```python
from typing import Dict, Any, Optional, List

def process_entities(entities: List[Dict[str, Any]]) -> Optional[List[EntityRecord]]:
    """Process a list of entities."""
```

## 🏆 Recognition

Contributors are recognized in:
- README.md acknowledgments
- Release notes
- GitHub contributors page

## 📞 Getting Help

- 💬 [GitHub Discussions](https://github.com/espocrm/espocrm-python-client/discussions)
- 🐛 [GitHub Issues](https://github.com/espocrm/espocrm-python-client/issues)
- 📧 Email: support@espocrm-python-client.com

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
