#!/usr/bin/env python3
"""
EspoCRM Authentication Examples

Bu dosya EspoCRM Python API istemcisi için farklı authentication yöntemlerinin
nasıl kullanılacağını gösterir.
"""

import sys
import os

# Proje root'unu Python path'ine ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from espocrm.auth import (
    # Authentication sınıfları
    ApiKeyAuthentication,
    HMACAuthentication,
    BasicAuthentication,
    
    # Factory fonksiyonları
    create_api_key_auth,
    create_hmac_auth,
    create_basic_auth,
    create_espo_auth,
    quick_auth,
    
    # Utility fonksiyonları
    get_auth_type_name,
    validate_auth,
    get_supported_auth_types
)


def example_api_key_auth():
    """API Key Authentication örneği."""
    print("=" * 60)
    print("API Key Authentication Example")
    print("=" * 60)
    
    # Yöntem 1: Doğrudan sınıf kullanımı
    print("\n1. Direct class usage:")
    auth = ApiKeyAuthentication(api_key="your_api_key_from_espocrm")
    headers = auth.get_headers()
    print(f"   Headers: {headers}")
    print(f"   Valid: {auth.validate_credentials()}")
    print(f"   Type: {get_auth_type_name(auth)}")
    
    # Yöntem 2: Factory fonksiyon
    print("\n2. Factory function:")
    auth2 = create_api_key_auth("another_api_key")
    headers2 = auth2.get_headers()
    print(f"   Headers: {headers2}")
    
    # Yöntem 3: Quick auth
    print("\n3. Quick auth:")
    auth3 = quick_auth("api_key", api_key="quick_api_key")
    headers3 = auth3.get_headers()
    print(f"   Headers: {headers3}")
    
    # API Key rotation örneği
    print("\n4. API Key rotation:")
    auth.rotate_api_key("new_rotated_api_key")
    headers_rotated = auth.get_headers()
    print(f"   New headers: {headers_rotated}")


def example_hmac_auth():
    """HMAC Authentication örneği."""
    print("\n" + "=" * 60)
    print("HMAC Authentication Example")
    print("=" * 60)
    
    # HMAC authentication setup
    api_key = "your_api_key"
    secret_key = "your_secret_key"
    
    print("\n1. HMAC Authentication setup:")
    auth = create_hmac_auth(api_key, secret_key)
    print(f"   Valid: {auth.validate_credentials()}")
    print(f"   Type: {get_auth_type_name(auth)}")
    
    # Farklı HTTP metodları için header'lar
    print("\n2. Headers for different HTTP methods:")
    
    methods_and_uris = [
        ("GET", "api/v1/Contact"),
        ("POST", "api/v1/Account"),
        ("PUT", "api/v1/Contact/123"),
        ("DELETE", "api/v1/Account/456")
    ]
    
    for method, uri in methods_and_uris:
        headers = auth.get_headers(method, uri)
        print(f"   {method:6} {uri:20} -> {headers['X-Hmac-Authorization'][:20]}...")
    
    # Credentials masking
    print("\n3. Credentials masking (for logging):")
    masked = auth.get_credentials_masked()
    print(f"   Masked credentials: {masked}")


def example_basic_auth():
    """Basic Authentication örneği."""
    print("\n" + "=" * 60)
    print("Basic Authentication Example")
    print("=" * 60)
    
    # Username/Password ile Basic Auth
    print("\n1. Basic Auth with username/password:")
    auth1 = create_basic_auth("username", password="password")
    headers1 = auth1.get_headers()
    print(f"   Headers: {headers1}")
    print(f"   Using token: {auth1.is_using_token()}")
    print(f"   Using Espo header: {auth1.is_using_espo_header()}")
    
    # Username/Token ile Basic Auth
    print("\n2. Basic Auth with username/token:")
    auth2 = BasicAuthentication(username="username", token="auth_token_123")
    headers2 = auth2.get_headers()
    print(f"   Headers: {headers2}")
    print(f"   Using token: {auth2.is_using_token()}")
    
    # Credential updates
    print("\n3. Credential updates:")
    print("   Before update:", auth1.get_credentials_masked())
    auth1.update_password("new_password")
    print("   After password update:", auth1.get_credentials_masked())
    
    auth1.update_token("new_token")
    print("   After token update:", auth1.get_credentials_masked())
    print("   Now using token:", auth1.is_using_token())


