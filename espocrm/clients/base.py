"""EspoCRM API istemcileri için base sınıflar.

Bu modül EspoCRM API istemcilerinin temel sınıflarını içerir.
HTTP request wrapper metodları ve ortak client davranışları sağlar.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from urllib3.util.retry import Retry

from ..config import ClientConfig
from ..exceptions import (
    EspoCRMConnectionError,
    EspoCRMError,
    create_exception_from_status_code,
)
from ..models.base import EspoCRMBaseModel, EspoCRMListResponse, ModelType


# Generic type variable for client classes
ClientType = TypeVar("ClientType", bound="BaseClient")


class RateLimiter:
    """Rate limiting için basit bir sınıf."""
    
    def __init__(self, max_requests_per_minute: Optional[int] = None) -> None:
        """Rate limiter'ı başlatır.
        
        Args:
            max_requests_per_minute: Dakika başına maksimum request sayısı
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.requests: List[float] = []
    
    def wait_if_needed(self) -> None:
        """Gerekirse rate limit için bekler."""
        if not self.max_requests_per_minute:
            return
        
        now = time.time()
        
        # Son 1 dakikadaki request'leri filtrele
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        # Rate limit kontrolü
        if len(self.requests) >= self.max_requests_per_minute:
            # En eski request'ten 60 saniye geçene kadar bekle
            oldest_request = min(self.requests)
            wait_time = 60 - (now - oldest_request)
            if wait_time > 0:
                time.sleep(wait_time)
        
        # Bu request'i kaydet
        self.requests.append(now)


