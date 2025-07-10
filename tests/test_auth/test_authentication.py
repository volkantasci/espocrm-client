"""
EspoCRM Authentication Test Module

Kapsamlı authentication testleri - tüm auth türleri, security, error handling.
"""

import pytest
import base64
import hmac
import hashlib
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from espocrm.auth import (
    AuthenticationBase,
    AuthenticationError,
    ApiKeyAuthentication,
    HMACAuthentication,
    BasicAuthentication,
    create_api_key_auth,
    create_hmac_auth,
    create_basic_auth,
    create_espo_auth,
    quick_auth
)
from espocrm.exceptions import EspoCRMError


class TestApiKeyAuthentication:
    """API Key Authentication testleri."""
    
    def test_valid_api_key(self):
        """Geçerli API key ile authentication testi."""
        api_key = "test_api_key_123"
        auth = ApiKeyAuthentication(api_key=api_key)
        
        assert auth.validate_credentials()
        assert auth.get_auth_type() == "ApiKeyAuthentication"
        
        headers = auth.get_headers()
        assert "X-Api-Key" in headers
        assert headers["X-Api-Key"] == api_key
    
    def test_invalid_api_key(self):
        """Geçersiz API key ile authentication testi."""
        with pytest.raises(AuthenticationError):
            ApiKeyAuthentication(api_key="")
        
        with pytest.raises(AuthenticationError):
            ApiKeyAuthentication(api_key=None)
    
    def test_api_key_masking(self):
        """API key maskeleme testi."""
        api_key = "test_api_key_123456789"
        auth = ApiKeyAuthentication(api_key=api_key)
        
        masked = auth.get_api_key_masked()
        assert masked.startswith("test")
        assert "*" in masked
        assert len(masked) == len(api_key)
    
    def test_api_key_rotation(self):
        """API key rotation testi."""
        old_key = "old_api_key"
        new_key = "new_api_key"
        
        auth = ApiKeyAuthentication(api_key=old_key)
        auth.rotate_api_key(new_key)
        
        headers = auth.get_headers()
        assert headers["X-Api-Key"] == new_key


class TestHMACAuthentication:
    """HMAC Authentication testleri."""
    
    def test_valid_hmac_credentials(self):
        """Geçerli HMAC credentials ile authentication testi."""
        api_key = "test_api_key_123"
        secret_key = "test_secret_key_with_sufficient_length"
        
        auth = HMACAuthentication(api_key=api_key, secret_key=secret_key)
        
        assert auth.validate_credentials()
        assert auth.get_auth_type() == "HMACAuthentication"
    
    def test_invalid_hmac_credentials(self):
        """Geçersiz HMAC credentials ile authentication testi."""
        with pytest.raises(AuthenticationError):
            HMACAuthentication(api_key="", secret_key="secret")
        
        with pytest.raises(AuthenticationError):
            HMACAuthentication(api_key="api", secret_key="")
    
    def test_hmac_signature_generation(self):
        """HMAC signature oluşturma testi."""
        api_key = "test_api_key_123"
        secret_key = "test_secret_key_with_sufficient_length"
        method = "GET"
        uri = "api/v1/Contact"
        
        auth = HMACAuthentication(api_key=api_key, secret_key=secret_key)
        headers = auth.get_headers(method=method, uri=uri)
        
        assert "X-Hmac-Authorization" in headers
        
        # Header'ı decode et ve kontrol et
        encoded_auth = headers["X-Hmac-Authorization"]
        decoded_auth = base64.b64decode(encoded_auth).decode('utf-8')
        
        # Format: api_key:signature
        assert decoded_auth.startswith(f"{api_key}:")
        
        # Signature'ı manuel olarak hesapla ve karşılaştır
        signature_string = f"{method.upper()} /{uri}"
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        expected_auth = f"{api_key}:{expected_signature}"
        assert decoded_auth == expected_auth
    
    def test_hmac_uri_formatting(self):
        """HMAC URI formatting testi."""
        api_key = "test_api_key_123"
        secret_key = "test_secret_key_with_sufficient_length"
        
        auth = HMACAuthentication(api_key=api_key, secret_key=secret_key)
        
        # URI başında '/' olmadan
        headers1 = auth.get_headers(method="GET", uri="api/v1/Contact")
        
        # URI başında '/' ile
        headers2 = auth.get_headers(method="GET", uri="/api/v1/Contact")
        
        # İkisi de aynı sonucu vermeli
        assert headers1["X-Hmac-Authorization"] == headers2["X-Hmac-Authorization"]


