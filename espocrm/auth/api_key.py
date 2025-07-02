"""
EspoCRM API Key Authentication Module

EspoCRM API Key authentication yöntemini implement eder.
API Key, X-Api-Key header'ı ile gönderilir.
"""

from typing import Dict, Any, Optional
import logging

from .base import AuthenticationBase, AuthenticationError

logger = logging.getLogger(__name__)


class ApiKeyAuthentication(AuthenticationBase):
    """
    EspoCRM API Key Authentication sınıfı.
    
    EspoCRM dokümantasyonuna göre:
    X-Api-Key: API_KEY_COPIED_FROM_THE_USER_DETAIL_VIEW
    
    Usage:
        auth = ApiKeyAuthentication(api_key="your_api_key_here")
        headers = auth.get_headers()
    """
    
    def __init__(self, api_key: Optional[str], **kwargs: Any) -> None:
        """
        API Key authentication'ını başlatır.
        
        Args:
            api_key: EspoCRM'den alınan API key
            **kwargs: Ek parametreler
            
        Raises:
            AuthenticationError: API key geçersizse
        """
        if not api_key or not isinstance(api_key, str):
            raise AuthenticationError(
                "API key must be a non-empty string",
                auth_type="ApiKey"
            )
        
        # API key validation
        self._validate_api_key(api_key)
        
        super().__init__(api_key=api_key, **kwargs)
    
    def _validate_api_key(self, api_key: str) -> None:
        """
        API key'in güvenlik gereksinimlerini kontrol eder.
        
        Args:
            api_key: Kontrol edilecek API key
            
        Raises:
            AuthenticationError: API key güvenlik gereksinimlerini karşılamazsa
        """
        # Minimum uzunluk kontrolü (EspoCRM genellikle 16+ karakter kullanır)
        if len(api_key.strip()) < 8:
            raise AuthenticationError(
                "API key must be at least 8 characters long",
                auth_type="ApiKey"
            )
        
        # Maksimum uzunluk kontrolü
        if len(api_key.strip()) > 255:
            raise AuthenticationError(
                "API key must be less than 255 characters",
                auth_type="ApiKey"
            )
        
        # Karakter format kontrolü - sadece alfanumerik ve bazı özel karakterler
        import re
        if not re.match(r'^[a-zA-Z0-9\-_\.]+$', api_key.strip()):
            raise AuthenticationError(
                "API key contains invalid characters. Only alphanumeric, dash, underscore and dot are allowed",
                auth_type="ApiKey"
            )
        
        # Boşluk karakteri kontrolü
        if ' ' in api_key or '\t' in api_key or '\n' in api_key:
            raise AuthenticationError(
                "API key cannot contain whitespace characters",
                auth_type="ApiKey"
            )
    
    def _setup_credentials(self, **kwargs: Any) -> None:
        """
        API Key credentials'ını ayarlar.
        
        Args:
            **kwargs: api_key parametresini içeren kwargs
        """
        api_key = kwargs.get("api_key", "")
        
        if not api_key:
            raise AuthenticationError(
                "API key is required for API Key authentication",
                auth_type="ApiKey"
            )
        
        # API key'i güvenli şekilde sakla
        self._credentials = {
            "api_key": api_key.strip(),
            "auth_type": "api_key"
        }
        
        logger.debug(
            f"API Key authentication setup completed. "
            f"Key: {self._mask_sensitive_data(api_key)}"
        )
    
    def get_headers(self, method: str = "GET", uri: str = "/") -> Dict[str, str]:
        """
        API Key authentication için HTTP header'larını döndürür.
        
        Args:
            method: HTTP method (API Key için kullanılmaz)
            uri: Request URI (API Key için kullanılmaz)
            
        Returns:
            X-Api-Key header'ını içeren dictionary
            
        Raises:
            AuthenticationError: Credentials geçersizse
        """
        if not self.validate_credentials():
            raise AuthenticationError(
                "Invalid or missing API key credentials",
                auth_type="ApiKey"
            )
        
        self._log_auth_attempt(method, uri)
        
        headers = {
            "X-Api-Key": self._credentials["api_key"]
        }
        
        logger.debug(f"Generated API Key headers for {method} {uri}")
        return headers
    
    def validate_credentials(self) -> bool:
        """
        API Key credentials'ının geçerli olup olmadığını kontrol eder.
        
        Returns:
            Credentials geçerliyse True, değilse False
        """
        return (
            super().validate_credentials() and
            "api_key" in self._credentials and
            bool(self._credentials["api_key"])
        )
    
    def get_api_key_masked(self) -> str:
        """
        Maskelenmiş API key'i döndürür (logging/debugging için).
        
        Returns:
            Maskelenmiş API key
        """
        if not self.validate_credentials():
            return "INVALID"
        
        return self._mask_sensitive_data(self._credentials["api_key"])
    
    def rotate_api_key(self, new_api_key: str) -> None:
        """
        API key'i yenisi ile değiştirir.
        
        Args:
            new_api_key: Yeni API key
            
        Raises:
            AuthenticationError: Yeni API key geçersizse
        """
        if not new_api_key or not isinstance(new_api_key, str):
            raise AuthenticationError(
                "New API key must be a non-empty string",
                auth_type="ApiKey"
            )
        
        old_key_masked = self.get_api_key_masked()
        self._credentials["api_key"] = new_api_key.strip()
        
        logger.info(
            f"API Key rotated from {old_key_masked} to "
            f"{self._mask_sensitive_data(new_api_key)}"
        )
    
    def __repr__(self) -> str:
        """String representation (sensitive data olmadan)."""
        return (
            f"ApiKeyAuthentication("
            f"api_key={self.get_api_key_masked()}, "
            f"valid={self.validate_credentials()})"
        )


# Convenience alias
APIKeyAuth = ApiKeyAuthentication