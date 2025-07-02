"""
EspoCRM HTTP Adapter Module

Bu modül EspoCRM API istemcisi için HTTP adapter sınıfını sağlar.
Connection pooling, retry logic, timeout management ve SSL/TLS konfigürasyonu içerir.
"""

import time
import random
import threading
from typing import Any, Dict, Optional, Union, Callable, Tuple
from urllib.parse import urljoin, urlparse
import logging

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import (
    RequestException,
    ConnectionError,
    Timeout,
    HTTPError,
    SSLError,
    TooManyRedirects
)

from ..exceptions import (
    EspoCRMConnectionError,
    EspoCRMRateLimitError,
    create_exception_from_status_code
)

logger = logging.getLogger(__name__)


class EspoCRMHTTPAdapter(HTTPAdapter):
    """
    EspoCRM için özelleştirilmiş HTTP adapter.
    
    Connection pooling, retry logic ve SSL/TLS konfigürasyonu sağlar.
    """
    
    def __init__(
        self,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        max_retries: int = 3,
        pool_block: bool = False,
        **kwargs
    ):
        """
        HTTP adapter'ını başlatır.
        
        Args:
            pool_connections: Connection pool sayısı
            pool_maxsize: Pool başına maksimum connection sayısı
            max_retries: Maksimum retry sayısı
            pool_block: Pool dolu olduğunda block edilsin mi
            **kwargs: Ek parametreler
        """
        # Retry stratejisi
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=1,
            raise_on_redirect=False,
            raise_on_status=False,
        )
        
        super().__init__(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy,
            pool_block=pool_block,
            **kwargs
        )