class TestBasicAuthentication:
    """Basic Authentication testleri."""
    
    def test_basic_auth_with_password(self):
        """Password ile Basic authentication testi."""
        username = "testuser"
        password = "testpass"
        
        auth = BasicAuthentication(username=username, password=password)
        
        assert auth.validate_credentials()
        assert not auth.is_using_token()
        assert not auth.is_using_espo_header()
        
        headers = auth.get_headers()
        assert "Authorization" in headers
        
        # Header'ı decode et ve kontrol et
        auth_header = headers["Authorization"]
        assert auth_header.startswith("Basic ")
        
        encoded_auth = auth_header[6:]  # "Basic " kısmını çıkar
        decoded_auth = base64.b64decode(encoded_auth).decode('utf-8')
        
        assert decoded_auth == f"{username}:{password}"
    
    def test_basic_auth_with_token(self):
        """Token ile Basic authentication testi."""
        username = "testuser"
        token = "test_token_123"
        
        auth = BasicAuthentication(username=username, token=token)
        
        assert auth.validate_credentials()
        assert auth.is_using_token()
        assert not auth.is_using_espo_header()
    
    def test_espo_auth_header(self):
        """Espo-Authorization header testi."""
        username = "testuser"
        password = "testpass"
        
        auth = BasicAuthentication(
            username=username, 
            password=password, 
            use_espo_header=True
        )
        
        assert auth.is_using_espo_header()
        
        headers = auth.get_headers()
        assert "Espo-Authorization" in headers
        assert "Authorization" not in headers
        
        # Header'ı decode et ve kontrol et
        encoded_auth = headers["Espo-Authorization"]
        decoded_auth = base64.b64decode(encoded_auth).decode('utf-8')
        
        assert decoded_auth == f"{username}:{password}"
    
    def test_invalid_basic_credentials(self):
        """Geçersiz Basic credentials testi."""
        with pytest.raises(AuthenticationError):
            BasicAuthentication(username="", password="pass")
        
        with pytest.raises(AuthenticationError):
            BasicAuthentication(username="user")  # password ve token yok
        
        with pytest.raises(AuthenticationError):
            BasicAuthentication(username="user", password="pass", token="token")  # ikisi de var
    
    def test_credential_updates(self):
        """Credential güncelleme testleri."""
        username = "testuser"
        password = "oldpass"
        
        auth = BasicAuthentication(username=username, password=password)
        
        # Password güncelle
        new_password = "newpass"
        auth.update_password(new_password)
        
        headers = auth.get_headers()
        encoded_auth = headers["Authorization"][6:]  # "Basic " kısmını çıkar
        decoded_auth = base64.b64decode(encoded_auth).decode('utf-8')
        
        assert decoded_auth == f"{username}:{new_password}"
        
        # Token'a geç
        new_token = "new_token"
        auth.update_token(new_token)
        
        assert auth.is_using_token()
        
        headers = auth.get_headers()
        encoded_auth = headers["Authorization"][6:]
        decoded_auth = base64.b64decode(encoded_auth).decode('utf-8')
        
        assert decoded_auth == f"{username}:{new_token}"


