"""EspoCRM API istemcisi için konfigürasyon yönetimi.

Bu modül EspoCRM API istemcisinin konfigürasyon ayarlarını yönetir.
Environment variable'ları otomatik olarak okur ve validasyon sağlar.
"""

import os
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self


class ClientConfig(BaseModel):
    """EspoCRM API istemcisi için konfigürasyon sınıfı.
    
    Bu sınıf API istemcisinin tüm konfigürasyon ayarlarını yönetir.
    Environment variable'lardan otomatik okuma ve validasyon sağlar.
    
    Attributes:
        base_url: EspoCRM server'ın base URL'i
        api_key: API anahtarı (opsiyonel)
        username: Kullanıcı adı (opsiyonel)
        password: Şifre (opsiyonel)
        timeout: Request timeout süresi (saniye)
        max_retries: Maksimum retry sayısı
        retry_delay: Retry'lar arası bekleme süresi (saniye)
        verify_ssl: SSL sertifikası doğrulaması
        user_agent: HTTP User-Agent header'ı
        rate_limit_per_minute: Dakika başına maksimum request sayısı
        debug: Debug modu
        log_level: Log seviyesi
    """
    
    # Temel bağlantı ayarları
    base_url: str = Field(
        ...,
        description="EspoCRM server'ın base URL'i",
        examples=["https://your-espocrm.com", "http://localhost:8080"],
    )
    
    # Authentication ayarları
    api_key: Optional[str] = Field(
        default=None,
        description="EspoCRM API anahtarı",
        min_length=1,
    )
    
    username: Optional[str] = Field(
        default=None,
        description="EspoCRM kullanıcı adı",
        min_length=1,
    )
    
    password: Optional[str] = Field(
        default=None,
        description="EspoCRM şifresi",
        min_length=1,
    )
    
    # HTTP ayarları
    timeout: float = Field(
        default=30.0,
        description="Request timeout süresi (saniye)",
        gt=0,
        le=300,
    )
    
    max_retries: int = Field(
        default=3,
        description="Maksimum retry sayısı",
        ge=0,
        le=10,
    )
    
    retry_delay: float = Field(
        default=1.0,
        description="Retry'lar arası bekleme süresi (saniye)",
        ge=0,
        le=60,
    )
    
    verify_ssl: bool = Field(
        default=True,
        description="SSL sertifikası doğrulaması",
    )
    
    user_agent: str = Field(
        default="EspoCRM-Python-Client/0.1.0",
        description="HTTP User-Agent header'ı",
        min_length=1,
    )
    
    # Rate limiting ayarları
    rate_limit_per_minute: Optional[int] = Field(
        default=None,
        description="Dakika başına maksimum request sayısı",
        gt=0,
        le=10000,
    )
    
    # Debug ve logging ayarları
    debug: bool = Field(
        default=False,
        description="Debug modu",
    )
    
    log_level: str = Field(
        default="INFO",
        description="Log seviyesi",
        pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )
    
    # Ek ayarlar
    extra_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Ek HTTP header'ları",
    )
    
    model_config = {
        "env_prefix": "ESPOCRM_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "validate_assignment": True,
        "extra": "forbid",
    }
    
    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Base URL'in geçerli olduğunu doğrular."""
        if not v:
            raise ValueError("Base URL boş olamaz")
        
        # URL parsing ile geçerliliği kontrol et
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Geçerli bir URL formatı giriniz (örn: https://example.com)")
        
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL scheme'i http veya https olmalıdır")
        
        # Trailing slash'i kaldır
        return v.rstrip("/")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Log level'ın geçerli olduğunu doğrular."""
        return v.upper()
    
    @model_validator(mode="after")
    def validate_authentication(self) -> Self:
        """Authentication ayarlarının tutarlı olduğunu doğrular."""
        has_api_key = bool(self.api_key)
        has_credentials = bool(self.username and self.password)
        
        if not has_api_key and not has_credentials:
            raise ValueError(
                "En az bir authentication yöntemi gereklidir: "
                "API key veya username/password"
            )
        
        if has_api_key and has_credentials:
            # Her ikisi de varsa API key'i tercih et
            pass
        
        return self
    
    @classmethod
    def from_env(cls, **overrides: Any) -> Self:
        """Environment variable'lardan konfigürasyon oluşturur.
        
        Args:
            **overrides: Override edilecek değerler
            
        Returns:
            Konfigürasyon instance'ı
            
        Example:
            >>> config = ClientConfig.from_env(debug=True)
            >>> config = ClientConfig.from_env(
            ...     base_url="https://my-espocrm.com",
            ...     api_key="my-api-key"
            ... )
        """
        env_values = {}
        
        # Environment variable'ları oku
        env_mapping = {
            "ESPOCRM_BASE_URL": "base_url",
            "ESPOCRM_API_KEY": "api_key",
            "ESPOCRM_USERNAME": "username",
            "ESPOCRM_PASSWORD": "password",
            "ESPOCRM_TIMEOUT": "timeout",
            "ESPOCRM_MAX_RETRIES": "max_retries",
            "ESPOCRM_RETRY_DELAY": "retry_delay",
            "ESPOCRM_VERIFY_SSL": "verify_ssl",
            "ESPOCRM_USER_AGENT": "user_agent",
            "ESPOCRM_RATE_LIMIT_PER_MINUTE": "rate_limit_per_minute",
            "ESPOCRM_DEBUG": "debug",
            "ESPOCRM_LOG_LEVEL": "log_level",
        }
        
        for env_key, field_name in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # Type conversion
                if field_name in ("timeout", "retry_delay"):
                    try:
                        env_values[field_name] = float(env_value)
                    except ValueError:
                        continue
                elif field_name in ("max_retries", "rate_limit_per_minute"):
                    try:
                        env_values[field_name] = int(env_value)
                    except ValueError:
                        continue
                elif field_name in ("verify_ssl", "debug"):
                    env_values[field_name] = env_value.lower() in ("true", "1", "yes", "on")
                else:
                    env_values[field_name] = env_value
        
        # Override'ları uygula
        env_values.update(overrides)
        
        return cls(**env_values)
    
    def get_api_url(self, endpoint: str = "") -> str:
        """API endpoint URL'ini oluşturur.
        
        Args:
            endpoint: API endpoint'i (opsiyonel)
            
        Returns:
            Tam API URL'i
            
        Example:
            >>> config.get_api_url()
            'https://example.com/api/v1'
            >>> config.get_api_url('Account')
            'https://example.com/api/v1/Account'
        """
        api_base = f"{self.base_url}/api/v1"
        if endpoint:
            endpoint = endpoint.lstrip("/")
            return f"{api_base}/{endpoint}"
        return api_base
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Authentication header'larını oluşturur.
        
        Returns:
            Authentication header'ları
        """
        headers = {}
        
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        
        return headers
    
    def get_default_headers(self) -> Dict[str, str]:
        """Default HTTP header'larını oluşturur.
        
        Returns:
            Default header'lar
        """
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Authentication header'larını ekle
        headers.update(self.get_auth_headers())
        
        # Extra header'ları ekle
        headers.update(self.extra_headers)
        
        return headers
    
    def is_debug_enabled(self) -> bool:
        """Debug modunun aktif olup olmadığını kontrol eder."""
        return self.debug
    
    def has_api_key_auth(self) -> bool:
        """API key authentication'ın mevcut olup olmadığını kontrol eder."""
        return bool(self.api_key)
    
    def has_basic_auth(self) -> bool:
        """Basic authentication'ın mevcut olup olmadığını kontrol eder."""
        return bool(self.username and self.password)
    
    def model_dump_safe(self) -> Dict[str, Any]:
        """Güvenli model dump (şifreler gizlenir).
        
        Returns:
            Güvenli model dictionary'si
        """
        data = self.model_dump()
        
        # Hassas bilgileri gizle
        if data.get("password"):
            data["password"] = "***"
        if data.get("api_key"):
            data["api_key"] = f"{data['api_key'][:8]}***"
        
        return data


# Default konfigürasyon instance'ı
_default_config: Optional[ClientConfig] = None


def get_default_config() -> Optional[ClientConfig]:
    """Default konfigürasyon instance'ını döndürür."""
    return _default_config


def set_default_config(config: ClientConfig) -> None:
    """Default konfigürasyon instance'ını ayarlar."""
    global _default_config
    _default_config = config


def create_config_from_env(**overrides: Any) -> ClientConfig:
    """Environment'tan konfigürasyon oluşturur ve default olarak ayarlar.
    
    Args:
        **overrides: Override edilecek değerler
        
    Returns:
        Konfigürasyon instance'ı
    """
    config = ClientConfig.from_env(**overrides)
    set_default_config(config)
    return config


# Export edilecek sınıf ve fonksiyonlar
__all__ = [
    "ClientConfig",
    "get_default_config",
    "set_default_config",
    "create_config_from_env",
]