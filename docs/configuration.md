# Configuration Guide

EspoCRM Python Client provides flexible configuration options to suit different deployment scenarios and security requirements.

## Configuration Methods

### 1. Direct Configuration

The most straightforward way to configure the client:

```python
from espocrm import EspoCRMClient
from espocrm.auth import APIKeyAuth

auth = APIKeyAuth("your-api-key")
client = EspoCRMClient("https://your-espocrm.com", auth)
```

### 2. Using Configuration Object

For more complex configurations:

```python
from espocrm import EspoCRMClient
from espocrm.config import ClientConfig
from espocrm.auth import APIKeyAuth

config = ClientConfig(
    base_url="https://your-espocrm.com",
    timeout=30,
    max_retries=3,
    retry_delay=1.0,
    verify_ssl=True,
    user_agent="MyApp/1.0"
)

auth = APIKeyAuth("your-api-key")
client = EspoCRMClient.from_config(config, auth)
```

### 3. Environment Variables

The recommended approach for production deployments:

```bash
# Required
export ESPOCRM_URL="https://your-espocrm.com"
export ESPOCRM_API_KEY="your-api-key"

# Optional
export ESPOCRM_TIMEOUT="30"
export ESPOCRM_MAX_RETRIES="3"
export ESPOCRM_RETRY_DELAY="1.0"
export ESPOCRM_VERIFY_SSL="true"
export ESPOCRM_USER_AGENT="MyApp/1.0"
```

```python
from espocrm import create_client

# Automatically uses environment variables
client = create_client()
```

### 4. Configuration File

Using a configuration file (JSON, YAML, or TOML):

=== "JSON Configuration"

    ```json
    {
      "espocrm": {
        "base_url": "https://your-espocrm.com",
        "api_key": "your-api-key",
        "timeout": 30,
        "max_retries": 3,
        "retry_delay": 1.0,
        "verify_ssl": true,
        "user_agent": "MyApp/1.0"
      }
    }
    ```

=== "YAML Configuration"

    ```yaml
    espocrm:
      base_url: "https://your-espocrm.com"
      api_key: "your-api-key"
      timeout: 30
      max_retries: 3
      retry_delay: 1.0
      verify_ssl: true
      user_agent: "MyApp/1.0"
    ```

=== "TOML Configuration"

    ```toml
    [espocrm]
    base_url = "https://your-espocrm.com"
    api_key = "your-api-key"
    timeout = 30
    max_retries = 3
    retry_delay = 1.0
    verify_ssl = true
    user_agent = "MyApp/1.0"
    ```

```python
import json
from espocrm import EspoCRMClient
from espocrm.config import ClientConfig
from espocrm.auth import APIKeyAuth

# Load configuration from file
with open('config.json', 'r') as f:
    config_data = json.load(f)['espocrm']

config = ClientConfig(
    base_url=config_data['base_url'],
    timeout=config_data.get('timeout', 30),
    max_retries=config_data.get('max_retries', 3),
    retry_delay=config_data.get('retry_delay', 1.0),
    verify_ssl=config_data.get('verify_ssl', True),
    user_agent=config_data.get('user_agent', 'EspoCRM-Python-Client')
)

auth = APIKeyAuth(config_data['api_key'])
client = EspoCRMClient.from_config(config, auth)
```

## Configuration Options

### Core Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base_url` | `str` | Required | EspoCRM instance URL |
| `timeout` | `int` | `30` | Request timeout in seconds |
| `max_retries` | `int` | `3` | Maximum number of retry attempts |
| `retry_delay` | `float` | `1.0` | Delay between retries in seconds |
| `verify_ssl` | `bool` | `True` | Verify SSL certificates |
| `user_agent` | `str` | `EspoCRM-Python-Client/{version}` | HTTP User-Agent header |

### HTTP Settings

```python
from espocrm.config import ClientConfig

config = ClientConfig(
    base_url="https://your-espocrm.com",
    
    # Connection settings
    timeout=60,  # 60 seconds timeout
    connect_timeout=10,  # 10 seconds connection timeout
    read_timeout=50,  # 50 seconds read timeout
    
    # Retry settings
    max_retries=5,
    retry_delay=2.0,
    retry_backoff_factor=2.0,  # Exponential backoff
    retry_on_status=[500, 502, 503, 504],  # Retry on these HTTP status codes
    
    # SSL settings
    verify_ssl=True,
    ssl_cert_path="/path/to/cert.pem",  # Client certificate
    ssl_key_path="/path/to/key.pem",   # Client private key
    
    # Headers
    user_agent="MyApp/1.0",
    custom_headers={
        "X-Custom-Header": "value",
        "X-App-Version": "1.0.0"
    }
)
```