class TestFactoryFunctions:
    """Factory fonksiyon testleri."""
    
    def test_create_api_key_auth(self):
        """create_api_key_auth fonksiyon testi."""
        api_key = "test_key"
        auth = create_api_key_auth(api_key)
        
        assert isinstance(auth, ApiKeyAuthentication)
        assert auth.validate_credentials()
    
    def test_create_hmac_auth(self):
        """create_hmac_auth fonksiyon testi."""
        api_key = "test_key_123"
        secret_key = "test_secret_key_with_sufficient_length"
        auth = create_hmac_auth(api_key, secret_key)
        
        assert isinstance(auth, HMACAuthentication)
        assert auth.validate_credentials()
    
    def test_create_basic_auth(self):
        """create_basic_auth fonksiyon testi."""
        username = "user"
        password = "strong_password_123"
        auth = create_basic_auth(username, password)
        
        assert isinstance(auth, BasicAuthentication)
        assert not auth.is_using_espo_header()
        assert auth.validate_credentials()
    
    def test_create_espo_auth(self):
        """create_espo_auth fonksiyon testi."""
        username = "user"
        token = "strong_token_123"
        auth = create_espo_auth(username, token=token)
        
        assert isinstance(auth, BasicAuthentication)
        assert auth.is_using_espo_header()
        assert auth.validate_credentials()
    
    def test_quick_auth(self):
        """quick_auth fonksiyon testi."""
        # API Key
        auth1 = quick_auth("api_key", api_key="test_key")
        assert isinstance(auth1, ApiKeyAuthentication)
        
        # HMAC
        auth2 = quick_auth("hmac", api_key="test_key_123", secret_key="test_secret_key_with_sufficient_length")
        assert isinstance(auth2, HMACAuthentication)
        
        # Basic
        auth3 = quick_auth("basic", username="user", password="strong_password_123")
        assert isinstance(auth3, BasicAuthentication)
        assert not auth3.is_using_espo_header()
        
        # Espo
        auth4 = quick_auth("espo", username="user", token="strong_token_123")
        assert isinstance(auth4, BasicAuthentication)
        assert auth4.is_using_espo_header()
        
        # Geçersiz tip
        with pytest.raises(ValueError):
            quick_auth("invalid_type", username="user")


@pytest.mark.auth
@pytest.mark.security
class TestAuthenticationSecurity:
    """Authentication security testleri."""
    
    def test_api_key_length_validation(self):
        """API key uzunluk validasyonu."""
        # Çok kısa API key
        with pytest.raises(AuthenticationError):
            ApiKeyAuthentication(api_key="abc")
        
        # Çok uzun API key
        long_key = "a" * 1000
        with pytest.raises(AuthenticationError):
            ApiKeyAuthentication(api_key=long_key)
    
    def test_api_key_character_validation(self):
        """API key karakter validasyonu."""
        # Geçersiz karakterler
        invalid_keys = [
            "key with spaces",
            "key\nwith\nnewlines",
            "key\twith\ttabs",
            "key<with>html",
            "key'with'quotes"
        ]
        
        for invalid_key in invalid_keys:
            with pytest.raises(AuthenticationError):
                ApiKeyAuthentication(api_key=invalid_key)
    
    def test_hmac_secret_strength(self):
        """HMAC secret güçlülük testi."""
        api_key = "test_api_key"
        
        # Zayıf secret'lar
        weak_secrets = ["123", "password", "secret", "abc"]
        
        for weak_secret in weak_secrets:
            with pytest.raises(AuthenticationError):
                HMACAuthentication(api_key=api_key, secret_key=weak_secret)
    
    def test_basic_auth_password_strength(self):
        """Basic auth password güçlülük testi."""
        username = "testuser"
        
        # Zayıf password'lar
        weak_passwords = ["123", "password", "abc", ""]
        
        for weak_password in weak_passwords:
            with pytest.raises(AuthenticationError):
                BasicAuthentication(username=username, password=weak_password)
    
    def test_credential_masking(self):
        """Credential maskeleme testi."""
        # API Key masking
        api_key = "very_secret_api_key_123456789"
        auth = ApiKeyAuthentication(api_key=api_key)
        masked = auth.get_api_key_masked()
        
        assert "very" in masked  # İlk kısım görünür
        assert "*" in masked     # Maskelenmiş kısım
        assert "123456789" not in masked  # Son kısım maskelenmiş
    
    def test_timing_attack_resistance(self):
        """Timing attack direnci testi."""
        auth1 = create_api_key_auth("correct_key")
        auth2 = create_api_key_auth("wrong_key")
        
        # Validation süreleri benzer olmalı
        times = []
        for auth in [auth1, auth2]:
            start = time.time()
            auth.validate_credentials()
            end = time.time()
            times.append(end - start)
        
        # Süre farkı çok büyük olmamalı (timing attack'ı önlemek için)
        time_diff = abs(times[0] - times[1])
        assert time_diff < 0.01  # 10ms'den az fark


