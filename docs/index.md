# EspoCRM Python Client Dokümantasyonu

Modern, type-safe ve kapsamlı EspoCRM API kütüphanesi için resmi dokümantasyon.

## Hoş Geldiniz

EspoCRM Python Client, EspoCRM'in REST API'sini kullanarak Python uygulamalarınızda CRM işlemlerini kolayca gerçekleştirmenizi sağlayan modern bir kütüphanedir.

## Temel Özellikler

- **Type Safety**: Full type hints ve Pydantic validation
- **Modern OOP**: SOLID prensiplerine uygun modüler tasarım
- **Structured Logging**: JSON formatında professional logging
- **Kapsamlı API Desteği**: Tüm EspoCRM API özelliklerini destekler
- **Multiple Auth Methods**: API Key, HMAC ve Basic authentication
- **Async Support**: Opsiyonel async/await desteği
- **Python 3.8+**: Modern Python sürümleri için optimize edilmiş

## Hızlı Başlangıç

```python
from espocrm import EspoCRMClient
from espocrm.auth import APIKeyAuth

# Client'ı başlat
auth = APIKeyAuth("your-api-key")
client = EspoCRMClient("https://your-espocrm.com", auth)

# Kayıt oluştur
lead = client.crud.create("Lead", {
    "firstName": "John",
    "lastName": "Doe",
    "emailAddress": "john.doe@example.com"
})
```

## Dokümantasyon İçeriği

- [Kurulum](installation.md) - Kütüphaneyi nasıl kuracağınızı öğrenin
- [Hızlı Başlangıç](quickstart.md) - İlk adımlarınızı atın
- [Authentication](authentication.md) - Kimlik doğrulama yöntemleri
- [API Referansı](api_reference/) - Detaylı API dokümantasyonu
- [Örnekler](examples/) - Kullanım örnekleri

## Destek

- **GitHub Issues**: [Sorun bildirin](https://github.com/espocrm/espocrm-python-client/issues)
- **GitHub Discussions**: [Toplulukla tartışın](https://github.com/espocrm/espocrm-python-client/discussions)
- **EspoCRM Dokümantasyonu**: [Resmi API dokümantasyonu](https://docs.espocrm.com/development/api/)

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.