### Logging Configuration

```python
from espocrm.config import ClientConfig
from espocrm.logging import setup_logging

# Setup logging first
setup_logging(
    level="INFO",
    format="json",
    output_file="espocrm.log"
)

config = ClientConfig(
    base_url="https://your-espocrm.com",
    
    # Logging settings
    log_requests=True,  # Log all HTTP requests
    log_responses=True,  # Log all HTTP responses
    log_level="DEBUG",  # Override log level for this client
    
    # Performance logging
    log_performance=True,  # Log request timing
    slow_request_threshold=5.0,  # Log requests slower than 5 seconds
)
```

### Connection Pooling

```python
from espocrm.config import ClientConfig

config = ClientConfig(
    base_url="https://your-espocrm.com",
    
    # Connection pool settings
    pool_connections=10,  # Number of connection pools
    pool_maxsize=20,      # Maximum connections per pool
    pool_block=False,     # Don't block when pool is full
    
    # Keep-alive settings
    keep_alive=True,
    keep_alive_timeout=30,
)
```

## Environment Variables Reference

### Required Variables

```bash
# EspoCRM instance URL
ESPOCRM_URL="https://your-espocrm.com"

# Authentication (choose one)
ESPOCRM_API_KEY="your-api-key"
# OR
ESPOCRM_USERNAME="username"
ESPOCRM_PASSWORD="password"
# OR
ESPOCRM_HMAC_KEY="hmac-key"
ESPOCRM_HMAC_SECRET="hmac-secret"
```

### Optional Variables

```bash
# HTTP settings
ESPOCRM_TIMEOUT="30"
ESPOCRM_CONNECT_TIMEOUT="10"
ESPOCRM_READ_TIMEOUT="20"
ESPOCRM_MAX_RETRIES="3"
ESPOCRM_RETRY_DELAY="1.0"
ESPOCRM_RETRY_BACKOFF_FACTOR="2.0"

# SSL settings
ESPOCRM_VERIFY_SSL="true"
ESPOCRM_SSL_CERT_PATH="/path/to/cert.pem"
ESPOCRM_SSL_KEY_PATH="/path/to/key.pem"

# Headers
ESPOCRM_USER_AGENT="MyApp/1.0"

# Logging
ESPOCRM_LOG_LEVEL="INFO"
ESPOCRM_LOG_REQUESTS="false"
ESPOCRM_LOG_RESPONSES="false"
ESPOCRM_LOG_PERFORMANCE="false"

# Connection pooling
ESPOCRM_POOL_CONNECTIONS="10"
ESPOCRM_POOL_MAXSIZE="20"
ESPOCRM_KEEP_ALIVE="true"
ESPOCRM_KEEP_ALIVE_TIMEOUT="30"
```

## Configuration Validation

The client automatically validates configuration settings:

```python
from espocrm.config import ClientConfig
from espocrm.exceptions import EspoCRMValidationError

try:
    config = ClientConfig(
        base_url="invalid-url",  # Invalid URL format
        timeout=-1,              # Invalid timeout value
        max_retries="invalid"    # Invalid type
    )
except EspoCRMValidationError as e:
    print(f"Configuration validation failed: {e}")
```

## Default Configuration

You can set default configuration that applies to all clients:

```python
from espocrm.config import set_default_config, get_default_config, ClientConfig

# Set default configuration
default_config = ClientConfig(
    timeout=60,
    max_retries=5,
    verify_ssl=True,
    log_requests=True
)
set_default_config(default_config)

# All new clients will use these defaults
from espocrm import EspoCRMClient
from espocrm.auth import APIKeyAuth

auth = APIKeyAuth("your-api-key")
client = EspoCRMClient("https://your-espocrm.com", auth)
# This client will use the default configuration

# Get current default configuration
current_default = get_default_config()
```

## Configuration Profiles

For different environments (development, staging, production):