@pytest.mark.auth
@pytest.mark.performance
class TestAuthenticationPerformance:
    """Authentication performance testleri."""
    
    def test_api_key_performance(self, performance_timer):
        """API key authentication performance."""
        api_key = "test_api_key_123"
        auth = ApiKeyAuthentication(api_key=api_key)
        
        performance_timer.start()
        for _ in range(1000):
            auth.get_headers()
        performance_timer.stop()
        
        # 1000 header generation < 100ms olmalı
        assert performance_timer.elapsed < 0.1
    
    def test_hmac_performance(self, performance_timer):
        """HMAC authentication performance."""
        auth = create_hmac_auth("test_key", "test_secret_key_with_sufficient_length")
        
        performance_timer.start()
        for _ in range(100):
            auth.get_headers("GET", "api/v1/Contact")
        performance_timer.stop()
        
        # 100 HMAC generation < 500ms olmalı
        assert performance_timer.elapsed < 0.5
    
    def test_basic_auth_performance(self, performance_timer):
        """Basic authentication performance."""
        auth = create_basic_auth("testuser", password="strong_password_123")
        
        performance_timer.start()
        for _ in range(1000):
            auth.get_headers()
        performance_timer.stop()
        
        # 1000 basic auth header generation < 100ms olmalı
        assert performance_timer.elapsed < 0.1


@pytest.mark.auth
@pytest.mark.error_handling
class TestAuthenticationErrorHandling:
    """Authentication error handling testleri."""
    
    @pytest.mark.skip(reason="Network validation not implemented yet")
    def test_network_error_handling(self):
        """Network error handling."""
        auth = create_api_key_auth("test_key")
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = ConnectionError("Network error")
            
            # Auth validation network hatası durumunda graceful fail olmalı
            with pytest.raises(AuthenticationError):
                auth.validate_credentials()
    
    @pytest.mark.skip(reason="Network validation not implemented yet")
    def test_malformed_response_handling(self):
        """Malformed response handling."""
        auth = create_api_key_auth("test_key")
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            with pytest.raises(AuthenticationError):
                auth.validate_credentials()
    
    @pytest.mark.skip(reason="Network validation not implemented yet")
    def test_timeout_handling(self):
        """Timeout handling."""
        auth = create_api_key_auth("test_key")
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = TimeoutError("Request timeout")
            
            with pytest.raises(AuthenticationError):
                auth.validate_credentials()
    
    @pytest.mark.skip(reason="Network validation not implemented yet")
    def test_invalid_credentials_response(self):
        """Invalid credentials response handling."""
        auth = create_api_key_auth("invalid_key")
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"error": "Unauthorized"}
            mock_get.return_value = mock_response
            
            with pytest.raises(AuthenticationError):
                auth.validate_credentials()


