# Authentication Guide

EspoCRM Python Client supports multiple authentication methods to suit different security requirements and deployment scenarios.

## Overview

The client supports three main authentication methods:

1. **API Key Authentication** - Recommended for most applications
2. **Basic Authentication** - Username and password
3. **HMAC Authentication** - Enhanced security with cryptographic signatures

## API Key Authentication

### Setup in EspoCRM

1. Log in to your EspoCRM instance as an administrator
2. Go to **Administration** → **API Users**
3. Create a new API user or select an existing one
4. Generate an API key for the user
5. Set appropriate permissions and access levels

### Usage

```python
from espocrm import EspoCRMClient
from espocrm.auth import APIKeyAuth

# Create authentication object
auth = APIKeyAuth("your-api-key-here")

# Initialize client
client = EspoCRMClient("https://your-espocrm.com", auth)
```

### Environment Variables

```bash
export ESPOCRM_URL="https://your-espocrm.com"
export ESPOCRM_API_KEY="your-api-key-here"
```

```python
from espocrm import create_client

# Automatically uses environment variables
client = create_client()
```

### Security Considerations

- API keys should be treated as passwords
- Store API keys securely (environment variables, secrets management)
- Rotate API keys regularly
- Use different API keys for different applications/environments
- Monitor API key usage in EspoCRM logs

## Basic Authentication

### Setup in EspoCRM

1. Ensure the user account exists in EspoCRM
2. The user must have API access permissions
3. Enable basic authentication in EspoCRM API settings

### Usage

```python
from espocrm import EspoCRMClient
from espocrm.auth import BasicAuth

# Create authentication object
auth = BasicAuth("username", "password")

# Initialize client
client = EspoCRMClient("https://your-espocrm.com", auth)
```

### Environment Variables

```bash
export ESPOCRM_URL="https://your-espocrm.com"
export ESPOCRM_USERNAME="your-username"
export ESPOCRM_PASSWORD="your-password"
```

```python
from espocrm.config import create_config_from_env
from espocrm import EspoCRMClient
from espocrm.auth import BasicAuth
import os

# Create client with environment variables
auth = BasicAuth(
    os.getenv('ESPOCRM_USERNAME'),
    os.getenv('ESPOCRM_PASSWORD')
)
client = EspoCRMClient(os.getenv('ESPOCRM_URL'), auth)
```

### Security Considerations

- Less secure than API key authentication
- Credentials are sent with every request
- Use HTTPS to encrypt credentials in transit
- Consider using application-specific passwords
- Enable two-factor authentication for the user account

## HMAC Authentication

HMAC (Hash-based Message Authentication Code) provides the highest level of security by signing each request with a cryptographic signature.

### Setup in EspoCRM

1. Create an API user in EspoCRM
2. Generate both an API key and a secret key
3. Configure HMAC authentication in EspoCRM API settings

### Usage

```python
from espocrm import EspoCRMClient
from espocrm.auth import HMACAuth

# Create authentication object
auth = HMACAuth("your-api-key", "your-secret-key")

# Initialize client
client = EspoCRMClient("https://your-espocrm.com", auth)
```

### Environment Variables

```bash
export ESPOCRM_URL="https://your-espocrm.com"
export ESPOCRM_HMAC_KEY="your-api-key"
export ESPOCRM_HMAC_SECRET="your-secret-key"
```

```python
from espocrm import EspoCRMClient
from espocrm.auth import HMACAuth
import os

# Create client with environment variables
auth = HMACAuth(
    os.getenv('ESPOCRM_HMAC_KEY'),
    os.getenv('ESPOCRM_HMAC_SECRET')
)
client = EspoCRMClient(os.getenv('ESPOCRM_URL'), auth)
```

### How HMAC Works

1. Each request is signed with HMAC-SHA256
2. The signature includes the request method, URL, headers, and body
3. EspoCRM verifies the signature on the server side
4. Requests with invalid signatures are rejected

### Security Benefits

- Prevents request tampering
- Protects against replay attacks (when combined with timestamps)
- Secret key is never transmitted
- Each request has a unique signature

## Custom Authentication

You can implement custom authentication by extending the base authentication class:

```python
from espocrm.auth.base import AuthenticationBase
from typing import Dict, Any

class CustomAuth(AuthenticationBase):
    """Custom authentication implementation."""
    
    def __init__(self, token: str, additional_param: str):
        self.token = token
        self.additional_param = additional_param
    
    def get_headers(self) -> Dict[str, str]:
        """Return authentication headers."""
        return {
            "Authorization": f"Custom {self.token}",
            "X-Custom-Param": self.additional_param
        }
    
    def get_auth_params(self) -> Dict[str, Any]:
        """Return authentication parameters for URL."""
        return {}
    
    def is_valid(self) -> bool:
        """Check if authentication is valid."""
        return bool(self.token and self.additional_param)

# Usage
auth = CustomAuth("your-token", "additional-value")
client = EspoCRMClient("https://your-espocrm.com", auth)
```

## Authentication Testing

### Test Connection

```python
from espocrm.exceptions import EspoCRMAuthenticationError

def test_authentication(client):
    """Test if authentication is working."""
    try:
        # Try to get application metadata
        metadata = client.metadata.get_app_metadata()
        print(f"✅ Authentication successful - EspoCRM v{metadata.version}")
        return True
    except EspoCRMAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

# Test your authentication
if test_authentication(client):
    print("Ready to use the client!")
else:
    print("Please check your authentication settings.")
```

### Validate Credentials

```python
from espocrm.auth import APIKeyAuth

def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key:
        return False
    
    # Basic format validation
    if len(api_key) < 16:
        return False
    
    # Check for common patterns
    if api_key.startswith('test') or api_key == 'your-api-key':
        return False
    
    return True

# Validate before using
api_key = "your-api-key"
if validate_api_key(api_key):
    auth = APIKeyAuth(api_key)
else:
    print("Invalid API key format")
```

## Authentication Best Practices

### 1. Credential Storage

```python
# ❌ Bad - hardcoded credentials
auth = APIKeyAuth("abc123-hardcoded-key")

# ✅ Good - environment variables
import os
auth = APIKeyAuth(os.getenv('ESPOCRM_API_KEY'))

# ✅ Better - secrets management service
from your_secrets_manager import get_secret
auth = APIKeyAuth(get_secret('espocrm-api-key'))
```

### 2. Credential Rotation

```python
import os
from datetime import datetime, timedelta

class RotatingAPIKeyAuth:
    """API key authentication with automatic rotation."""
    
    def __init__(self, primary_key: str, backup_key: str = None):
        self.primary_key = primary_key
        self.backup_key = backup_key
        self.last_rotation = datetime.now()
        self.rotation_interval = timedelta(days=30)
    
    def get_current_key(self) -> str:
        """Get the current API key, rotating if necessary."""
        if self.should_rotate():
            self.rotate_key()
        return self.primary_key
    
    def should_rotate(self) -> bool:
        """Check if key should be rotated."""
        return datetime.now() - self.last_rotation > self.rotation_interval
    
    def rotate_key(self):
        """Rotate to backup key and request new primary key."""
        if self.backup_key:
            self.primary_key = self.backup_key
            self.backup_key = None  # Request new backup key
            self.last_rotation = datetime.now()
            print("🔄 API key rotated")
```

### 3. Multiple Environments

```python
import os
from espocrm.auth import APIKeyAuth

def get_auth_for_environment(env: str = None):
    """Get authentication based on environment."""
    env = env or os.getenv('ENVIRONMENT', 'development')
    
    if env == 'development':
        return APIKeyAuth(os.getenv('ESPOCRM_DEV_API_KEY'))
    elif env == 'staging':
        return APIKeyAuth(os.getenv('ESPOCRM_STAGING_API_KEY'))
    elif env == 'production':
        return APIKeyAuth(os.getenv('ESPOCRM_PROD_API_KEY'))
    else:
        raise ValueError(f"Unknown environment: {env}")

# Usage
auth = get_auth_for_environment()
```

### 4. Authentication Middleware

```python
from espocrm.auth.base import AuthenticationBase
import time
import hashlib

class TimestampedHMACAuth(AuthenticationBase):
    """HMAC authentication with timestamp to prevent replay attacks."""
    
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
    
    def get_headers(self) -> Dict[str, str]:
        timestamp = str(int(time.time()))
        signature = self._generate_signature(timestamp)
        
        return {
            "X-API-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }
    
    def _generate_signature(self, timestamp: str) -> str:
        """Generate HMAC signature with timestamp."""
        import hmac
        message = f"{self.api_key}:{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
```

