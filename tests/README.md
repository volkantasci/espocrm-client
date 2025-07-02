# EspoCRM Python Client Test Suite

Bu dizin EspoCRM Python Client için kapsamlı test suite'ini içerir. Test suite %90+ code coverage hedefler ve tüm bileşenleri kapsamlı şekilde test eder.

## Test Yapısı

```
tests/
├── conftest.py                 # Pytest fixtures ve konfigürasyon
├── test_runner.py             # Test runner ve raporlama
├── README.md                  # Bu dosya
├── test_auth/                 # Authentication testleri
│   └── test_authentication.py
├── test_clients/              # Client testleri
│   ├── test_crud.py
│   ├── test_relationships.py
│   ├── test_stream.py
│   ├── test_attachments.py
│   └── test_metadata.py
├── test_models/               # Model testleri
│   └── test_entities.py
├── test_utils/                # Utility testleri
│   └── test_http.py
├── test_logging/              # Logging testleri
│   └── test_logger.py
└── integration/               # Integration testleri
    └── test_end_to_end.py
```

## Test Kategorileri

### Unit Tests (`@pytest.mark.unit`)
- Her sınıf ve fonksiyon için izole testler
- Mock'lar kullanarak bağımlılıkları simüle eder
- Hızlı çalışır ve CI/CD pipeline'da sürekli çalıştırılır

### Integration Tests (`@pytest.mark.integration`)
- Bileşenler arası etkileşim testleri
- Mock EspoCRM server ile gerçek API simülasyonu
- End-to-end workflow testleri

### Performance Tests (`@pytest.mark.performance`)
- Response time ve memory usage testleri
- Bulk operations performance
- High volume data handling

### Security Tests (`@pytest.mark.security`)
- Authentication ve authorization testleri
- Input validation ve sanitization
- SQL injection, XSS prevention testleri

### Specialized Tests
- `@pytest.mark.auth` - Authentication testleri
- `@pytest.mark.crud` - CRUD operation testleri
- `@pytest.mark.metadata` - Metadata testleri
- `@pytest.mark.relationships` - Relationship testleri
- `@pytest.mark.stream` - Stream testleri
- `@pytest.mark.attachments` - Attachment testleri
- `@pytest.mark.logging` - Logging testleri

## Test Çalıştırma

### Hızlı Testler (Önerilen)
```bash
# Sadece hızlı unit testler
python tests/test_runner.py fast

# Veya pytest ile
pytest -m "unit and not slow"
```

### Tüm Testler
```bash
# Tüm testler (yavaş)
python tests/test_runner.py full

# Veya pytest ile
pytest
```

### Belirli Test Kategorileri
```bash
# Authentication testleri
python tests/test_runner.py auth

# CRUD testleri
python tests/test_runner.py crud

# Performance testleri
python tests/test_runner.py performance

# Security testleri
python tests/test_runner.py security
```

### Özel Marker'lar
```bash
# Özel marker kombinasyonu
python tests/test_runner.py --markers unit performance

# Pytest ile
pytest -m "unit and performance"
```

### Mevcut Test Suite'leri
```bash
# Mevcut suite'leri listele
python tests/test_runner.py list
```

## Coverage Raporları

### HTML Coverage Raporu
```bash
pytest --cov=espocrm --cov-report=html
# htmlcov/index.html dosyasını tarayıcıda açın
```

### Terminal Coverage Raporu
```bash
pytest --cov=espocrm --cov-report=term-missing
```

### XML Coverage Raporu (CI/CD için)
```bash
pytest --cov=espocrm --cov-report=xml
```

## Test Fixtures

### Mock EspoCRM Server
```python
def test_example(mock_server):
    # Mock server otomatik olarak HTTP response'ları simüle eder
    mock_server.reset()  # Server state'ini sıfırla
```

### Test Data
```python
def test_example(sample_account, sample_contact):
    # Hazır test entity'leri
    assert sample_account.get("name") == "Test Company"
```

### Authentication
```python
def test_example(api_key_auth, hmac_auth, basic_auth):
    # Farklı auth method'ları test et
```

### Performance Timer
```python
def test_example(performance_timer):
    performance_timer.start()
    # Test kodu
    performance_timer.stop()
    assert performance_timer.elapsed < 1.0
```

## Mock Utilities

### HTTP Mocking
```python
@responses.activate
def test_http_request():
    responses.add(
        responses.GET,
        "https://test.espocrm.com/api/v1/Account/123",
        json={"id": "123", "name": "Test"},
        status=200
    )
```