@pytest.mark.auth
class TestAuthenticationParametrized:
    """Parametrized authentication testleri."""
    
    @pytest.mark.parametrize("auth_type,credentials", [
        ("api_key", {"api_key": "test_api_key_123"}),
        ("hmac", {"api_key": "test_key", "secret_key": "test_secret_key_with_length"}),
        ("basic", {"username": "user", "password": "strong_password_123"}),
        ("espo", {"username": "user", "token": "test_token_123"})
    ])
    def test_all_auth_types_validation(self, auth_type, credentials):
        """Tüm auth türleri için validation testi."""
        auth = quick_auth(auth_type, **credentials)
        assert auth.validate_credentials()
    
    @pytest.mark.parametrize("method,uri", [
        ("GET", "api/v1/Contact"),
        ("POST", "api/v1/Account"),
        ("PUT", "api/v1/Lead/123"),
        ("DELETE", "api/v1/Opportunity/456"),
        ("PATCH", "api/v1/Contact/789")
    ])
    def test_hmac_with_different_methods(self, method, uri):
        """HMAC farklı HTTP methodları ile test."""
        auth = create_hmac_auth("test_key", "test_secret_key_with_sufficient_length")
        headers = auth.get_headers(method=method, uri=uri)
        
        assert "X-Hmac-Authorization" in headers
        
        # Signature doğrulama
        encoded_auth = headers["X-Hmac-Authorization"]
        decoded_auth = base64.b64decode(encoded_auth).decode('utf-8')
        
        api_key, signature = decoded_auth.split(':', 1)
        assert api_key == "test_key"
        assert len(signature) == 64  # SHA256 hex length
    
    @pytest.mark.parametrize("invalid_input", [
        "",
        None,
        " ",
        "\n",
        "\t",
        "a",
        "ab"
    ])
    def test_invalid_api_keys(self, invalid_input):
        """Geçersiz API key'ler için test."""
        with pytest.raises(AuthenticationError):
            ApiKeyAuthentication(api_key=invalid_input)
    
    @pytest.mark.parametrize("header_type", [
        "Authorization",
        "Espo-Authorization"
    ])
    def test_basic_auth_header_types(self, header_type):
        """Basic auth farklı header türleri."""
        use_espo = header_type == "Espo-Authorization"
        auth = BasicAuthentication(
            username="testuser",
            password="strong_password_123",
            use_espo_header=use_espo
        )
        
        headers = auth.get_headers()
        assert header_type in headers
        
        # Diğer header türü olmamalı
        other_header = "Authorization" if use_espo else "Espo-Authorization"
        assert other_header not in headers


@pytest.mark.auth
@pytest.mark.integration
class TestAuthenticationIntegration:
    """Authentication integration testleri."""
    
    def test_auth_with_real_client(self, real_client):
        """Gerçek client ile auth testi."""
        # Client'ın auth'u olmalı
        assert real_client.auth is not None
        assert real_client.auth.validate_credentials()
    
    def test_auth_header_injection(self):
        """Auth header injection testi."""
        auth = create_api_key_auth("test_api_key_123")
        
        # Mock request ile header kontrolü
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_get.return_value = mock_response
            
            # Request yap
            import requests
            headers = auth.get_headers()
            requests.get("https://test.espocrm.com/api/v1/Contact", headers=headers)
            
            # Header'ın inject edildiğini kontrol et
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "X-Api-Key" in call_args[1]["headers"]
            assert call_args[1]["headers"]["X-Api-Key"] == "test_api_key_123"
    
    def test_auth_rotation_workflow(self):
        """Auth rotation workflow testi."""
        # API Key rotation
        auth = create_api_key_auth("old_api_key")
        old_headers = auth.get_headers()
        
        auth.rotate_api_key("new_api_key")
        new_headers = auth.get_headers()
        
        assert old_headers["X-Api-Key"] != new_headers["X-Api-Key"]
        assert new_headers["X-Api-Key"] == "new_api_key"
        
        # Basic auth credential update
        basic_auth = create_basic_auth("user", password="old_password")
        basic_auth.update_password("new_strong_password_123")
        
        headers = basic_auth.get_headers()
        encoded_auth = headers["Authorization"][6:]  # "Basic " kısmını çıkar
        decoded_auth = base64.b64decode(encoded_auth).decode('utf-8')
        
        assert decoded_auth == "user:new_strong_password_123"


