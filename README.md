# EspoCRM Python Client

[![PyPI version](https://badge.fury.io/py/espocrm-python-client.svg)](https://badge.fury.io/py/espocrm-python-client)
[![Python versions](https://img.shields.io/pypi/pyversions/espocrm-python-client.svg)](https://pypi.org/project/espocrm-python-client/)
[![License](https://img.shields.io/pypi/l/espocrm-python-client.svg)](https://github.com/espocrm/espocrm-python-client/blob/main/LICENSE)
[![Tests](https://github.com/espocrm/espocrm-python-client/workflows/Tests/badge.svg)](https://github.com/espocrm/espocrm-python-client/actions)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen.svg)](https://espocrm-python-client.readthedocs.io)
[![Coverage](https://codecov.io/gh/espocrm/espocrm-python-client/branch/main/graph/badge.svg)](https://codecov.io/gh/espocrm/espocrm-python-client)

Modern, type-safe and comprehensive EspoCRM API client library for Python.

## ✨ Features

- **🔒 Type Safety**: Full type hints with Pydantic v2 validation
- **🏗️ Modern Architecture**: SOLID principles, modular design
- **📊 Structured Logging**: JSON-formatted professional logging
- **🌐 Comprehensive API**: Complete EspoCRM API coverage
- **🔐 Multiple Auth Methods**: API Key, HMAC, and Basic authentication
- **⚡ Async Support**: Optional async/await support
- **🐍 Python 3.8+**: Optimized for modern Python versions
- **🧪 Well Tested**: High test coverage with comprehensive test suite
- **📚 Well Documented**: Complete documentation with examples
- **🛠️ CLI Tool**: Command-line interface for common operations

## 📦 Installation

Install from PyPI using pip:

```bash
pip install espocrm-python-client
```

### Optional Dependencies

```bash
# For async support
pip install espocrm-python-client[async]

# For development
pip install espocrm-python-client[dev]

# For documentation
pip install espocrm-python-client[docs]

# Install all optional dependencies
pip install espocrm-python-client[async,dev,docs]
```

### Development Installation

```bash
git clone https://github.com/espocrm/espocrm-python-client.git
cd espocrm-python-client
pip install -e ".[dev]"
```

## 🚀 Quick Start

```python
from espocrm import EspoCRMClient
from espocrm.auth import APIKeyAuth

# Client'ı başlat
auth = APIKeyAuth("your-api-key")
client = EspoCRMClient("https://your-espocrm.com", auth)

# Kayıt oluştur
lead_data = {
    "firstName": "John",
    "lastName": "Doe", 
    "emailAddress": "john.doe@example.com"
}
lead = client.crud.create("Lead", lead_data)
print(f"Yeni Lead oluşturuldu: {lead.id}")

# Kayıtları listele
leads = client.crud.list("Lead", limit=10)
for lead in leads.records:
    print(f"Lead: {lead.firstName} {lead.lastName}")

# Kayıt güncelle
client.crud.update("Lead", lead.id, {"status": "Qualified"})

# Kayıt sil
client.crud.delete("Lead", lead.id)
```

## 🔐 Authentication

### API Key Authentication
```python
from espocrm.auth import APIKeyAuth

auth = APIKeyAuth("your-api-key")
client = EspoCRMClient("https://your-espocrm.com", auth)
```

### HMAC Authentication
```python
from espocrm.auth import HMACAuth

auth = HMACAuth("your-api-key", "your-secret-key")
client = EspoCRMClient("https://your-espocrm.com", auth)
```

### Basic Authentication
```python
from espocrm.auth import BasicAuth

auth = BasicAuth("username", "password")
client = EspoCRMClient("https://your-espocrm.com", auth)
```

## 📚 API Modülleri

### CRUD İşlemleri
```python
# Kayıt oluştur
record = client.crud.create("Account", data)

# Kayıt oku
record = client.crud.get("Account", record_id)

# Kayıtları listele
records = client.crud.list("Account", limit=20)

# Kayıt güncelle
client.crud.update("Account", record_id, updates)

# Kayıt sil
client.crud.delete("Account", record_id)
```

### İlişki Yönetimi
```python
# İlişkili kayıtları listele
contacts = client.relationships.list("Account", account_id, "contacts")

# İlişki oluştur
client.relationships.relate("Account", account_id, "contacts", contact_id)

# İlişki kaldır
client.relationships.unrelate("Account", account_id, "contacts", contact_id)
```

### Stream İşlemleri
```python
# Stream kayıtlarını al
stream = client.stream.get_user_stream()

# Kayıt stream'ini al
record_stream = client.stream.get_record_stream("Account", account_id)

# Stream'e post yap
client.stream.post("Account", account_id, "Yeni bir not eklendi")
```

### Dosya Yönetimi
```python
# Dosya yükle
with open("document.pdf", "rb") as f:
    attachment = client.attachments.upload(f, "document.pdf")

# Dosya indir
file_data = client.attachments.download(attachment_id)
```

### Metadata İşlemleri
```python
# Uygulama metadata'sını al
metadata = client.metadata.get_app_metadata()

# Entity metadata'sını al
entity_metadata = client.metadata.get_entity_metadata("Account")
```

## 🔍 Gelişmiş Arama

```python
from espocrm.models import SearchParams, WhereClause

# Gelişmiş arama parametreleri
search_params = SearchParams(
    where=[
        WhereClause(
            type="equals",
            attribute="status",
            value="New"
        ),
        WhereClause(
            type="contains",
            attribute="name",
            value="Tech"
        )
    ],
    order_by="createdAt",
    order="desc",
    limit=50,
    select=["id", "name", "status", "createdAt"]
)

results = client.crud.search("Lead", search_params)
```

## 📊 Logging ve Monitoring

```python
from espocrm.logging import get_logger

# Structured logger kullan
logger = get_logger("my_app")

# JSON formatında log
logger.info(
    "Lead oluşturuldu",
    extra={
        "lead_id": lead.id,
        "user_id": "user_123",
        "execution_time_ms": 245
    }
)
```

## 🧪 Test

```bash
# Tüm testleri çalıştır
pytest

# Coverage ile test
pytest --cov=espocrm

# Sadece unit testler
pytest -m unit

# Sadece integration testler  
pytest -m integration
```

## 🛠️ Geliştirme

```bash
# Geliştirme ortamını hazırla
pip install -e ".[dev]"

# Pre-commit hooks'ları kur
pre-commit install

# Code formatting
black espocrm tests
isort espocrm tests

# Type checking
mypy espocrm

# Linting
flake8 espocrm tests

# Security scan
bandit -r espocrm
```

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🤝 Katkıda Bulunma

Katkılarınızı memnuniyetle karşılıyoruz! Lütfen katkıda bulunmadan önce [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun.

## 📞 Destek

- **Dokümantasyon**: [https://espocrm-python-client.readthedocs.io](https://espocrm-python-client.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/espocrm/espocrm-python-client/issues)
- **Discussions**: [GitHub Discussions](https://github.com/espocrm/espocrm-python-client/discussions)

## 🔗 Links

- [EspoCRM Official Website](https://www.espocrm.com/)
- [EspoCRM API Documentation](https://docs.espocrm.com/development/api/)
- [PyPI Package](https://pypi.org/project/espocrm-python-client/)
- [GitHub Repository](https://github.com/espocrm/espocrm-python-client)
- [Documentation](https://espocrm-python-client.readthedocs.io)
- [Changelog](https://github.com/espocrm/espocrm-python-client/blob/main/CHANGELOG.md)

## 📈 Project Status

- **Development Status**: Beta
- **Stability**: Stable API
- **Maintenance**: Actively maintained
- **Python Support**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Platform Support**: Windows, macOS, Linux

## 🏆 Why Choose EspoCRM Python Client?

- **Production Ready**: Used in production environments
- **Type Safe**: Catch errors at development time, not runtime
- **Well Tested**: Comprehensive test suite with high coverage
- **Modern Python**: Built for Python 3.8+ with modern features
- **Excellent Documentation**: Complete guides and API reference
- **Active Community**: Regular updates and community support
- **Enterprise Ready**: Suitable for enterprise applications

## 📊 Statistics

- **Downloads**: [![Downloads](https://pepy.tech/badge/espocrm-python-client)](https://pepy.tech/project/espocrm-python-client)
- **GitHub Stars**: [![GitHub stars](https://img.shields.io/github/stars/espocrm/espocrm-python-client.svg?style=social&label=Star)](https://github.com/espocrm/espocrm-python-client)
- **Code Quality**: [![Code Quality](https://img.shields.io/codacy/grade/your-project-id.svg)](https://www.codacy.com/app/espocrm/espocrm-python-client)

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Bugs**: [Create an issue](https://github.com/espocrm/espocrm-python-client/issues/new?template=bug_report.md)
2. **Request Features**: [Create a feature request](https://github.com/espocrm/espocrm-python-client/issues/new?template=feature_request.md)
3. **Submit Pull Requests**: [Contributing Guidelines](https://github.com/espocrm/espocrm-python-client/blob/main/CONTRIBUTING.md)
4. **Improve Documentation**: Help us improve our docs
5. **Share**: Star the project and share with others

### Development Setup

```bash
# Clone the repository
git clone https://github.com/espocrm/espocrm-python-client.git
cd espocrm-python-client

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
black espocrm tests
isort espocrm tests
mypy espocrm
flake8 espocrm tests
```

## 📝 Changelog

See [CHANGELOG.md](https://github.com/espocrm/espocrm-python-client/blob/main/CHANGELOG.md) for a detailed history of changes.

## 🆘 Support

- **Documentation**: [Complete documentation](https://espocrm-python-client.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/espocrm/espocrm-python-client/issues)
- **Discussions**: [GitHub Discussions](https://github.com/espocrm/espocrm-python-client/discussions)
- **Email**: [support@espocrm-python-client.com](mailto:support@espocrm-python-client.com)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/espocrm/espocrm-python-client/blob/main/LICENSE) file for details.

## 🙏 Acknowledgments

- [EspoCRM Team](https://www.espocrm.com/) for creating an excellent CRM system
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- [Requests](https://requests.readthedocs.io/) for HTTP functionality
- [Structlog](https://www.structlog.org/) for structured logging
- All [contributors](https://github.com/espocrm/espocrm-python-client/graphs/contributors) who help improve this project

---

<div align="center">

**Made with ❤️ for the EspoCRM community**

[⭐ Star us on GitHub](https://github.com/espocrm/espocrm-python-client) • [📦 Install from PyPI](https://pypi.org/project/espocrm-python-client/) • [📚 Read the Docs](https://espocrm-python-client.readthedocs.io)

</div>