def example_espo_auth():
    """Espo Authorization örneği."""
    print("\n" + "=" * 60)
    print("Espo Authorization Example")
    print("=" * 60)
    
    # Espo-Authorization header ile
    print("\n1. Espo-Authorization with password:")
    auth1 = create_espo_auth("username", password="password")
    headers1 = auth1.get_headers()
    print(f"   Headers: {headers1}")
    print(f"   Using Espo header: {auth1.is_using_espo_header()}")
    
    # Token ile Espo-Authorization
    print("\n2. Espo-Authorization with token:")
    auth2 = create_espo_auth("username", token="espo_token_123")
    headers2 = auth2.get_headers()
    print(f"   Headers: {headers2}")
    
    # Header tipi değiştirme
    print("\n3. Switching header types:")
    auth3 = BasicAuthentication(username="user", password="pass", use_espo_header=False)
    print(f"   Standard Basic: {auth3.get_headers()}")
    
    auth3.switch_header_type(use_espo_header=True)
    print(f"   Espo header: {auth3.get_headers()}")


def example_quick_auth_factory():
    """Quick Auth Factory örneği."""
    print("\n" + "=" * 60)
    print("Quick Auth Factory Example")
    print("=" * 60)
    
    # Tüm auth tiplerini quick_auth ile oluştur
    auth_configs = [
        ("api_key", {"api_key": "quick_api_key"}),
        ("hmac", {"api_key": "quick_api", "secret_key": "quick_secret"}),
        ("basic", {"username": "quick_user", "password": "quick_pass"}),
        ("espo", {"username": "quick_user", "token": "quick_token"})
    ]
    
    print("\nCreating all auth types with quick_auth:")
    for auth_type, kwargs in auth_configs:
        auth = quick_auth(auth_type, **kwargs)
        headers = auth.get_headers()
        print(f"   {auth_type:8} -> {get_auth_type_name(auth):20} -> {list(headers.keys())[0]}")


def example_utility_functions():
    """Utility fonksiyonları örneği."""
    print("\n" + "=" * 60)
    print("Utility Functions Example")
    print("=" * 60)
    
    # Desteklenen auth tipleri
    print("\n1. Supported authentication types:")
    supported_types = get_supported_auth_types()
    for auth_type in supported_types:
        print(f"   - {auth_type}")
    
    # Authentication validation
    print("\n2. Authentication validation:")
    valid_auth = create_api_key_auth("valid_key")
    invalid_auth = None
    
    print(f"   Valid auth: {validate_auth(valid_auth)}")
    print(f"   Invalid auth: {validate_auth(invalid_auth)}")
    
    # Auth type detection
    print("\n3. Authentication type detection:")
    auths = [
        create_api_key_auth("key"),
        create_hmac_auth("key", "secret"),
        create_basic_auth("user", password="pass"),
        create_espo_auth("user", token="token")
    ]
    
    for auth in auths:
        print(f"   {auth.__class__.__name__:20} -> {get_auth_type_name(auth)}")


def example_error_handling():
    """Error handling örneği."""
    print("\n" + "=" * 60)
    print("Error Handling Example")
    print("=" * 60)
    
    from espocrm.auth import AuthenticationError
    
    print("\n1. Invalid credentials:")
    try:
        ApiKeyAuthentication(api_key="")
    except AuthenticationError as e:
        print(f"   ✓ Caught: {e}")
    
    print("\n2. Missing parameters:")
    try:
        quick_auth("hmac", api_key="key")  # secret_key eksik
    except AuthenticationError as e:
        print(f"   ✓ Caught: {e}")
    
    print("\n3. Invalid auth type:")
    try:
        quick_auth("invalid_type", username="user")
    except ValueError as e:
        print(f"   ✓ Caught: {e}")
    
    print("\n4. Invalid credentials in existing auth:")
    try:
        auth = create_basic_auth("user", password="pass")
        auth._credentials = {}  # Credentials'ı bozalım
        auth.get_headers()
    except AuthenticationError as e:
        print(f"   ✓ Caught: {e}")


def main():
    """Ana örnek fonksiyon."""
    print("EspoCRM Python API Client - Authentication Examples")
    print("=" * 80)
    
    # Tüm örnekleri çalıştır
    example_api_key_auth()
    example_hmac_auth()
    example_basic_auth()
    example_espo_auth()
    example_quick_auth_factory()
    example_utility_functions()
    example_error_handling()
    
    print("\n" + "=" * 80)
    print("🎉 All authentication examples completed successfully!")
    print("\nNext steps:")
    print("1. Choose the authentication method that matches your EspoCRM setup")
    print("2. Replace example credentials with your actual EspoCRM credentials")
    print("3. Use the authentication object with EspoCRM API client")
    print("=" * 80)


if __name__ == "__main__":
    main()