@pytest.mark.auth
@pytest.mark.validation
class TestAuthenticationValidation:
    """Authentication validation testleri."""
    
    def test_comprehensive_api_key_validation(self):
        """Kapsamlı API key validation."""
        # Geçerli API key'ler
        valid_keys = [
            "valid_api_key_123",
            "VALID_API_KEY_456",
            "Valid-API-Key-789",
            "valid.api.key.012",
            "valid_API_key_345_with_numbers"
        ]
        
        for key in valid_keys:
            auth = ApiKeyAuthentication(api_key=key)
            assert auth.validate_credentials()
    
    def test_comprehensive_hmac_validation(self):
        """Kapsamlı HMAC validation."""
        api_key = "test_api_key_123"
        
        # Geçerli secret key'ler
        valid_secrets = [
            "strong_secret_key_with_sufficient_length",
            "STRONG_SECRET_KEY_WITH_SUFFICIENT_LENGTH",
            "Strong-Secret-Key-With-Sufficient-Length",
            "strong.secret.key.with.sufficient.length",
            "StrongSecretKey123WithNumbers456"
        ]
        
        for secret in valid_secrets:
            auth = HMACAuthentication(api_key=api_key, secret_key=secret)
            assert auth.validate_credentials()
    
    def test_comprehensive_basic_auth_validation(self):
        """Kapsamlı Basic auth validation."""
        username = "testuser"
        
        # Geçerli password'lar
        valid_passwords = [
            "strong_password_123",
            "StrongPassword456",
            "Strong-Password-789",
            "Strong.Password.012",
            "StrongP@ssw0rd!345"
        ]
        
        for password in valid_passwords:
            auth = BasicAuthentication(username=username, password=password)
            assert auth.validate_credentials()
    
    def test_edge_case_validations(self):
        """Edge case validasyonları."""
        # Minimum uzunluk sınırları
        min_api_key = "a" * 10  # Minimum 10 karakter
        auth = ApiKeyAuthentication(api_key=min_api_key)
        assert auth.validate_credentials()
        
        # Maximum uzunluk sınırları
        max_api_key = "a" * 255  # Maximum 255 karakter
        auth = ApiKeyAuthentication(api_key=max_api_key)
        assert auth.validate_credentials()
        
        # Unicode karakterler
        unicode_key = "test_api_key_üñíçødé_123"
        with pytest.raises(AuthenticationError):
            ApiKeyAuthentication(api_key=unicode_key)


if __name__ == "__main__":
    # Basit manuel test
    print("EspoCRM Authentication Test")
    print("=" * 40)
    
    # API Key test
    print("\n1. API Key Authentication Test:")
    try:
        auth = create_api_key_auth("test_api_key_123")
        headers = auth.get_headers()
        print(f"   ✓ Headers: {headers}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # HMAC test
    print("\n2. HMAC Authentication Test:")
    try:
        auth = create_hmac_auth("test_api_key", "test_secret_key_with_sufficient_length")
        headers = auth.get_headers("GET", "api/v1/Contact")
        print(f"   ✓ Headers: {headers}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Basic test
    print("\n3. Basic Authentication Test:")
    try:
        auth = create_basic_auth("testuser", password="strong_password_123")
        headers = auth.get_headers()
        print(f"   ✓ Headers: {headers}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Espo test
    print("\n4. Espo Authentication Test:")
    try:
        auth = create_espo_auth("testuser", token="test_token_123")
        headers = auth.get_headers()
        print(f"   ✓ Headers: {headers}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 40)
    print("Test completed!")