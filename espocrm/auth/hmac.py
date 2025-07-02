"""
EspoCRM HMAC Authentication Module

EspoCRM HMAC authentication yöntemini implement eder.
HMAC-SHA256 signature ile güvenli authentication sağlar.
"""

import hashlib
import hmac
import base64
from typing import Dict, Any
import logging

from .base import AuthenticationBase, AuthenticationError

logger = logging.getLogger(__name__)


class HMACAuthentication(AuthenticationBase):
    """
    EspoCRM HMAC Authentication sınıfı.
    
    EspoCRM dokümantasyonuna göre:
    X-Hmac-Authorization: base64Encode(apiKey + ':' + hashHmacSha256(method + ' /' + uri, secretKey))
    
    Usage:
        auth = HMACAuthentication(api_key="your_api_key", secret_key="your_secret")
        headers = auth.get_headers(method="GET", uri="api/v1/Contact")
    """
    
    def __init__(self, api_key: str, secret_key: str, **kwargs: Any) -> None:
        """
        HMAC authentication'ını başlatır.
        
        Args:
            api_key: EspoCRM API key
            secret_key: EspoCRM secret key
            **kwargs: Ek parametreler
            
        Raises:
            AuthenticationError: Parametreler geçersizse
        """
        if not api_key or not isinstance(api_key, str):
            raise AuthenticationError(
                "API key must be a non-empty string",
                auth_type="HMAC"
            )
        
        if not secret_key or not isinstance(secret_key, str):
            raise AuthenticationError(
                "Secret key must be a non-empty string",
                auth_type="HMAC"
            )
        
        super().__init__(api_key=api_key, secret_key=secret_key, **kwargs)
    
    def _setup_credentials(self, **kwargs: Any) -> None:
        """
        HMAC credentials'ını ayarlar.
        
        Args:
            **kwargs: api_key ve secret_key parametrelerini içeren kwargs
        """
        api_key = kwargs.get("api_key", "")
        secret_key = kwargs.get("secret_key", "")
        
        if not api_key or not secret_key:
            raise AuthenticationError(
                "Both API key and secret key are required for HMAC authentication",
                auth_type="HMAC"
            )
        
        # Credentials'ı güvenli şekilde sakla
        self._credentials = {
            "api_key": api_key.strip(),
            "secret_key": secret_key.strip(),
            "auth_type": "hmac"
        }
        
        logger.debug(
            f"HMAC authentication setup completed. "
            f"API Key: {self._mask_sensitive_data(api_key)}, "
            f"Secret: {self._mask_sensitive_data(secret_key)}"
        )
    
    def _generate_hmac_signature(self, method: str, uri: str) -> str:
        """
        HMAC-SHA256 signature oluşturur.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            uri: Request URI path
            
        Returns:
            HMAC signature string
            
        Raises:
            AuthenticationError: Signature oluşturulamazsa
        """
        try:
            # EspoCRM format: method + ' /' + uri
            # URI'nin başında '/' yoksa ekle
            if not uri.startswith('/'):
                uri = '/' + uri
            
            # Signature string'i oluştur
            signature_string = f"{method.upper()} {uri}"
            
            # HMAC-SHA256 hesapla
            secret_bytes = self._credentials["secret_key"].encode('utf-8')
            message_bytes = signature_string.encode('utf-8')
            
            signature = hmac.new(
                secret_bytes,
                message_bytes,
                hashlib.sha256
            ).hexdigest()
            
            logger.debug(
                f"Generated HMAC signature for: {signature_string} "
                f"(signature: {self._mask_sensitive_data(signature, 8)})"
            )
            
            return signature
            
        except Exception as e:
            raise AuthenticationError(
                f"Failed to generate HMAC signature: {str(e)}",
                auth_type="HMAC"
            )
    
    def _create_authorization_header(self, method: str, uri: str) -> str:
        """
        X-Hmac-Authorization header değerini oluşturur.
        
        Args:
            method: HTTP method
            uri: Request URI
            
        Returns:
            Base64 encoded authorization string
        """
        # HMAC signature oluştur
        signature = self._generate_hmac_signature(method, uri)
        
        # EspoCRM format: apiKey + ':' + signature
        auth_string = f"{self._credentials['api_key']}:{signature}"
        
        # Base64 encode
        auth_bytes = auth_string.encode('utf-8')
        encoded_auth = base64.b64encode(auth_bytes).decode('utf-8')
        
        return encoded_auth
    
    def get_headers(self, method: str = "GET", uri: str = "/") -> Dict[str, str]:
        """
        HMAC authentication için HTTP header'larını döndürür.
        
        Args:
            method: HTTP method
            uri: Request URI path
            
        Returns:
            X-Hmac-Authorization header'ını içeren dictionary
            
        Raises:
            AuthenticationError: Credentials geçersizse veya header oluşturulamazsa
        """
        if not self.validate_credentials():
            raise AuthenticationError(
                "Invalid or missing HMAC credentials",
                auth_type="HMAC"
            )
        
        self._log_auth_attempt(method, uri)
        
        try:
            authorization_header = self._create_authorization_header(method, uri)
            
            headers = {
                "X-Hmac-Authorization": authorization_header
            }
            
            logger.debug(f"Generated HMAC headers for {method} {uri}")
            return headers
            
        except Exception as e:
            raise AuthenticationError(
                f"Failed to create HMAC headers: {str(e)}",
                auth_type="HMAC"
            )
    
    def validate_credentials(self) -> bool:
        """
        HMAC credentials'ının geçerli olup olmadığını kontrol eder.
        
        Returns:
            Credentials geçerliyse True, değilse False
        """
        return (
            super().validate_credentials() and
            "api_key" in self._credentials and
            "secret_key" in self._credentials and
            bool(self._credentials["api_key"]) and
            bool(self._credentials["secret_key"])
        )
    
    def get_credentials_masked(self) -> Dict[str, str]:
        """
        Maskelenmiş credentials döndürür (logging/debugging için).
        
        Returns:
            Maskelenmiş credentials dictionary
        """
        if not self.validate_credentials():
            return {"api_key": "INVALID", "secret_key": "INVALID"}
        
        return {
            "api_key": self._mask_sensitive_data(self._credentials["api_key"]),
            "secret_key": self._mask_sensitive_data(self._credentials["secret_key"])
        }
    
    def rotate_credentials(self, new_api_key: str = None, new_secret_key: str = None) -> None:
        """
        API key ve/veya secret key'i yenisi ile değiştirir.
        
        Args:
            new_api_key: Yeni API key (opsiyonel)
            new_secret_key: Yeni secret key (opsiyonel)
            
        Raises:
            AuthenticationError: Yeni credentials geçersizse
        """
        if new_api_key is not None:
            if not new_api_key or not isinstance(new_api_key, str):
                raise AuthenticationError(
                    "New API key must be a non-empty string",
                    auth_type="HMAC"
                )
            self._credentials["api_key"] = new_api_key.strip()
        
        if new_secret_key is not None:
            if not new_secret_key or not isinstance(new_secret_key, str):
                raise AuthenticationError(
                    "New secret key must be a non-empty string",
                    auth_type="HMAC"
                )
            self._credentials["secret_key"] = new_secret_key.strip()
        
        logger.info("HMAC credentials rotated successfully")
    
    def __repr__(self) -> str:
        """String representation (sensitive data olmadan)."""
        masked_creds = self.get_credentials_masked()
        return (
            f"HMACAuthentication("
            f"api_key={masked_creds['api_key']}, "
            f"secret_key={masked_creds['secret_key']}, "
            f"valid={self.validate_credentials()})"
        )


# Convenience alias
HMACAuth = HMACAuthentication