"""
EspoCRM Authentication modülü

Farklı authentication yöntemlerini destekler:
- API Key Authentication
- HMAC Authentication  
- Basic Authentication
"""

from .base import AuthenticationBase, AuthenticationError
from .api_key import ApiKeyAuthentication, APIKeyAuth
from .hmac import HMACAuthentication, HMACAuth
from .basic import BasicAuthentication, BasicAuth

from typing import Union, Optional, List, Any

__all__ = [
    # Base classes
    "AuthenticationBase",
    "AuthenticationError",
    
    # Authentication implementations
    "ApiKeyAuthentication",
    "HMACAuthentication", 
    "BasicAuthentication",
    
    # Convenience aliases
    "APIKeyAuth",
    "HMACAuth",
    "BasicAuth",
    
    # Factory functions
    "create_api_key_auth",
    "create_hmac_auth",
    "create_basic_auth",
    "create_espo_auth",
    "quick_auth",
]

# Type alias for all authentication types
AuthenticationType = Union[
    ApiKeyAuthentication,
    HMACAuthentication,
    BasicAuthentication
]


def create_api_key_auth(api_key: str) -> ApiKeyAuthentication:
    """
    API Key authentication oluşturur.
    
    Args:
        api_key: EspoCRM API key
        
    Returns:
        ApiKeyAuthentication instance
        
    Example:
        auth = create_api_key_auth("your_api_key_here")
    """
    return ApiKeyAuthentication(api_key=api_key)


def create_hmac_auth(api_key: str, secret_key: str) -> HMACAuthentication:
    """
    HMAC authentication oluşturur.
    
    Args:
        api_key: EspoCRM API key
        secret_key: EspoCRM secret key
        
    Returns:
        HMACAuthentication instance
        
    Example:
        auth = create_hmac_auth("your_api_key", "your_secret_key")
    """
    return HMACAuthentication(api_key=api_key, secret_key=secret_key)


def create_basic_auth(
    username: str, 
    password: Optional[str] = None, 
    token: Optional[str] = None
) -> BasicAuthentication:
    """
    Standart Basic authentication oluşturur.
    
    Args:
        username: Kullanıcı adı
        password: Şifre (token yoksa gerekli)
        token: Authentication token (password yerine kullanılabilir)
        
    Returns:
        BasicAuthentication instance
        
    Example:
        auth = create_basic_auth("username", password="password")
        # veya
        auth = create_basic_auth("username", token="auth_token")
    """
    return BasicAuthentication(
        username=username,
        password=password,
        token=token,
        use_espo_header=False
    )


def create_espo_auth(
    username: str, 
    password: Optional[str] = None, 
    token: Optional[str] = None
) -> BasicAuthentication:
    """
    Espo-Authorization header ile Basic authentication oluşturur.
    
    Args:
        username: Kullanıcı adı
        password: Şifre (token yoksa gerekli)
        token: Authentication token (password yerine kullanılabilir)
        
    Returns:
        BasicAuthentication instance (Espo header ile)
        
    Example:
        auth = create_espo_auth("username", password="password")
        # veya
        auth = create_espo_auth("username", token="auth_token")
    """
    return BasicAuthentication(
        username=username,
        password=password,
        token=token,
        use_espo_header=True
    )


def get_auth_type_name(auth: AuthenticationType) -> str:
    """
    Authentication tipinin adını döndürür.
    
    Args:
        auth: Authentication instance
        
    Returns:
        Authentication tipi adı
    """
    if isinstance(auth, ApiKeyAuthentication):
        return "API Key"
    elif isinstance(auth, HMACAuthentication):
        return "HMAC"
    elif isinstance(auth, BasicAuthentication):
        if auth.is_using_espo_header():
            return "Espo Authorization"
        else:
            return "Basic Authorization"
    else:
        return "Unknown"


def validate_auth(auth: Optional[AuthenticationType]) -> bool:
    """
    Authentication instance'ının geçerli olup olmadığını kontrol eder.
    
    Args:
        auth: Authentication instance veya None
        
    Returns:
        Authentication geçerliyse True, değilse False
    """
    if auth is None:
        return False
    
    if not isinstance(auth, AuthenticationBase):
        return False
    
    return auth.validate_credentials()


def get_supported_auth_types() -> List[str]:
    """
    Desteklenen authentication tiplerinin listesini döndürür.
    
    Returns:
        Authentication tipi adlarının listesi
    """
    return [
        "API Key",
        "HMAC", 
        "Basic Authorization",
        "Espo Authorization"
    ]


# Convenience function for quick authentication setup
def quick_auth(
    auth_type: str,
    **kwargs: Any
) -> AuthenticationType:
    """
    Hızlı authentication setup için convenience fonksiyon.
    
    Args:
        auth_type: Authentication tipi ("api_key", "hmac", "basic", "espo")
        **kwargs: Authentication parametreleri
        
    Returns:
        Uygun authentication instance
        
    Raises:
        ValueError: Desteklenmeyen authentication tipi
        AuthenticationError: Geçersiz parametreler
        
    Example:
        # API Key
        auth = quick_auth("api_key", api_key="your_key")
        
        # HMAC
        auth = quick_auth("hmac", api_key="key", secret_key="secret")
        
        # Basic
        auth = quick_auth("basic", username="user", password="pass")
        
        # Espo
        auth = quick_auth("espo", username="user", token="token")
    """
    auth_type = auth_type.lower().strip()
    
    if auth_type == "api_key":
        api_key = kwargs.get("api_key")
        if not api_key:
            raise AuthenticationError("api_key parameter is required for API Key authentication")
        return create_api_key_auth(api_key)
    
    elif auth_type == "hmac":
        api_key = kwargs.get("api_key")
        secret_key = kwargs.get("secret_key")
        if not api_key or not secret_key:
            raise AuthenticationError("api_key and secret_key parameters are required for HMAC authentication")
        return create_hmac_auth(api_key, secret_key)
    
    elif auth_type == "basic":
        username = kwargs.get("username")
        password = kwargs.get("password")
        token = kwargs.get("token")
        if not username:
            raise AuthenticationError("username parameter is required for Basic authentication")
        return create_basic_auth(username, password, token)
    
    elif auth_type == "espo":
        username = kwargs.get("username")
        password = kwargs.get("password")
        token = kwargs.get("token")
        if not username:
            raise AuthenticationError("username parameter is required for Espo authentication")
        return create_espo_auth(username, password, token)
    
    else:
        supported_types = ", ".join(["api_key", "hmac", "basic", "espo"])
        raise ValueError(f"Unsupported authentication type: {auth_type}. Supported types: {supported_types}")