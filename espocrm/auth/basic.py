"""
EspoCRM Basic Authentication Module

EspoCRM Basic authentication yöntemlerini implement eder.
Hem standart Basic Auth hem de Espo-Authorization header'ını destekler.
"""

import base64
from typing import Dict, Any, Optional
import logging

from .base import AuthenticationBase, AuthenticationError

logger = logging.getLogger(__name__)


class BasicAuthentication(AuthenticationBase):
    """
    EspoCRM Basic Authentication sınıfı.
    
    İki farklı authentication yöntemini destekler:
    1. Authorization: Basic base64Encode(username + ':' + password)
    2. Espo-Authorization: base64Encode(username + ':' + passwordOrToken)
    
    Usage:
        # Standart Basic Auth
        auth = BasicAuthentication(username="user", password="pass")
        
        # Espo Authorization with token
        auth = BasicAuthentication(username="user", token="token", use_espo_header=True)
        
        # Espo Authorization with password
        auth = BasicAuthentication(username="user", password="pass", use_espo_header=True)
    """
    
    def __init__(
        self, 
        username: str, 
        password: str = None, 
        token: str = None,
        use_espo_header: bool = False,
        **kwargs: Any
    ) -> None:
        """
        Basic authentication'ını başlatır.
        
        Args:
            username: Kullanıcı adı
            password: Şifre (token yoksa gerekli)
            token: Authentication token (password yerine kullanılabilir)
            use_espo_header: Espo-Authorization header kullanılsın mı
            **kwargs: Ek parametreler
            
        Raises:
            AuthenticationError: Parametreler geçersizse
        """
        if not username or not isinstance(username, str):
            raise AuthenticationError(
                "Username must be a non-empty string",
                auth_type="Basic"
            )
        
        if not password and not token:
            raise AuthenticationError(
                "Either password or token must be provided",
                auth_type="Basic"
            )
        
        if password and token:
            raise AuthenticationError(
                "Cannot provide both password and token",
                auth_type="Basic"
            )
        
        super().__init__(
            username=username,
            password=password,
            token=token,
            use_espo_header=use_espo_header,
            **kwargs
        )
    
    def _setup_credentials(self, **kwargs: Any) -> None:
        """
        Basic authentication credentials'ını ayarlar.
        
        Args:
            **kwargs: username, password, token, use_espo_header parametrelerini içeren kwargs
        """
        username = kwargs.get("username", "")
        password = kwargs.get("password")
        token = kwargs.get("token")
        use_espo_header = kwargs.get("use_espo_header", False)
        
        if not username:
            raise AuthenticationError(
                "Username is required for Basic authentication",
                auth_type="Basic"
            )
        
        # Credentials'ı güvenli şekilde sakla
        self._credentials = {
            "username": username.strip(),
            "password": password.strip() if password else None,
            "token": token.strip() if token else None,
            "use_espo_header": bool(use_espo_header),
            "auth_type": "basic"
        }
        
        auth_method = "token" if token else "password"
        header_type = "Espo-Authorization" if use_espo_header else "Authorization"
        
        logger.debug(
            f"Basic authentication setup completed. "
            f"Username: {self._mask_sensitive_data(username)}, "
            f"Auth method: {auth_method}, "
            f"Header type: {header_type}"
        )
    
    def _create_auth_string(self) -> str:
        """
        Authentication string'i oluşturur (username:password veya username:token).
        
        Returns:
            Authentication string
        """
        username = self._credentials["username"]
        
        # Token varsa onu kullan, yoksa password kullan
        if self._credentials["token"]:
            credential = self._credentials["token"]
        else:
            credential = self._credentials["password"]
        
        return f"{username}:{credential}"
    
    def _create_authorization_header(self) -> str:
        """
        Authorization header değerini oluşturur.
        
        Returns:
            Base64 encoded authorization string
        """
        auth_string = self._create_auth_string()
        auth_bytes = auth_string.encode('utf-8')
        encoded_auth = base64.b64encode(auth_bytes).decode('utf-8')
        
        return encoded_auth
    
    def get_headers(self, method: str = "GET", uri: str = "/") -> Dict[str, str]:
        """
        Basic authentication için HTTP header'larını döndürür.
        
        Args:
            method: HTTP method (Basic auth için kullanılmaz)
            uri: Request URI (Basic auth için kullanılmaz)
            
        Returns:
            Authorization veya Espo-Authorization header'ını içeren dictionary
            
        Raises:
            AuthenticationError: Credentials geçersizse
        """
        if not self.validate_credentials():
            raise AuthenticationError(
                "Invalid or missing Basic authentication credentials",
                auth_type="Basic"
            )
        
        self._log_auth_attempt(method, uri)
        
        try:
            encoded_auth = self._create_authorization_header()
            
            # Header tipini belirle
            if self._credentials["use_espo_header"]:
                header_name = "Espo-Authorization"
                header_value = encoded_auth
            else:
                header_name = "Authorization"
                header_value = f"Basic {encoded_auth}"
            
            headers = {
                header_name: header_value
            }
            
            logger.debug(f"Generated Basic auth headers ({header_name}) for {method} {uri}")
            return headers
            
        except Exception as e:
            raise AuthenticationError(
                f"Failed to create Basic auth headers: {str(e)}",
                auth_type="Basic"
            )
    
    def validate_credentials(self) -> bool:
        """
        Basic authentication credentials'ının geçerli olup olmadığını kontrol eder.
        
        Returns:
            Credentials geçerliyse True, değilse False
        """
        if not super().validate_credentials():
            return False
        
        # Username her zaman gerekli
        if not self._credentials.get("username"):
            return False
        
        # Password veya token'dan biri gerekli
        has_password = bool(self._credentials.get("password"))
        has_token = bool(self._credentials.get("token"))
        
        return has_password or has_token
    
    def get_credentials_masked(self) -> Dict[str, str]:
        """
        Maskelenmiş credentials döndürür (logging/debugging için).
        
        Returns:
            Maskelenmiş credentials dictionary
        """
        if not self.validate_credentials():
            return {
                "username": "INVALID",
                "password": "INVALID",
                "token": "INVALID"
            }
        
        masked = {
            "username": self._mask_sensitive_data(self._credentials["username"]),
            "use_espo_header": self._credentials["use_espo_header"]
        }
        
        if self._credentials.get("password"):
            masked["password"] = self._mask_sensitive_data(self._credentials["password"])
        
        if self._credentials.get("token"):
            masked["token"] = self._mask_sensitive_data(self._credentials["token"])
        
        return masked
    
    def is_using_token(self) -> bool:
        """
        Token kullanılıp kullanılmadığını kontrol eder.
        
        Returns:
            Token kullanılıyorsa True, password kullanılıyorsa False
        """
        return bool(self._credentials.get("token"))
    
    def is_using_espo_header(self) -> bool:
        """
        Espo-Authorization header kullanılıp kullanılmadığını kontrol eder.
        
        Returns:
            Espo header kullanılıyorsa True, standart Authorization kullanılıyorsa False
        """
        return self._credentials.get("use_espo_header", False)
    
    def update_password(self, new_password: str) -> None:
        """
        Password'ü günceller ve token'ı temizler.
        
        Args:
            new_password: Yeni password
            
        Raises:
            AuthenticationError: Yeni password geçersizse
        """
        if not new_password or not isinstance(new_password, str):
            raise AuthenticationError(
                "New password must be a non-empty string",
                auth_type="Basic"
            )
        
        self._credentials["password"] = new_password.strip()
        self._credentials["token"] = None  # Token'ı temizle
        
        logger.info("Basic authentication password updated")
    
    def update_token(self, new_token: str) -> None:
        """
        Token'ı günceller ve password'ü temizler.
        
        Args:
            new_token: Yeni token
            
        Raises:
            AuthenticationError: Yeni token geçersizse
        """
        if not new_token or not isinstance(new_token, str):
            raise AuthenticationError(
                "New token must be a non-empty string",
                auth_type="Basic"
            )
        
        self._credentials["token"] = new_token.strip()
        self._credentials["password"] = None  # Password'ü temizle
        
        logger.info("Basic authentication token updated")
    
    def switch_header_type(self, use_espo_header: bool) -> None:
        """
        Header tipini değiştirir (Authorization <-> Espo-Authorization).
        
        Args:
            use_espo_header: Espo-Authorization kullanılsın mı
        """
        old_type = "Espo-Authorization" if self._credentials["use_espo_header"] else "Authorization"
        new_type = "Espo-Authorization" if use_espo_header else "Authorization"
        
        self._credentials["use_espo_header"] = bool(use_espo_header)
        
        logger.info(f"Basic authentication header type changed from {old_type} to {new_type}")
    
    def __repr__(self) -> str:
        """String representation (sensitive data olmadan)."""
        masked_creds = self.get_credentials_masked()
        auth_method = "token" if self.is_using_token() else "password"
        header_type = "Espo" if self.is_using_espo_header() else "Basic"
        
        return (
            f"BasicAuthentication("
            f"username={masked_creds['username']}, "
            f"auth_method={auth_method}, "
            f"header_type={header_type}, "
            f"valid={self.validate_credentials()})"
        )


# Convenience alias
BasicAuth = BasicAuthentication