class HTTPClient:
    """
    EspoCRM için HTTP client sınıfı.
    
    Request/response interceptors, timeout management, SSL/TLS konfigürasyonu
    ve comprehensive error handling sağlar.
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_per_minute: Optional[int] = None,
        pool_connections: int = 10,
        pool_maxsize: int = 10,
        user_agent: str = "EspoCRM-Python-Client/0.1.0",
        extra_headers: Optional[Dict[str, str]] = None
    ):
        """
        HTTP client'ını başlatır.
        
        Args:
            base_url: Base URL
            timeout: Request timeout (saniye)
            verify_ssl: SSL sertifikası doğrulaması
            max_retries: Maksimum retry sayısı
            retry_delay: Retry'lar arası bekleme süresi
            rate_limit_per_minute: Dakika başına maksimum request sayısı
            pool_connections: Connection pool sayısı
            pool_maxsize: Pool başına maksimum connection sayısı
            user_agent: User-Agent header
            extra_headers: Ek HTTP header'ları
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_per_minute = rate_limit_per_minute
        self.user_agent = user_agent
        self.extra_headers = extra_headers or {}
        
        # Rate limiting için
        self._request_times: list = []
        self._rate_limit_lock = threading.Lock()
        
        # Request/response interceptors
        self._request_interceptors: list = []
        self._response_interceptors: list = []
        
        # Session oluştur
        self._session = self._create_session(pool_connections, pool_maxsize)
        
        logger.debug(
            "HTTP client initialized",
            base_url=base_url,
            timeout=timeout,
            verify_ssl=verify_ssl,
            max_retries=max_retries
        )
    
    def _create_session(self, pool_connections: int, pool_maxsize: int) -> requests.Session:
        """HTTP session oluşturur."""
        session = requests.Session()
        
        # Custom adapter mount et
        adapter = EspoCRMHTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=self.max_retries
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # Default headers
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        
        # Extra headers
        session.headers.update(self.extra_headers)
        
        return session
    
    def add_request_interceptor(self, interceptor: Callable[[requests.PreparedRequest], requests.PreparedRequest]):
        """Request interceptor ekler."""
        self._request_interceptors.append(interceptor)
    
    def add_response_interceptor(self, interceptor: Callable[[requests.Response], requests.Response]):
        """Response interceptor ekler."""
        self._response_interceptors.append(interceptor)
    
    def _apply_request_interceptors(self, prepared_request: requests.PreparedRequest) -> requests.PreparedRequest:
        """Request interceptor'larını uygular."""
        for interceptor in self._request_interceptors:
            try:
                prepared_request = interceptor(prepared_request)
            except Exception as e:
                logger.warning(f"Request interceptor failed: {e}")
        return prepared_request
    
    def _apply_response_interceptors(self, response: requests.Response) -> requests.Response:
        """Response interceptor'larını uygular."""
        for interceptor in self._response_interceptors:
            try:
                response = interceptor(response)
            except Exception as e:
                logger.warning(f"Response interceptor failed: {e}")
        return response
    
    def _check_rate_limit(self):
        """Rate limit kontrolü yapar."""
        if not self.rate_limit_per_minute:
            return
        
        with self._rate_limit_lock:
            now = time.time()
            # Son 1 dakikadaki request'leri filtrele
            self._request_times = [t for t in self._request_times if now - t < 60]
            
            if len(self._request_times) >= self.rate_limit_per_minute:
                sleep_time = 60 - (now - self._request_times[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
            
            self._request_times.append(now)
    
    def _build_url(self, endpoint: str) -> str:
        """Tam URL oluşturur."""
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        
        endpoint = endpoint.lstrip('/')
        return urljoin(f"{self.base_url}/", endpoint)
    
    def _prepare_request_data(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Request verilerini hazırlar."""
        # Headers
        request_headers = self._session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Request kwargs
        request_kwargs = {
            'method': method.upper(),
            'url': url,
            'headers': request_headers,
            'timeout': self.timeout,
            'verify': self.verify_ssl,
            'allow_redirects': True,
        }
        
        if params:
            request_kwargs['params'] = params
        
        if data is not None:
            request_kwargs['data'] = data
        
        if json is not None:
            request_kwargs['json'] = json
        
        # Ek kwargs
        request_kwargs.update(kwargs)
        
        return url, request_kwargs
    
    def _execute_request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """Request'i retry logic ile execute eder."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Rate limit kontrolü
                self._check_rate_limit()
                
                # Request hazırla
                request = requests.Request(**kwargs)
                prepared_request = self._session.prepare_request(request)
                
                # Request interceptors uygula
                prepared_request = self._apply_request_interceptors(prepared_request)
                
                # Log request
                logger.debug(
                    "HTTP request",
                    method=method,
                    url=url,
                    attempt=attempt + 1,
                    max_attempts=self.max_retries + 1
                )
                
                # Request gönder
                response = self._session.send(prepared_request)
                
                # Response interceptors uygula
                response = self._apply_response_interceptors(response)
                
                # Log response
                logger.debug(
                    "HTTP response",
                    method=method,
                    url=url,
                    status_code=response.status_code,
                    response_time_ms=response.elapsed.total_seconds() * 1000
                )
                
                # Rate limit kontrolü
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            sleep_time = int(retry_after)
                            logger.warning(f"Rate limited, sleeping for {sleep_time} seconds")
                            time.sleep(sleep_time)
                            continue
                        except ValueError:
                            pass
                
                return response
                
            except (ConnectionError, Timeout, SSLError, TooManyRedirects) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Exponential backoff with jitter
                    sleep_time = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Request failed, retrying in {sleep_time:.2f} seconds",
                        error=str(e),
                        attempt=attempt + 1,
                        max_attempts=self.max_retries + 1
                    )
                    time.sleep(sleep_time)
                else:
                    logger.error(
                        "Request failed after all retries",
                        error=str(e),
                        attempts=self.max_retries + 1
                    )
                    break
            
            except RequestException as e:
                last_exception = e
                logger.error(f"Request exception: {e}")
                break
        
        # Son exception'ı raise et
        if last_exception:
            if isinstance(last_exception, (ConnectionError, Timeout)):
                raise EspoCRMConnectionError(
                    f"Connection failed: {last_exception}",
                    original_error=last_exception
                )
            else:
                raise EspoCRMConnectionError(
                    f"Request failed: {last_exception}",
                    original_error=last_exception
                )
        
        raise EspoCRMConnectionError("Request failed for unknown reason")
    
    def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """
        HTTP request gönderir.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            headers: Ek HTTP headers
            params: Query parameters
            data: Request body data
            json: JSON data
            **kwargs: Ek request parametreleri
            
        Returns:
            HTTP response
            
        Raises:
            EspoCRMConnectionError: Bağlantı hatası
            EspoCRMRateLimitError: Rate limit hatası
            EspoCRMError: Diğer API hataları
        """
        url = self._build_url(endpoint)
        full_url, request_kwargs = self._prepare_request_data(
            method, url, headers, params, data, json, **kwargs
        )
        
        try:
            response = self._execute_request_with_retry(method, full_url, **request_kwargs)
            
            # HTTP error kontrolü
            if not response.ok:
                error_message = f"HTTP {response.status_code}: {response.reason}"
                
                # Response body'den detaylı hata mesajı al
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and 'message' in error_data:
                        error_message = error_data['message']
                except:
                    pass
                
                # Rate limit özel durumu
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    raise EspoCRMRateLimitError(
                        error_message,
                        status_code=response.status_code,
                        retry_after=int(retry_after) if retry_after else None,
                        response_data={'headers': dict(response.headers)}
                    )
                
                # Diğer HTTP hataları
                raise create_exception_from_status_code(
                    response.status_code,
                    error_message,
                    response_data={'headers': dict(response.headers)}
                )
            
            return response
            
        except (EspoCRMConnectionError, EspoCRMRateLimitError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during request: {e}")
            raise EspoCRMConnectionError(f"Unexpected error: {e}", original_error=e)
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET request gönderir."""
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST request gönderir."""
        return self.request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """PUT request gönderir."""
        return self.request('PUT', endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """PATCH request gönderir."""
        return self.request('PATCH', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE request gönderir."""
        return self.request('DELETE', endpoint, **kwargs)
    
    def head(self, endpoint: str, **kwargs) -> requests.Response:
        """HEAD request gönderir."""
        return self.request('HEAD', endpoint, **kwargs)
    
    def options(self, endpoint: str, **kwargs) -> requests.Response:
        """OPTIONS request gönderir."""
        return self.request('OPTIONS', endpoint, **kwargs)
    
    def close(self):
        """HTTP client'ı kapatır."""
        if self._session:
            self._session.close()
            logger.debug("HTTP client closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions
def create_http_client(
    base_url: str,
    timeout: float = 30.0,
    verify_ssl: bool = True,
    max_retries: int = 3,
    **kwargs
) -> HTTPClient:
    """HTTP client oluşturur."""
    return HTTPClient(
        base_url=base_url,
        timeout=timeout,
        verify_ssl=verify_ssl,
        max_retries=max_retries,
        **kwargs
    )


# Export edilecek sınıf ve fonksiyonlar
__all__ = [
    "EspoCRMHTTPAdapter",
    "HTTPClient",
    "create_http_client",
]