```python
import os
from espocrm.config import ClientConfig

def get_config_for_environment(env: str = None) -> ClientConfig:
    """Get configuration based on environment."""
    env = env or os.getenv('ENVIRONMENT', 'development')
    
    if env == 'development':
        return ClientConfig(
            base_url="https://dev-espocrm.com",
            timeout=10,
            max_retries=1,
            verify_ssl=False,  # For self-signed certificates
            log_requests=True,
            log_responses=True
        )
    elif env == 'staging':
        return ClientConfig(
            base_url="https://staging-espocrm.com",
            timeout=30,
            max_retries=3,
            verify_ssl=True,
            log_requests=True,
            log_performance=True
        )
    elif env == 'production':
        return ClientConfig(
            base_url="https://espocrm.com",
            timeout=60,
            max_retries=5,
            retry_backoff_factor=2.0,
            verify_ssl=True,
            log_requests=False,  # Reduce logging in production
            log_responses=False,
            pool_connections=20,
            pool_maxsize=50
        )
    else:
        raise ValueError(f"Unknown environment: {env}")

# Usage
config = get_config_for_environment()
```

## Security Best Practices

### 1. Credential Management

Never hardcode credentials in your source code:

```python
# ❌ Bad - credentials in code
auth = APIKeyAuth("abc123-secret-key")

# ✅ Good - credentials from environment
import os
auth = APIKeyAuth(os.getenv('ESPOCRM_API_KEY'))

# ✅ Better - use a secrets management service
from your_secrets_manager import get_secret
auth = APIKeyAuth(get_secret('espocrm-api-key'))
```

### 2. SSL Configuration

Always verify SSL certificates in production:

```python
# ✅ Production configuration
config = ClientConfig(
    base_url="https://your-espocrm.com",
    verify_ssl=True,  # Always verify SSL
    ssl_cert_path="/path/to/client-cert.pem",  # Client certificate if required
    ssl_key_path="/path/to/client-key.pem"    # Client private key
)

# ⚠️ Development only - disable SSL verification
if os.getenv('ENVIRONMENT') == 'development':
    config.verify_ssl = False
```

### 3. Network Security

Configure appropriate timeouts and limits:

```python
config = ClientConfig(
    base_url="https://your-espocrm.com",
    timeout=30,        # Prevent hanging requests
    max_retries=3,     # Limit retry attempts
    retry_delay=1.0,   # Prevent rapid retry attacks
    
    # Rate limiting (if supported by your proxy/firewall)
    custom_headers={
        "X-Rate-Limit": "100/hour"
    }
)
```

## Configuration Testing

Test your configuration before deploying:

```python
from espocrm import EspoCRMClient
from espocrm.config import ClientConfig
from espocrm.auth import APIKeyAuth
from espocrm.exceptions import EspoCRMError

def test_configuration(config: ClientConfig, auth) -> bool:
    """Test if configuration works correctly."""
    try:
        client = EspoCRMClient.from_config(config, auth)
        
        # Test connection
        metadata = client.metadata.get_app_metadata()
        print(f"✅ Connection successful - EspoCRM v{metadata.version}")
        
        # Test basic operations
        leads = client.crud.list("Lead", limit=1)
        print(f"✅ API access successful - found {leads.total} leads")
        
        return True
        
    except EspoCRMError as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

# Test your configuration
config = ClientConfig(base_url="https://your-espocrm.com")
auth = APIKeyAuth("your-api-key")

if test_configuration(config, auth):
    print("Configuration is valid!")
else:
    print("Please check your configuration.")
```

## Troubleshooting

### Common Configuration Issues

#### 1. SSL Certificate Errors

```python
# If you get SSL certificate errors
config = ClientConfig(
    base_url="https://your-espocrm.com",
    verify_ssl=False  # Temporary workaround
)

# Better solution: Add certificate to trust store
# or provide custom CA bundle
config = ClientConfig(
    base_url="https://your-espocrm.com",
    verify_ssl="/path/to/ca-bundle.pem"
)
```

#### 2. Timeout Issues

```python
# Increase timeouts for slow networks
config = ClientConfig(
    base_url="https://your-espocrm.com",
    timeout=120,        # 2 minutes total timeout
    connect_timeout=30, # 30 seconds to connect
    read_timeout=90     # 90 seconds to read response
)
```

#### 3. Connection Pool Exhaustion

```python
# Increase connection pool size
config = ClientConfig(
    base_url="https://your-espocrm.com",
    pool_connections=20,  # More connection pools
    pool_maxsize=50,      # More connections per pool
    pool_block=True       # Block when pool is full instead of failing
)
```

## Next Steps

- [Authentication Setup](authentication.md) - Configure authentication methods
- [Quick Start Guide](quickstart.md) - Start using the client
- [Error Handling](advanced/error-handling.md) - Handle configuration errors
- [Performance Tuning](advanced/performance.md) - Optimize configuration for performance