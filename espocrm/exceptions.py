"""EspoCRM API istemcisi için exception sınıfları.

Bu modül EspoCRM API'sine özel exception sınıflarını içerir.
Tüm exception'lar HTTP status kodlarını ve detaylı hata mesajlarını destekler.
"""

from typing import Any, Dict, Optional, Union
from typing_extensions import Self


class EspoCRMError(Exception):
    """EspoCRM API istemcisi için temel exception sınıfı.
    
    Tüm EspoCRM-specific exception'ların base sınıfıdır.
    HTTP status kodu, hata mesajı ve ek detayları içerebilir.
    
    Args:
        message: Hata mesajı
        status_code: HTTP status kodu (opsiyonel)
        details: Ek hata detayları (opsiyonel)
        response_data: API'den dönen ham veri (opsiyonel)
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.response_data = response_data or {}
    
    def __str__(self) -> str:
        """Exception'ın string temsilini döndürür."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message
    
    def __repr__(self) -> str:
        """Exception'ın debug temsilini döndürür."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"details={self.details})"
        )
    
    @classmethod
    def from_response(
        cls,
        message: str,
        status_code: int,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> Self:
        """HTTP response'dan exception oluşturur.
        
        Args:
            message: Hata mesajı
            status_code: HTTP status kodu
            response_data: API'den dönen ham veri
            
        Returns:
            Uygun exception sınıfının instance'ı
        """
        return cls(
            message=message,
            status_code=status_code,
            response_data=response_data,
        )


class EspoCRMAPIError(EspoCRMError):
    """Genel API hataları için exception sınıfı.
    
    EspoCRM API'den dönen genel hataları temsil eder.
    HTTP 4xx ve 5xx status kodları için kullanılır.
    """
    
    pass


class EspoCRMAuthenticationError(EspoCRMError):
    """Authentication (kimlik doğrulama) hataları için exception sınıfı.
    
    Geçersiz credentials, expired token gibi durumlarda kullanılır.
    Genellikle HTTP 401 Unauthorized ile ilişkilidir.
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: Optional[int] = 401,
        details: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            details=details,
            response_data=response_data,
        )


class EspoCRMAuthorizationError(EspoCRMError):
    """Authorization (yetkilendirme) hataları için exception sınıfı.
    
    Kullanıcının belirli bir kaynağa erişim yetkisi olmadığı durumlarda kullanılır.
    Genellikle HTTP 403 Forbidden ile ilişkilidir.
    """
    
    def __init__(
        self,
        message: str = "Access forbidden",
        status_code: Optional[int] = 403,
        details: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            details=details,
            response_data=response_data,
        )


class EspoCRMValidationError(EspoCRMError):
    """Veri validasyon hataları için exception sınıfı.
    
    Geçersiz veri formatı, eksik required field'lar gibi durumlarda kullanılır.
    Genellikle HTTP 400 Bad Request ile ilişkilidir.
    """
    
    def __init__(
        self,
        message: str = "Validation failed",
        status_code: Optional[int] = 400,
        details: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        validation_errors: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            details=details,
            response_data=response_data,
        )
        self.validation_errors = validation_errors or {}
    
    def get_field_errors(self) -> Dict[str, Any]:
        """Field-specific validation hatalarını döndürür."""
        return self.validation_errors


class EspoCRMConnectionError(EspoCRMError):
    """Bağlantı hataları için exception sınıfı.
    
    Network timeout, connection refused gibi durumlarda kullanılır.
    HTTP status kodu olmayabilir.
    """
    
    def __init__(
        self,
        message: str = "Connection failed",
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            details=details,
            response_data=response_data,
        )
        self.original_error = original_error


class EspoCRMRateLimitError(EspoCRMError):
    """Rate limit hataları için exception sınıfı.
    
    API rate limit'e takıldığında kullanılır.
    Genellikle HTTP 429 Too Many Requests ile ilişkilidir.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: Optional[int] = 429,
        details: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            details=details,
            response_data=response_data,
        )
        self.retry_after = retry_after
    
    def get_retry_after(self) -> Optional[int]:
        """Rate limit reset süresini saniye cinsinden döndürür."""
        return self.retry_after


class EspoCRMNotFoundError(EspoCRMError):
    """Kaynak bulunamadı hataları için exception sınıfı.
    
    İstenen kaynak mevcut olmadığında kullanılır.
    Genellikle HTTP 404 Not Found ile ilişkilidir.
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        status_code: Optional[int] = 404,
        details: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[Union[str, int]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            details=details,
            response_data=response_data,
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class EspoCRMServerError(EspoCRMError):
    """Server hataları için exception sınıfı.
    
    EspoCRM server'da internal error oluştuğunda kullanılır.
    Genellikle HTTP 5xx status kodları ile ilişkilidir.
    """
    
    def __init__(
        self,
        message: str = "Internal server error",
        status_code: Optional[int] = 500,
        details: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            details=details,
            response_data=response_data,
        )


def create_exception_from_status_code(
    status_code: int,
    message: str,
    response_data: Optional[Dict[str, Any]] = None,
) -> EspoCRMError:
    """HTTP status koduna göre uygun exception sınıfını oluşturur.
    
    Args:
        status_code: HTTP status kodu
        message: Hata mesajı
        response_data: API'den dönen ham veri
        
    Returns:
        Uygun exception sınıfının instance'ı
    """
    if status_code == 400:
        return EspoCRMValidationError(
            message=message,
            status_code=status_code,
            response_data=response_data,
        )
    elif status_code == 401:
        return EspoCRMAuthenticationError(
            message=message,
            status_code=status_code,
            response_data=response_data,
        )
    elif status_code == 403:
        return EspoCRMAuthorizationError(
            message=message,
            status_code=status_code,
            response_data=response_data,
        )
    elif status_code == 404:
        return EspoCRMNotFoundError(
            message=message,
            status_code=status_code,
            response_data=response_data,
        )
    elif status_code == 429:
        # Retry-After header'ını response_data'dan çıkarmaya çalış
        retry_after = None
        if response_data and "headers" in response_data:
            retry_after = response_data["headers"].get("Retry-After")
            if retry_after:
                try:
                    retry_after = int(retry_after)
                except (ValueError, TypeError):
                    retry_after = None
        
        return EspoCRMRateLimitError(
            message=message,
            status_code=status_code,
            response_data=response_data,
            retry_after=retry_after,
        )
    elif 500 <= status_code < 600:
        return EspoCRMServerError(
            message=message,
            status_code=status_code,
            response_data=response_data,
        )
    else:
        return EspoCRMAPIError(
            message=message,
            status_code=status_code,
            response_data=response_data,
        )


# Exception sınıflarının listesi - dışarıdan import edilebilir
__all__ = [
    "EspoCRMError",
    "EspoCRMAPIError",
    "EspoCRMAuthenticationError",
    "EspoCRMAuthorizationError",
    "EspoCRMValidationError",
    "EspoCRMConnectionError",
    "EspoCRMRateLimitError",
    "EspoCRMNotFoundError",
    "EspoCRMServerError",
    "create_exception_from_status_code",
]