class BaseClient(ABC):
    """EspoCRM API istemcileri için temel abstract sınıf.
    
    Bu sınıf tüm EspoCRM client sınıflarının base'idir.
    HTTP request wrapper metodları ve ortak davranışları sağlar.
    
    Attributes:
        config: Client konfigürasyonu
        session: HTTP session
        rate_limiter: Rate limiter instance'ı
    """
    
    def __init__(self, config: ClientConfig) -> None:
        """Base client'ı başlatır.
        
        Args:
            config: Client konfigürasyonu
        """
        self.config = config
        self.session = self._create_session()
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
    
    def _create_session(self) -> requests.Session:
        """HTTP session'ı oluşturur ve yapılandırır.
        
        Returns:
            Yapılandırılmış requests.Session
        """
        session = requests.Session()
        
        # Default header'ları ayarla
        session.headers.update(self.config.get_default_headers())
        
        # SSL doğrulaması
        session.verify = self.config.verify_ssl
        
        # Retry stratejisi
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> requests.Response:
        """HTTP request yapar.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint
            data: Request body verisi
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            HTTP response
            
        Raises:
            EspoCRMConnectionError: Bağlantı hatası
            EspoCRMError: API hatası
        """
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        # URL oluştur
        url = self.config.get_api_url(endpoint)
        
        # Timeout ayarla
        if timeout is None:
            timeout = self.config.timeout
        
        # Ek header'ları merge et
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        try:
            if self.config.debug:
                print(f"[DEBUG] {method} {url}")
                if data:
                    print(f"[DEBUG] Request data: {data}")
                if params:
                    print(f"[DEBUG] Request params: {params}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=timeout,
            )
            
            if self.config.debug:
                print(f"[DEBUG] Response status: {response.status_code}")
                print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            # HTTP hata kontrolü
            if not response.ok:
                self._handle_error_response(response)
            
            return response
            
        except (ConnectionError, Timeout) as e:
            raise EspoCRMConnectionError(
                message=f"Bağlantı hatası: {str(e)}",
                original_error=e,
            )
        except RequestException as e:
            raise EspoCRMConnectionError(
                message=f"Request hatası: {str(e)}",
                original_error=e,
            )
    
    def _handle_error_response(self, response: requests.Response) -> None:
        """Hata response'unu işler ve uygun exception fırlatır.
        
        Args:
            response: HTTP response
            
        Raises:
            EspoCRMError: Uygun exception türü
        """
        try:
            error_data = response.json()
        except ValueError:
            error_data = {"message": response.text or "Unknown error"}
        
        # Hata mesajını çıkar
        error_message = error_data.get("message", f"HTTP {response.status_code}")
        
        # Response data'yı hazırla
        response_data = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": error_data,
        }
        
        # Uygun exception'ı oluştur ve fırlat
        exception = create_exception_from_status_code(
            status_code=response.status_code,
            message=error_message,
            response_data=response_data,
        )
        
        raise exception
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> requests.Response:
        """GET request yapar.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            HTTP response
        """
        return self._make_request("GET", endpoint, params=params, headers=headers, timeout=timeout)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> requests.Response:
        """POST request yapar.
        
        Args:
            endpoint: API endpoint
            data: Request body verisi
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            HTTP response
        """
        return self._make_request("POST", endpoint, data=data, params=params, headers=headers, timeout=timeout)
    
    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> requests.Response:
        """PUT request yapar.
        
        Args:
            endpoint: API endpoint
            data: Request body verisi
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            HTTP response
        """
        return self._make_request("PUT", endpoint, data=data, params=params, headers=headers, timeout=timeout)
    
    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> requests.Response:
        """PATCH request yapar.
        
        Args:
            endpoint: API endpoint
            data: Request body verisi
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            HTTP response
        """
        return self._make_request("PATCH", endpoint, data=data, params=params, headers=headers, timeout=timeout)
    
    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> requests.Response:
        """DELETE request yapar.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            HTTP response
        """
        return self._make_request("DELETE", endpoint, params=params, headers=headers, timeout=timeout)
    
    def get_json(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """GET request yapar ve JSON response döndürür.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            JSON response
        """
        response = self.get(endpoint, params=params, headers=headers, timeout=timeout)
        return response.json()
    
    def post_json(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """POST request yapar ve JSON response döndürür.
        
        Args:
            endpoint: API endpoint
            data: Request body verisi
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            JSON response
        """
        response = self.post(endpoint, data=data, params=params, headers=headers, timeout=timeout)
        return response.json()
    
    def put_json(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """PUT request yapar ve JSON response döndürür.
        
        Args:
            endpoint: API endpoint
            data: Request body verisi
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            JSON response
        """
        response = self.put(endpoint, data=data, params=params, headers=headers, timeout=timeout)
        return response.json()
    
    def patch_json(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """PATCH request yapar ve JSON response döndürür.
        
        Args:
            endpoint: API endpoint
            data: Request body verisi
            params: Query parameters
            headers: Ek header'lar
            timeout: Request timeout
            
        Returns:
            JSON response
        """
        response = self.patch(endpoint, data=data, params=params, headers=headers, timeout=timeout)
        return response.json()
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authentication işlemini gerçekleştirir.
        
        Bu method alt sınıflar tarafından implement edilmelidir.
        
        Returns:
            Authentication başarılı ise True
            
        Raises:
            EspoCRMAuthenticationError: Authentication hatası
        """
        pass
    
    def test_connection(self) -> bool:
        """EspoCRM server'a bağlantıyı test eder.
        
        Returns:
            Bağlantı başarılı ise True
            
        Raises:
            EspoCRMConnectionError: Bağlantı hatası
            EspoCRMError: API hatası
        """
        try:
            # Basit bir GET request ile bağlantıyı test et
            response = self.get("")
            return response.status_code == 200
        except EspoCRMError:
            raise
        except Exception as e:
            raise EspoCRMConnectionError(
                message=f"Bağlantı testi başarısız: {str(e)}",
                original_error=e,
            )
    
    def close(self) -> None:
        """Client'ı kapatır ve kaynakları temizler."""
        if hasattr(self, "session"):
            self.session.close()
    
    def __enter__(self) -> "BaseClient":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


class EntityClient(BaseClient):
    """EspoCRM entity'leri için özelleştirilmiş client sınıfı.
    
    Bu sınıf belirli bir EspoCRM entity türü için CRUD operasyonları sağlar.
    """
    
    def __init__(self, config: ClientConfig, entity_type: str) -> None:
        """Entity client'ı başlatır.
        
        Args:
            config: Client konfigürasyonu
            entity_type: EspoCRM entity türü (örn: 'Account', 'Contact')
        """
        super().__init__(config)
        self.entity_type = entity_type
    
    def list(
        self,
        offset: int = 0,
        max_size: int = 20,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order: str = "asc",
        select: Optional[List[str]] = None,
    ) -> EspoCRMListResponse:
        """Entity listesini getirir.
        
        Args:
            offset: Başlangıç offset'i
            max_size: Maksimum kayıt sayısı
            where: Filtreleme koşulları
            order_by: Sıralama field'ı
            order: Sıralama yönü ('asc' veya 'desc')
            select: Seçilecek field'lar
            
        Returns:
            Liste response'u
        """
        params = {
            "offset": offset,
            "maxSize": max_size,
            "order": order,
        }
        
        if where:
            params["where"] = where
        
        if order_by:
            params["orderBy"] = order_by
        
        if select:
            params["select"] = ",".join(select)
        
        response_data = self.get_json(self.entity_type, params=params)
        return EspoCRMListResponse(**response_data)
    
    def get_by_id(self, record_id: str) -> Dict[str, Any]:
        """ID'ye göre kayıt getirir.
        
        Args:
            record_id: Kayıt ID'si
            
        Returns:
            Kayıt verisi
        """
        endpoint = f"{self.entity_type}/{record_id}"
        return self.get_json(endpoint)
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni kayıt oluşturur.
        
        Args:
            data: Kayıt verisi
            
        Returns:
            Oluşturulan kayıt verisi
        """
        return self.post_json(self.entity_type, data=data)
    
    def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mevcut kaydı günceller.
        
        Args:
            record_id: Kayıt ID'si
            data: Güncellenecek veri
            
        Returns:
            Güncellenmiş kayıt verisi
        """
        endpoint = f"{self.entity_type}/{record_id}"
        return self.put_json(endpoint, data=data)
    
    def delete(self, record_id: str) -> bool:
        """Kaydı siler.
        
        Args:
            record_id: Kayıt ID'si
            
        Returns:
            Silme işlemi başarılı ise True
        """
        endpoint = f"{self.entity_type}/{record_id}"
        response = super().delete(endpoint)
        return response.status_code == 200
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authentication işlemini gerçekleştirir."""
        # EntityClient için authentication base client'a bırakılır
        return True


# Export edilecek sınıflar
__all__ = [
    "BaseClient",
    "EntityClient",
    "RateLimiter",
    "ClientType",
]