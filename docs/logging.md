# EspoCRM Structured Logging System

EspoCRM Python API istemcisi için professional-grade structured logging sistemi. JSON formatında log çıktısı, context management, sensitive data masking, performance metrics ve external monitoring system integration desteği sunar.

## 🚀 Özellikler

### Core Features
- **Structured Logging**: JSON formatında structured log çıktısı
- **Context Management**: Request ID, user ID, session ID gibi context bilgileri
- **Sensitive Data Masking**: API key'ler, şifreler, PII verilerinin otomatik maskelenmesi
- **Thread-Safe**: Multi-threaded uygulamalar için güvenli
- **Performance Optimized**: Minimal overhead ile yüksek performans

### Formatters
- **JSONFormatter**: Production ortamları için compact JSON formatı
- **ConsoleFormatter**: Development için renkli, human-readable format
- **CompactJSONFormatter**: Yüksek hacimli logging için optimize edilmiş
- **DebugFormatter**: Maximum verbosity ile debug formatı

### Handlers
- **FileHandler**: Thread-safe file logging
- **ConsoleHandler**: Color-aware console output
- **RotatingFileHandler**: Automatic log rotation with compression
- **TimedRotatingHandler**: Time-based log rotation
- **AsyncHandler**: Non-blocking asynchronous logging
- **MonitoringHandler**: External monitoring system integration

### Metrics Collection
- **API Request Metrics**: Response time, success/failure rates
- **Performance Metrics**: Operation timing ve profiling
- **Counter Metrics**: Custom counters with labels
- **Statistics**: Real-time aggregated statistics

## 📦 Kurulum

```bash
# EspoCRM client zaten structlog bağımlılığına sahip
pip install espocrm-python-client
```

## 🔧 Temel Kullanım

### Hızlı Başlangıç

```python
from espocrm.logging import configure_espocrm_logging, get_logger

# Logging sistemini konfigüre et
configure_espocrm_logging(
    level='INFO',
    log_file='logs/espocrm.log',
    enable_console=True,
    enable_metrics=True,
    production_mode=False
)

# Logger oluştur
logger = get_logger('espocrm.client')

# Temel logging
logger.info('EspoCRM client başlatıldı')
logger.warning('Rate limit yaklaşıyor', remaining_requests=10)
logger.error('API hatası', error_code='VALIDATION_ERROR')
```

### Context Management

```python
# Request ID oluştur ve context'e ekle
request_id = logger.generate_request_id()
logger.set_context(
    user_id='user_12345',
    session_id='sess_abcdef',
    client_version='1.0.0'
)

# Context ile log
logger.info('Kullanıcı işlemi', action='create_lead', success=True)

# Context temizle
logger.clear_context()
```

### API Call Logging

```python
# Başarılı API call
logger.log_api_call(
    method='GET',
    endpoint='/api/v1/Lead',
    status_code=200,
    execution_time_ms=145.5,
    record_count=25
)

# Hatalı API call
logger.log_api_call(
    method='POST',
    endpoint='/api/v1/Contact',
    status_code=400,
    execution_time_ms=89.2,
    error_code='VALIDATION_ERROR'
)
```

### Sensitive Data Masking

```python
# Sensitive data otomatik olarak maskelenir
sensitive_data = {
    'email': 'john.doe@example.com',
    'password': 'super_secret_password',
    'api_key': 'sk_live_1234567890abcdef',
    'credit_card': '4111-1111-1111-1111'
}

logger.info('Kullanıcı verisi işlendi', data=sensitive_data)
# Output: email: "jo***@example.com", password: "***MASKED***", etc.
```

## 📊 Metrics Collection

### Performance Monitoring

```python
from espocrm.logging import time_operation, record_performance

# Timer ile operation timing
with time_operation('database_query', context={'table': 'leads'}):
    # Your database operation
    results = db.query('SELECT * FROM leads')

# Manuel performance logging
import time
start_time = time.perf_counter()
# Your operation
duration_ms = (time.perf_counter() - start_time) * 1000
record_performance('api_call', duration_ms, context={'endpoint': '/api/v1/Lead'})
```

### API Request Metrics

```python
from espocrm.logging import record_request, increment_counter

# API request metrics
record_request('GET', '/api/v1/Lead', status_code=200, response_time_ms=120.5)
record_request('POST', '/api/v1/Lead', status_code=201, response_time_ms=245.8)

# Counter metrics
increment_counter('api_calls_total', labels={'method': 'GET', 'endpoint': '/api/v1/Lead'})
increment_counter('errors_total', labels={'type': 'validation_error'})
```

### Statistics

```python
from espocrm.logging import get_stats
from datetime import timedelta

# Son 5 dakikanın istatistikleri
stats = get_stats(time_window=timedelta(minutes=5))
print(f"Success rate: {stats['requests']['success_rate']:.2%}")
print(f"Average response time: {stats['requests']['avg_response_time']:.2f}ms")
```

## 🏭 Production Configuration

### Production Logger

```python
from espocrm.logging import create_production_logger

logger = create_production_logger(
    name='espocrm.client',
    log_file='/var/log/espocrm/client.log',
    level='INFO',
    enable_console=False,
    enable_monitoring=True,
    max_size=50 * 1024 * 1024,  # 50MB
    backup_count=10
)
```