## Error Handling

### Authentication Errors

```python
from espocrm.exceptions import (
    EspoCRMAuthenticationError,
    EspoCRMAuthorizationError,
    EspoCRMError
)

try:
    client = EspoCRMClient("https://your-espocrm.com", auth)
    leads = client.crud.list("Lead")
    
except EspoCRMAuthenticationError as e:
    print(f"❌ Authentication failed: {e}")
    print("Please check your credentials")
    
except EspoCRMAuthorizationError as e:
    print(f"❌ Authorization failed: {e}")
    print("Your account doesn't have permission for this operation")
    
except EspoCRMError as e:
    print(f"❌ API error: {e}")
```

### Retry with Different Authentication

```python
from espocrm.exceptions import EspoCRMAuthenticationError

def try_multiple_auth_methods(base_url: str, credentials: dict):
    """Try multiple authentication methods."""
    
    # Try API key first
    if 'api_key' in credentials:
        try:
            auth = APIKeyAuth(credentials['api_key'])
            client = EspoCRMClient(base_url, auth)
            client.metadata.get_app_metadata()  # Test connection
            return client
        except EspoCRMAuthenticationError:
            print("API key authentication failed, trying basic auth...")
    
    # Try basic authentication
    if 'username' in credentials and 'password' in credentials:
        try:
            auth = BasicAuth(credentials['username'], credentials['password'])
            client = EspoCRMClient(base_url, auth)
            client.metadata.get_app_metadata()  # Test connection
            return client
        except EspoCRMAuthenticationError:
            print("Basic authentication failed, trying HMAC...")
    
    # Try HMAC authentication
    if 'hmac_key' in credentials and 'hmac_secret' in credentials:
        try:
            auth = HMACAuth(credentials['hmac_key'], credentials['hmac_secret'])
            client = EspoCRMClient(base_url, auth)
            client.metadata.get_app_metadata()  # Test connection
            return client
        except EspoCRMAuthenticationError:
            print("HMAC authentication failed")
    
    raise EspoCRMAuthenticationError("All authentication methods failed")
```

## CLI Authentication

The CLI tool supports all authentication methods:

### API Key

```bash
# Command line argument
espocrm-cli --url https://your-espocrm.com --api-key your-key list Lead

# Environment variable
export ESPOCRM_API_KEY="your-key"
espocrm-cli --url https://your-espocrm.com list Lead
```

### Basic Authentication

```bash
# Command line arguments
espocrm-cli --url https://your-espocrm.com --username user --password pass list Lead

# Environment variables
export ESPOCRM_USERNAME="user"
export ESPOCRM_PASSWORD="pass"
espocrm-cli --url https://your-espocrm.com list Lead
```

### HMAC Authentication

```bash
# Command line arguments
espocrm-cli --url https://your-espocrm.com --hmac-key key --hmac-secret secret list Lead

# Environment variables
export ESPOCRM_HMAC_KEY="key"
export ESPOCRM_HMAC_SECRET="secret"
espocrm-cli --url https://your-espocrm.com list Lead
```

## Troubleshooting

### Common Issues

#### 1. Invalid API Key

```
❌ Error: 401 Unauthorized - Invalid API key
```

**Solutions:**
- Verify the API key is correct
- Check if the API user exists in EspoCRM
- Ensure the API user has proper permissions
- Verify API access is enabled for the user

#### 2. Expired Credentials

```
❌ Error: 401 Unauthorized - Token expired
```

**Solutions:**
- Generate a new API key
- Update your environment variables
- Implement automatic credential rotation

#### 3. Insufficient Permissions

```
❌ Error: 403 Forbidden - Insufficient permissions
```

**Solutions:**
- Check user permissions in EspoCRM
- Verify the user has API access
- Ensure the user can access the requested entities

#### 4. HMAC Signature Mismatch

```
❌ Error: 401 Unauthorized - Invalid signature
```

**Solutions:**
- Verify both API key and secret key are correct
- Check system clock synchronization
- Ensure request is not being modified by proxies

## Next Steps

- [Configuration Guide](configuration.md) - Configure client settings
- [Quick Start](quickstart.md) - Start using the authenticated client
- [Error Handling](advanced/error-handling.md) - Handle authentication errors
- [Security Best Practices](advanced/security.md) - Advanced security topics