"""
EspoCRM Client Usage Example

Bu örnek EspoCRM ana client sınıfının temel kullanımını gösterir.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from espocrm import (
    EspoCRMClient,
    ClientConfig,
    APIKeyAuth,
    configure_espocrm_logging,
    get_logger
)
from espocrm.exceptions import EspoCRMError


def main():
    """Ana örnek fonksiyon."""
    
    # Logging'i konfigüre et
    configure_espocrm_logging(
        level='INFO',
        enable_console=True,
        enable_metrics=True,
        production_mode=False
    )
    
    logger = get_logger('example')
    logger.info("EspoCRM Client example started")
    
    try:
        # Konfigürasyon oluştur
        config = ClientConfig(
            base_url="https://demo.espocrm.com",  # Demo URL
            api_key="demo-api-key",  # Demo API key
            timeout=30.0,
            max_retries=3,
            debug=True
        )
        
        # Authentication oluştur
        auth = APIKeyAuth(api_key=config.api_key)
        
        # Client oluştur ve context manager ile kullan
        with EspoCRMClient(config.base_url, auth, config) as client:
            logger.info("Client created successfully")
            
            # Bağlantı testi (bu demo URL'de çalışmayabilir)
            try:
                logger.info("Testing connection...")
                is_connected = client.test_connection()
                logger.info(f"Connection test result: {is_connected}")
            except EspoCRMError as e:
                logger.warning(f"Connection test failed (expected for demo): {e}")
            
            # Server bilgilerini al (bu da demo URL'de çalışmayabilir)
            try:
                logger.info("Getting server info...")
                server_info = client.get_server_info()
                logger.info(f"Server info: {server_info}")
            except EspoCRMError as e:
                logger.warning(f"Could not get server info (expected for demo): {e}")
            
            # Request context örneği
            with client.request_context() as request_id:
                logger.info(f"Request context created with ID: {request_id}")
                
                # Örnek GET request (bu da demo URL'de çalışmayabilir)
                try:
                    logger.info("Making example GET request...")
                    response = client.get('Account', params={'maxSize': 10})
                    logger.info(f"GET response: {response}")
                except EspoCRMError as e:
                    logger.warning(f"GET request failed (expected for demo): {e}")
            
            logger.info("Client operations completed")
    
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise
    
    logger.info("EspoCRM Client example completed")


if __name__ == "__main__":
    main()