# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial PyPI package release preparation
- CLI tool (`espocrm-cli`) for command-line operations
- Comprehensive CI/CD pipeline with GitHub Actions
- Enhanced documentation with installation guides and API reference
- Package validation and quality checks
- Security scanning integration
- Multi-Python version support (3.8-3.12)
- Multi-OS testing (Ubuntu, Windows, macOS)

### Changed
- Updated package metadata for PyPI compatibility
- Enhanced classifiers and keywords for better discoverability
- Improved dependency management with version constraints

### Fixed
- Package structure validation
- Import path consistency
- Entry point configuration

## [0.1.0] - 2025-01-02

### Added
- **Core Features**
  - Modern, type-safe EspoCRM API client
  - Full Pydantic v2 integration for data validation
  - Comprehensive authentication support (API Key, Basic, HMAC)
  - Structured logging with JSON output
  - Complete CRUD operations support
  - Relationship management capabilities
  - Stream operations for activity feeds
  - File attachment handling
  - Metadata operations for schema introspection

- **Authentication Methods**
  - API Key authentication (`APIKeyAuth`)
  - Basic HTTP authentication (`BasicAuth`)
  - HMAC-SHA256 authentication (`HMACAuth`)
  - Extensible authentication base class

- **API Clients**
  - `CrudClient` - Create, Read, Update, Delete operations
  - `MetadataClient` - Schema and metadata operations
  - `RelationshipClient` - Entity relationship management
  - `StreamClient` - Activity stream operations
  - `AttachmentClient` - File upload and download

- **Data Models**
  - Type-safe entity models (Account, Contact, Lead, Opportunity)
  - Search and filtering capabilities with `SearchParams`
  - Response models for API operations
  - Comprehensive validation with Pydantic

- **Utilities**
  - HTTP utilities with retry logic
  - Data serialization and deserialization
  - URL and ID validation helpers
  - Query string building utilities

- **Logging System**
  - Structured logging with `structlog`
  - JSON formatters for production use
  - Metrics collection and performance tracking
  - Configurable log levels and handlers

- **Configuration Management**
  - Environment-based configuration
  - Default configuration management
  - Flexible client configuration options

- **Error Handling**
  - Comprehensive exception hierarchy
  - HTTP status code to exception mapping
  - Detailed error messages and context

- **Testing Infrastructure**
  - Comprehensive test suite with pytest
  - Unit tests for all components
  - Integration tests for API operations
  - Mock-based testing for external dependencies
  - Test coverage reporting

- **Documentation**
  - Complete API documentation
  - Usage examples and tutorials
  - Authentication guides
  - Best practices documentation

- **Development Tools**
  - Pre-commit hooks configuration
  - Code formatting with Black
  - Import sorting with isort
  - Type checking with mypy
  - Linting with flake8
  - Security scanning with bandit

### Technical Details
- **Python Support**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Dependencies**: 
  - `requests>=2.31.0` for HTTP operations
  - `pydantic>=2.5.0` for data validation
  - `structlog>=23.2.0` for structured logging
  - `typing-extensions>=4.8.0` for enhanced type hints
- **Optional Dependencies**:
  - `httpx>=0.25.0` for async support
  - `aiofiles>=23.2.0` for async file operations
- **Development Dependencies**: pytest, black, isort, mypy, flake8, bandit
- **Documentation Dependencies**: mkdocs, mkdocs-material, mkdocstrings

### Architecture
- **Design Patterns**: Factory, Strategy, Observer
- **SOLID Principles**: Single Responsibility, Open/Closed, Dependency Inversion
- **Type Safety**: Full type hints, runtime validation
- **Error Handling**: Comprehensive exception hierarchy
- **Logging**: Structured, contextual logging
- **Testing**: High test coverage, multiple test types
- **Documentation**: Comprehensive, up-to-date documentation

### Performance
- **HTTP Connection Pooling**: Efficient connection reuse
- **Request Retry Logic**: Automatic retry with exponential backoff
- **Data Validation**: Fast Pydantic validation
- **Memory Efficiency**: Optimized data structures
- **Async Support**: Optional async operations for high throughput

### Security
- **Authentication**: Multiple secure authentication methods
- **Input Validation**: Comprehensive data validation
- **Error Handling**: Secure error messages without sensitive data exposure
- **Dependencies**: Regular security updates and vulnerability scanning
- **Code Quality**: Static analysis and security scanning

---

## Release Notes

### Version 0.1.0 - Initial Release

This is the initial release of the EspoCRM Python Client library. It provides a modern, type-safe, and comprehensive interface to the EspoCRM API.

**Key Highlights:**
- 🔒 **Type Safety**: Full type hints and runtime validation
- 🚀 **Modern Python**: Support for Python 3.8+
- 📊 **Structured Logging**: JSON-based logging for production
- 🔧 **Multiple Auth Methods**: API Key, Basic, and HMAC authentication
- 📦 **Comprehensive API**: All major EspoCRM operations supported
- 🧪 **Well Tested**: High test coverage with multiple test types
- 📚 **Well Documented**: Complete documentation and examples

**Getting Started:**
```bash
pip install espocrm-python-client
```

**Quick Example:**
```python
from espocrm import EspoCRMClient
from espocrm.auth import APIKeyAuth

auth = APIKeyAuth("your-api-key")
client = EspoCRMClient("https://your-espocrm.com", auth)

# Create a lead
lead = client.crud.create("Lead", {
    "firstName": "John",
    "lastName": "Doe",
    "emailAddress": "john@example.com"
})
```

For detailed documentation, visit: https://espocrm-python-client.readthedocs.io

---

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## Support

- **Documentation**: https://espocrm-python-client.readthedocs.io
- **Issues**: https://github.com/espocrm/espocrm-python-client/issues
- **Discussions**: https://github.com/espocrm/espocrm-python-client/discussions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.