### Development Logger

```python
from espocrm.logging import create_development_logger

logger = create_development_logger(
    name='espocrm.client',
    level='DEBUG',
    log_file='logs/debug.log',
    enable_async=True
)
```

## 🔒 Security Features

### Sensitive Data Masking

Sistem otomatik olarak şu tür verileri maskeler:

**Credential Fields:**
- `password`, `passwd`, `pwd`
- `secret`, `token`, `key`
- `api_key`, `apikey`
- `authorization`, `credential`
- `private_key`, `access_token`

**PII Fields:**
- `email` → `jo***@example.com`
- `phone`, `mobile` → `12***89`
- `credit_card` → `41***11`
- `ssn`, `account_number` → `12***89`

### Log Injection Prevention

Tüm log mesajları otomatik olarak sanitize edilir ve injection saldırılarına karşı korunur.

## 📈 Monitoring Integration

### Prometheus Metrics

```python
from espocrm.logging import MonitoringHandler

def prometheus_callback(record, log_counts, error_counts):
    # Prometheus metrics'e gönder
    prometheus_counter.labels(
        level=record.levelname,
        logger=record.name
    ).inc()

monitoring_handler = MonitoringHandler(
    metrics_callback=prometheus_callback,
    error_threshold=logging.ERROR
)
```

### External Monitoring

```python
def alert_callback(record):
    if record.levelno >= logging.ERROR:
        # Slack, PagerDuty, etc. alert gönder
        send_alert(f"Error in {record.name}: {record.getMessage()}")

monitoring_handler = MonitoringHandler(
    alert_callback=alert_callback
)
```

## 🎯 Log Format Examples

### JSON Format (Production)

```json
{
    "timestamp": "2025-01-02T14:48:00Z",
    "level": "INFO",
    "logger": "espocrm.client.crud",
    "message": "Creating new Lead record",
    "context": {
        "method": "POST",
        "endpoint": "/api/v1/Lead",
        "request_id": "req_123456",
        "user_id": "api_user_001",
        "execution_time_ms": 245
    },
    "data": {
        "entity_type": "Lead",
        "fields": ["firstName", "lastName", "emailAddress"]
    }
}
```

### Console Format (Development)

```
2025-01-02T14:48:00Z INFO     [espocrm.client.crud ] Creating new Lead record
  Context: request_id=req_123456, user_id=api_user_001, execution_time_ms=245
  Data: entity_type="Lead", fields=["firstName", "lastName", "emailAddress"]
```

## ⚡ Performance Tips

### Async Logging

```python
from espocrm.logging import create_async_handler, create_file_handler

# Async wrapper ile non-blocking logging
file_handler = create_file_handler('logs/app.log')
async_handler = create_async_handler(file_handler, queue_size=1000)
```

### Log Level Optimization

```python
# Production'da DEBUG level'ı kapatın
configure_espocrm_logging(level='INFO')

# Critical path'lerde conditional logging
if logger.isEnabledFor(logging.DEBUG):
    logger.debug('Expensive debug info', data=expensive_operation())
```

### Batch Metrics

```python
# Metrics'i batch olarak işleyin
metrics_collector = get_metrics_collector()
metrics_collector.add_metric_callback(batch_processor)
```

## 🧪 Testing

Logging sistemini test etmek için örnek dosyayı çalıştırın:

```bash
cd /path/to/espocrm-python-client
PYTHONPATH=. python examples/logging_example.py
```

Bu örnek şunları test eder:
- Temel logging functionality
- Context management
- API call logging
- Sensitive data masking
- Performance metrics
- Exception handling
- Statistics collection

## 📚 API Reference

### Core Classes

- [`StructuredLogger`](espocrm/logging/logger.py:178): Ana logger sınıfı
- [`MetricsCollector`](espocrm/logging/metrics.py:298): Metrics collection sistemi
- [`SensitiveDataMasker`](espocrm/logging/logger.py:32): Sensitive data masking utility

### Factory Functions

- [`get_logger()`](espocrm/logging/logger.py:360): Logger oluştur
- [`configure_espocrm_logging()`](espocrm/logging/__init__.py:280): Sistem konfigürasyonu
- [`create_production_logger()`](espocrm/logging/__init__.py:200): Production logger
- [`create_development_logger()`](espocrm/logging/__init__.py:240): Development logger

### Metrics Functions

- [`record_request()`](espocrm/logging/metrics.py:570): API request metrics
- [`record_performance()`](espocrm/logging/metrics.py:574): Performance metrics
- [`time_operation()`](espocrm/logging/metrics.py:582): Operation timing
- [`get_stats()`](espocrm/logging/metrics.py:586): Statistics

## 🤝 Contributing

Logging sistemine katkıda bulunmak için:

1. Issue oluşturun veya mevcut issue'yu seçin
2. Feature branch oluşturun
3. Testlerinizi yazın
4. Pull request gönderin

## 📄 License

MIT License - Detaylar için [LICENSE](../LICENSE) dosyasına bakın.