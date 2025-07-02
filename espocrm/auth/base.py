"""
EspoCRM Authentication Base Module

Bu modül tüm authentication yöntemleri için temel abstract sınıfı sağlar.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AuthenticationBase(ABC):
    """
    Tüm EspoCRM authentication yöntemleri için temel abstract sınıf.
    
    Bu sınıf authentication interface'ini tanımlar ve ortak metodları sağlar.
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """
        Authentication base sınıfını başlatır.
        
        Args:
            **kwargs: Authentication parametreleri
        """
        self._credentials: Dict[str, Any] = {}
        self._setup_credentials(**kwargs)
    
    @abstractmethod
    def _setup_credentials(self, **kwargs: Any) -> None:
        """
        Authentication credentials'ını ayarlar.
        
        Args:
            **kwargs: Authentication parametreleri
        """
        pass
    
    @abstractmethod
    def get_headers(self, method: str = "GET", uri: str = "/") -> Dict[str, str]:
        """
        HTTP request için authentication header'larını döndürür.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            uri: Request URI path
            
        Returns:
            Authentication header'larını içeren dictionary
        """
        pass
    
    def validate_credentials(self) -> bool:
        """
        Credentials'ın geçerli olup olmadığını kontrol eder.
        
        Returns:
            Credentials geçerliyse True, değilse False
        """
        return bool(self._credentials)
    
    def get_auth_type(self) -> str:
        """
        Authentication tipini döndürür.
        
        Returns:
            Authentication tipi string olarak
        """
        return self.__class__.__name__
    
    def _log_auth_attempt(self, method: str, uri: str) -> None:
        """
        Authentication denemesini loglar (sensitive data olmadan).
        
        Args:
            method: HTTP method
            uri: Request URI
        """
        logger.debug(
            f"Authentication attempt: {self.get_auth_type()} for {method} {uri}"
        )
    
    def _mask_sensitive_data(self, data: str, visible_chars: int = 4) -> str:
        """
        Sensitive data'yı maskeler (logging için).
        
        Args:
            data: Maskelenecek data
            visible_chars: Görünür karakter sayısı
            
        Returns:
            Maskelenmiş string
        """
        if not data or len(data) <= visible_chars:
            return "*" * len(data) if data else ""
        
        return data[:visible_chars] + "*" * (len(data) - visible_chars)
    
    def __repr__(self) -> str:
        """String representation (sensitive data olmadan)."""
        return f"{self.__class__.__name__}(type={self.get_auth_type()})"


class AuthenticationError(Exception):
    """Authentication ile ilgili hatalar için özel exception."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None) -> None:
        """
        Authentication error'ını başlatır.
        
        Args:
            message: Hata mesajı
            auth_type: Authentication tipi
        """
        self.auth_type = auth_type
        super().__init__(message)
    
    def __str__(self) -> str:
        """String representation."""
        if self.auth_type:
            return f"[{self.auth_type}] {super().__str__()}"
        return super().__str__()