#!/usr/bin/env python3
"""
EspoCRM Structured Logging System Example

Bu örnek, EspoCRM structured logging sisteminin temel kullanımını gösterir:
- Logger oluşturma ve konfigürasyon
- Context management
- API call logging
- Performance metrics
- Sensitive data masking
"""

import time
import json
from datetime import timedelta
from pathlib import Path

# EspoCRM logging sistemini import et
from espocrm.logging import (
    configure_espocrm_logging,
    get_logger,
    get_metrics_collector,
    time_operation,
    record_request,
    record_performance,
    increment_counter,
    get_stats
)


def main():
    """Ana örnek fonksiyon"""
    print("🚀 EspoCRM Structured Logging System Example")
    print("=" * 50)
    
    # 1. Logging sistemini konfigüre et
    print("\n1. Logging sistemini konfigüre ediliyor...")
    
    config = configure_espocrm_logging(
        level='INFO',
        log_file='logs/espocrm_example.log',
        enable_console=True,
        enable_metrics=True,
        enable_masking=True,
        production_mode=False
    )
    
    print(f"✅ Logging konfigürasyonu tamamlandı:")
    print(json.dumps(config, indent=2, default=str))
    
    # 2. Logger oluştur
    print("\n2. Logger oluşturuluyor...")
    logger = get_logger('espocrm.example')
    
    # 3. Temel logging örnekleri
    print("\n3. Temel logging örnekleri...")
    
    logger.info("EspoCRM client başlatıldı")
    logger.debug("Debug bilgisi", debug_data={'version': '1.0.0', 'mode': 'example'})
    logger.warning("Uyarı mesajı", warning_type='rate_limit', remaining_requests=10)
    
    # 4. Context management örneği
    print("\n4. Context management örneği...")
    
    # Request ID oluştur ve context'e ekle
    request_id = logger.generate_request_id()
    logger.set_context(
        user_id='user_12345',
        session_id='sess_abcdef',
        client_version='1.0.0'
    )
    
    logger.info("Context ile log mesajı", action='user_login', success=True)
    
    # 5. API call logging örneği
    print("\n5. API call logging örneği...")
    
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
        error_code='VALIDATION_ERROR',
        error_message='Email field is required'
    )
    
    # 6. Sensitive data masking örneği
    print("\n6. Sensitive data masking örneği...")
    
    sensitive_data = {
        'user_id': 'user_12345',
        'email': 'john.doe@example.com',
        'password': 'super_secret_password',
        'api_key': 'sk_live_1234567890abcdef',
        'credit_card': '4111-1111-1111-1111',
        'normal_field': 'this should not be masked'
    }
    
    logger.info("Kullanıcı verisi işlendi", data=sensitive_data)
    
    # 7. Performance monitoring örneği
    print("\n7. Performance monitoring örneği...")
    
    # Timer ile operation timing
    with time_operation('database_query', context={'table': 'leads', 'operation': 'select'}):
        time.sleep(0.1)  # Simulated database operation
    
    # Manuel performance logging
    start_time = time.perf_counter()
    time.sleep(0.05)  # Simulated API call
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    record_performance(
        operation='external_api_call',
        duration_ms=duration_ms,
        context={'service': 'email_validation', 'provider': 'external'}
    )
    
    # 8. Metrics collection örneği
    print("\n8. Metrics collection örneği...")
    
    metrics = get_metrics_collector()
    
    # API request metrics
    record_request('GET', '/api/v1/Lead', status_code=200, response_time_ms=120.5)
    record_request('POST', '/api/v1/Lead', status_code=201, response_time_ms=245.8)
    record_request('GET', '/api/v1/Contact', status_code=404, response_time_ms=89.2)
    record_request('PUT', '/api/v1/Lead/123', status_code=500, response_time_ms=1205.3)
    
    # Counter metrics
    increment_counter('api_calls_total', labels={'method': 'GET', 'endpoint': '/api/v1/Lead'})
    increment_counter('api_calls_total', labels={'method': 'POST', 'endpoint': '/api/v1/Lead'})
    increment_counter('errors_total', labels={'type': 'validation_error'})
    increment_counter('errors_total', labels={'type': 'server_error'})
    
    # 9. Exception handling örneği
    print("\n9. Exception handling örneği...")
    
    try:
        # Simulated error
        raise ValueError("Bu bir test hatası")
    except Exception as e:
        logger.exception("İşlem sırasında hata oluştu", 
                        operation='data_processing',
                        error_type=type(e).__name__)
    
    # 10. Metrics istatistikleri
    print("\n10. Metrics istatistikleri...")
    
    stats = get_stats(time_window=timedelta(minutes=5))
    print("📊 Son 5 dakikanın istatistikleri:")
    print(json.dumps(stats, indent=2, default=str))
    
    # 11. Context temizleme
    print("\n11. Context temizleniyor...")
    logger.clear_context()
    logger.info("Context temizlendi", final_message=True)
    
    print("\n✅ Örnek tamamlandı!")
    print(f"📁 Log dosyası: {Path('logs/espocrm_example.log').absolute()}")


if __name__ == '__main__':
    main()