### Error Simulation
```python
def test_error_handling(error_simulator):
    # Network error
    error_simulator.network_error()
    
    # HTTP error
    error_simulator.http_error(404, "Not Found")
    
    # Rate limit error
    error_simulator.rate_limit_error()
```

## Test Data Factories

### Entity Factory
```python
def test_example():
    account_data = TestDataFactory.create_account(
        name="Custom Company",
        type="Partner"
    )
```

### Response Factory
```python
def test_example():
    list_response = TestDataFactory.create_list_response(
        entities=[entity1, entity2],
        total=2
    )
```

## Paralel Test Çalıştırma

```bash
# Paralel çalıştırma (hızlandırır)
python tests/test_runner.py fast --parallel

# Veya pytest ile
pytest -n auto
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Tests
  run: |
    python tests/test_runner.py fast --format json --output test_results.json
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Test Raporları
```bash
# JSON raporu
python tests/test_runner.py fast --format json --output results.json

# HTML raporu
python tests/test_runner.py fast --format html --output results.html
```

## Test Yazma Rehberi

### Unit Test Örneği
```python
@pytest.mark.unit
@pytest.mark.crud
class TestCRUDClient:
    def test_create_entity_success(self, mock_client, sample_account):
        mock_client.post.return_value = sample_account.data
        
        crud_client = CRUDClient(mock_client)
        result = crud_client.create("Account", {"name": "Test"})
        
        assert isinstance(result, Entity)
        assert result.get("name") == sample_account.get("name")
        mock_client.post.assert_called_once()
```

### Integration Test Örneği
```python
@pytest.mark.integration
@pytest.mark.slow
@responses.activate
def test_full_workflow(real_client, mock_http_responses):
    # 1. Create
    entity = real_client.crud.create("Account", {"name": "Test"})
    
    # 2. Read
    read_entity = real_client.crud.read("Account", entity.id)
    
    # 3. Update
    updated = real_client.crud.update("Account", entity.id, {"type": "Customer"})
    
    # 4. Delete
    deleted = real_client.crud.delete("Account", entity.id)
    
    assert deleted is True
```

### Performance Test Örneği
```python
@pytest.mark.performance
def test_bulk_operations_performance(mock_client, performance_timer):
    performance_timer.start()
    
    # Bulk operations
    for i in range(100):
        mock_client.crud.create("Account", {"name": f"Company {i}"})
    
    performance_timer.stop()
    assert performance_timer.elapsed < 5.0  # 5 saniyeden az
```

### Security Test Örneği
```python
@pytest.mark.security
def test_sql_injection_prevention(mock_client, security_test_data):
    for payload in security_test_data["sql_injection"]:
        with pytest.raises((ValidationError, EspoCRMError)):
            mock_client.crud.create("Account", {"name": payload})
```

## Debugging

### Verbose Output
```bash
python tests/test_runner.py fast --verbose
```

### Specific Test
```bash
pytest tests/test_clients/test_crud.py::TestCRUDClient::test_create_entity_success -v
```

### Debug Mode
```bash
pytest --pdb  # Hata durumunda debugger'a gir
```

## Best Practices

1. **Test İsimlendirme**: `test_method_name_scenario` formatını kullan
2. **Assertions**: Açık ve anlamlı assertion mesajları kullan
3. **Fixtures**: Tekrar kullanılabilir test data için fixture'ları kullan
4. **Mocking**: External dependencies'leri mock'la
5. **Performance**: Performance testlerini `@pytest.mark.slow` ile işaretle
6. **Security**: Security testlerini ayrı kategoride tut
7. **Documentation**: Karmaşık testler için docstring kullan

## Troubleshooting

### Common Issues

1. **Import Errors**: `PYTHONPATH` ayarlandığından emin ol
2. **Mock Failures**: Mock setup'ının doğru olduğunu kontrol et
3. **Slow Tests**: `@pytest.mark.slow` kullan ve fast suite'den çıkar
4. **Flaky Tests**: Timing issues için `time.sleep()` veya proper mocking kullan

### Debug Commands
```bash
# Test discovery
pytest --collect-only

# Markers listesi
pytest --markers

# Fixture listesi
pytest --fixtures
```

## Katkıda Bulunma

Yeni test eklerken:

1. Uygun marker'ları kullan
2. Fixture'ları yeniden kullan
3. Performance impact'ini düşün
4. Documentation ekle
5. Coverage'ı kontrol et

Test suite'i sürekli geliştirilmektedir. Yeni özellikler eklendiğinde ilgili testler de eklenmeli ve mevcut testler güncellenmelidir.