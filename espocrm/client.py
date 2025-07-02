"""
EspoCRM Main Client Module

Bu modül EspoCRM API istemcisinin ana sınıfını sağlar.
Authentication, logging, HTTP operations ve modüler client'ları yönetir.
"""

import threading
from typing import Any, Dict, Optional, Union
from contextlib import contextmanager
import logging

from .config import ClientConfig
from .auth.base import AuthenticationBase
from .logging import StructuredLogger, get_logger
from .utils.http import HTTPClient
from .utils.serializers import DataSerializer, parse_espocrm_response
from .utils.validators import validate_url, ValidationError
from .utils.helpers import generate_request_id, timing_decorator
from .exceptions import (
    EspoCRMError,
    EspoCRMConnectionError,
    EspoCRMAuthenticationError,
    create_exception_from_status_code
)

logger = logging.getLogger(__name__)


class EspoCRMClient:
    """
    EspoCRM API istemcisinin ana sınıfı.
    
    Authentication, HTTP operations, logging ve modüler client'ları yönetir.
    Context manager pattern'ı destekler ve thread-safe operations sağlar.
    
    Example:
        >>> from espocrm import EspoCRMClient, ClientConfig
        >>> from espocrm.auth import APIKeyAuth
        >>> 
        >>> config = ClientConfig(
        ...     base_url="https://your-espocrm.com",
        ...     api_key="your-api-key"
        ... )
        >>> auth = APIKeyAuth(api_key="your-api-key")
        >>> 
        >>> with EspoCRMClient(config.base_url, auth, config) as client:
        ...     # Use client
        ...     pass
    """
    
    def __init__(
        self,
        base_url: str,
        auth: AuthenticationBase,
        config: Optional[ClientConfig] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        EspoCRM client'ını başlatır.
        
        Args:
            base_url: EspoCRM server'ın base URL'i
            auth: Authentication instance'ı
            config: Client konfigürasyonu (opsiyonel)
            logger: Structured logger (opsiyonel)
            
        Raises:
            ValidationError: Geçersiz URL
            EspoCRMAuthenticationError: Authentication hatası
        """
        # URL validation
        try:
            validate_url(base_url, require_https=False)
        except ValidationError as e:
            raise ValidationError(f"Invalid base URL: {e}")
        
        self.base_url = base_url.rstrip('/')
        self.auth = auth
        self.config = config or ClientConfig(base_url=base_url)
        
        # Logger setup
        if logger:
            self.logger = logger
        else:
            self.logger = get_logger(
                'espocrm.client',
                level=self.config.log_level,
                enable_masking=True
            )
        
        # Thread safety
        self._lock = threading.RLock()
        self._closed = False
        
        # Request context
        self._request_context = threading.local()
        
        # Components initialization
        self._initialize_components()
        
        # Modüler client'lar (placeholder - gerçek implementasyonlar sonra eklenecek)
        self._initialize_clients()
        
        self.logger.info(
            "EspoCRM client initialized",
            base_url=self.base_url,
            auth_type=self.auth.get_auth_type(),
            config=self.config.model_dump_safe()
        )
    
    def _initialize_components(self):
        """Core component'ları başlatır."""
        # HTTP client
        self.http_client = HTTPClient(
            base_url=f"{self.base_url}/api/v1",
            timeout=self.config.timeout,
            verify_ssl=self.config.verify_ssl,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            rate_limit_per_minute=self.config.rate_limit_per_minute,
            user_agent=self.config.user_agent,
            extra_headers=self.config.extra_headers
        )
        
        # Data serializer
        self.serializer = DataSerializer()
        
        # Request/response interceptors
        self._setup_interceptors()
    
    def _setup_interceptors(self):
        """HTTP request/response interceptor'larını ayarlar."""
        # Request interceptor - authentication headers ekle
        def auth_interceptor(prepared_request):
            # Authentication headers al
            auth_headers = self.auth.get_headers(
                method=prepared_request.method,
                uri=prepared_request.path_url or '/'
            )
            
            # Headers'ı güncelle
            if auth_headers:
                prepared_request.headers.update(auth_headers)
            
            # Request ID ekle
            request_id = self._get_request_id()
            if request_id:
                prepared_request.headers['X-Request-ID'] = request_id
            
            return prepared_request
        
        # Response interceptor - logging ve error handling
        def response_interceptor(response):
            # Response'u logla
            self.logger.debug(
                "API response received",
                method=response.request.method,
                url=response.request.url,
                status_code=response.status_code,
                response_time_ms=response.elapsed.total_seconds() * 1000,
                request_id=self._get_request_id()
            )
            
            return response
        
        # Interceptor'ları ekle
        self.http_client.add_request_interceptor(auth_interceptor)
        self.http_client.add_response_interceptor(response_interceptor)
    
    def _initialize_clients(self):
        """Modüler client'ları başlatır."""
        # CRUD client'ı başlat
        from .clients.crud import CrudClient
        self.crud = CrudClient(self)
        
        # Relationship client'ı başlat
        from .clients.relationships import RelationshipClient
        self.relationships = RelationshipClient(self)
        
        # Stream client'ı başlat
        from .clients.stream import StreamClient
        self.stream = StreamClient(self)
        
        # Attachment client'ı başlat
        from .clients.attachments import AttachmentClient
        self.attachments = AttachmentClient(self)
        
        # Metadata client'ı başlat
        from .clients.metadata import MetadataClient
        self.metadata = MetadataClient(self)
    
    def _get_request_id(self) -> Optional[str]:
        """Current request ID'sini döndürür."""
        return getattr(self._request_context, 'request_id', None)
    
    def _set_request_id(self, request_id: str):
        """Request ID'sini ayarlar."""
        self._request_context.request_id = request_id
    
    @contextmanager
    def request_context(self, request_id: Optional[str] = None):
        """
        Request context manager.
        
        Args:
            request_id: Request ID (opsiyonel, otomatik generate edilir)
            
        Example:
            >>> with client.request_context() as ctx:
            ...     # Request operations
            ...     pass
        """
        if request_id is None:
            request_id = generate_request_id()
        
        old_request_id = self._get_request_id()
        self._set_request_id(request_id)
        
        # Logger context'e request ID ekle
        self.logger.set_context(request_id=request_id)
        
        try:
            yield request_id
        finally:
            # Eski request ID'yi restore et
            if old_request_id:
                self._set_request_id(old_request_id)
                self.logger.set_context(request_id=old_request_id)
            else:
                self._request_context.request_id = None
                self.logger.clear_context()
    
    @timing_decorator
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        HTTP request gönderir ve response'u parse eder.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            headers: Ek HTTP headers
            **kwargs: Ek request parametreleri
            
        Returns:
            Parse edilmiş response data
            
        Raises:
            EspoCRMError: API hatası
            EspoCRMConnectionError: Bağlantı hatası
        """
        with self._lock:
            if self._closed:
                raise EspoCRMError("Client is closed")
        
        # Request context oluştur
        with self.request_context() as request_id:
            try:
                # Request'i logla
                self.logger.info(
                    "API request started",
                    method=method,
                    endpoint=endpoint,
                    request_id=request_id
                )
                
                # Data serialization
                json_data = None
                if data:
                    json_data = self.serializer.transform_for_espocrm(data)
                
                # HTTP request gönder
                response = self.http_client.request(
                    method=method,
                    endpoint=endpoint,
                    params=params,
                    json=json_data,
                    headers=headers,
                    **kwargs
                )
                
                # Response parse et
                try:
                    response_data = response.json()
                except ValueError:
                    # JSON parse edilemezse raw text döndür
                    response_data = {'raw_response': response.text}
                
                # EspoCRM response format'ına çevir
                parsed_data = parse_espocrm_response(response_data)
                
                # Success log
                self.logger.info(
                    "API request completed",
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    request_id=request_id
                )
                
                return parsed_data
                
            except Exception as e:
                # Error log
                self.logger.error(
                    "API request failed",
                    method=method,
                    endpoint=endpoint,
                    error=str(e),
                    request_id=request_id
                )
                raise
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """GET request gönderir."""
        return self.request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """POST request gönderir."""
        return self.request('POST', endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """PUT request gönderir."""
        return self.request('PUT', endpoint, data=data, **kwargs)
    
    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """PATCH request gönderir."""
        return self.request('PATCH', endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request gönderir."""
        return self.request('DELETE', endpoint, **kwargs)
    
    def test_connection(self) -> bool:
        """
        EspoCRM server'a bağlantıyı test eder.
        
        Returns:
            Bağlantı başarılı mı
            
        Raises:
            EspoCRMConnectionError: Bağlantı hatası
            EspoCRMAuthenticationError: Authentication hatası
        """
        try:
            # Basit bir endpoint'e request gönder
            response = self.get('App/user')
            return response.get('success', True)
            
        except EspoCRMAuthenticationError:
            self.logger.error("Authentication failed during connection test")
            raise
        except EspoCRMConnectionError:
            self.logger.error("Connection failed during connection test")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during connection test: {e}")
            raise EspoCRMConnectionError(f"Connection test failed: {e}")
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        EspoCRM server bilgilerini alır.
        
        Returns:
            Server bilgileri
        """
        try:
            return self.get('App/about')
        except Exception as e:
            self.logger.warning(f"Could not retrieve server info: {e}")
            return {}
    
    def close(self):
        """Client'ı kapatır ve kaynakları temizler."""
        with self._lock:
            if self._closed:
                return
            
            self._closed = True
            
            # HTTP client'ı kapat
            if hasattr(self, 'http_client'):
                self.http_client.close()
            
            # Logger context'i temizle
            self.logger.clear_context()
            
            self.logger.info("EspoCRM client closed")
    
    def is_closed(self) -> bool:
        """Client'ın kapalı olup olmadığını kontrol eder."""
        with self._lock:
            return self._closed
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EspoCRMClient("
            f"base_url={self.base_url!r}, "
            f"auth_type={self.auth.get_auth_type()!r}, "
            f"closed={self._closed})"
        )


def create_client(
    base_url: str,
    auth: AuthenticationBase,
    config: Optional[ClientConfig] = None,
    **kwargs
) -> EspoCRMClient:
    """
    EspoCRM client oluşturur.
    
    Args:
        base_url: EspoCRM server'ın base URL'i
        auth: Authentication instance'ı
        config: Client konfigürasyonu
        **kwargs: Ek parametreler
        
    Returns:
        EspoCRMClient instance'ı
        
    Example:
        >>> from espocrm.auth import APIKeyAuth
        >>> auth = APIKeyAuth(api_key="your-api-key")
        >>> client = create_client("https://your-espocrm.com", auth)
    """
    return EspoCRMClient(base_url, auth, config, **kwargs)


    # CRUD convenience methods
    def create_entity(self, entity_type: str, data, **kwargs):
        """Entity oluşturur (CRUD client'a delegate eder)."""
        return self.crud.create(entity_type, data, **kwargs)
    
    def get_entity(self, entity_type: str, entity_id: str, **kwargs):
        """Entity getirir (CRUD client'a delegate eder)."""
        return self.crud.read(entity_type, entity_id, **kwargs)
    
    def update_entity(self, entity_type: str, entity_id: str, data, **kwargs):
        """Entity günceller (CRUD client'a delegate eder)."""
        return self.crud.update(entity_type, entity_id, data, **kwargs)
    
    def delete_entity(self, entity_type: str, entity_id: str, **kwargs):
        """Entity siler (CRUD client'a delegate eder)."""
        return self.crud.delete(entity_type, entity_id, **kwargs)
    
    def list_entities(self, entity_type: str, search_params=None, **kwargs):
        """Entity listesi getirir (CRUD client'a delegate eder)."""
        return self.crud.list(entity_type, search_params=search_params, **kwargs)
    
    def search_entities(self, entity_type: str, search_params, **kwargs):
        """Entity arama yapar (CRUD client'a delegate eder)."""
        return self.crud.search(entity_type, search_params, **kwargs)
    
    def count_entities(self, entity_type: str, where=None, **kwargs):
        """Entity sayısını döndürür (CRUD client'a delegate eder)."""
        return self.crud.count(entity_type, where=where, **kwargs)
    
    def entity_exists(self, entity_type: str, entity_id: str, **kwargs):
        """Entity'nin var olup olmadığını kontrol eder (CRUD client'a delegate eder)."""
        return self.crud.exists(entity_type, entity_id, **kwargs)
    
    # Relationship convenience methods
    def list_related_entities(self, entity_type: str, entity_id: str, link: str, **kwargs):
        """İlişkili entity'leri listeler (Relationship client'a delegate eder)."""
        return self.relationships.list_related(entity_type, entity_id, link, **kwargs)
    
    def link_entities(self, entity_type: str, entity_id: str, link: str, target_ids, **kwargs):
        """Entity'leri ilişkilendirir (Relationship client'a delegate eder)."""
        if isinstance(target_ids, str):
            return self.relationships.link_single(entity_type, entity_id, link, target_ids, **kwargs)
        elif isinstance(target_ids, list):
            return self.relationships.link_multiple(entity_type, entity_id, link, target_ids, **kwargs)
        else:
            raise ValueError("target_ids string veya liste formatında olmalıdır")
    
    def unlink_entities(self, entity_type: str, entity_id: str, link: str, target_ids=None, **kwargs):
        """Entity ilişkilerini kaldırır (Relationship client'a delegate eder)."""
        if target_ids is None:
            return self.relationships.unlink_all(entity_type, entity_id, link, **kwargs)
        elif isinstance(target_ids, str):
            return self.relationships.unlink_single(entity_type, entity_id, link, target_ids, **kwargs)
        elif isinstance(target_ids, list):
            return self.relationships.unlink_multiple(entity_type, entity_id, link, target_ids, **kwargs)
        else:
            raise ValueError("target_ids None, string veya liste formatında olmalıdır")
    
    def mass_relate_entities(self, entity_type: str, entity_id: str, link: str, where, **kwargs):
        """Mass relate operasyonu gerçekleştirir (Relationship client'a delegate eder)."""
        return self.relationships.mass_relate(entity_type, entity_id, link, where, **kwargs)
    
    def check_entity_relationship(self, entity_type: str, entity_id: str, link: str, target_id: str, **kwargs):
        """Entity ilişkisinin var olup olmadığını kontrol eder (Relationship client'a delegate eder)."""
        return self.relationships.check_relationship_exists(entity_type, entity_id, link, target_id, **kwargs)
    
    # Stream convenience methods
    def get_user_stream(self, **kwargs):
        """Kullanıcı stream'ini getirir (Stream client'a delegate eder)."""
        return self.stream.list_user_stream(**kwargs)
    
    def get_entity_stream(self, entity_type: str, entity_id: str, **kwargs):
        """Entity stream'ini getirir (Stream client'a delegate eder)."""
        return self.stream.list_entity_stream(entity_type, entity_id, **kwargs)
    
    def post_to_stream(self, parent_type: str, parent_id: str, post: str, **kwargs):
        """Stream'e post yapar (Stream client'a delegate eder)."""
        return self.stream.post_to_stream(parent_type, parent_id, post, **kwargs)
    
    def follow_entity(self, entity_type: str, entity_id: str, **kwargs):
        """Entity'yi takip eder (Stream client'a delegate eder)."""
        return self.stream.follow_entity(entity_type, entity_id, **kwargs)
    
    def unfollow_entity(self, entity_type: str, entity_id: str, **kwargs):
        """Entity takibini bırakır (Stream client'a delegate eder)."""
        return self.stream.unfollow_entity(entity_type, entity_id, **kwargs)
    
    def is_following_entity(self, entity_type: str, entity_id: str, **kwargs):
        """Entity'nin takip edilip edilmediğini kontrol eder (Stream client'a delegate eder)."""
        return self.stream.is_following_entity(entity_type, entity_id, **kwargs)
    
    def get_stream_note(self, note_id: str, **kwargs):
        """Stream note'u getirir (Stream client'a delegate eder)."""
        return self.stream.get_stream_note(note_id, **kwargs)
    
    def delete_stream_note(self, note_id: str, **kwargs):
        """Stream note'u siler (Stream client'a delegate eder)."""
        return self.stream.delete_stream_note(note_id, **kwargs)
    
    # Attachment convenience methods
    def upload_file(self, file_path, related_type: str, field: str = "file", **kwargs):
        """File field için dosya yükler (Attachment client'a delegate eder)."""
        return self.attachments.upload_file(file_path, related_type, field, **kwargs)
    
    def upload_attachment(self, file_path, parent_type: str, **kwargs):
        """Attachment-Multiple field için dosya yükler (Attachment client'a delegate eder)."""
        return self.attachments.upload_attachment(file_path, parent_type, **kwargs)
    
    def upload_from_bytes(self, file_data: bytes, filename: str, **kwargs):
        """Bytes veriden dosya yükler (Attachment client'a delegate eder)."""
        return self.attachments.upload_from_bytes(file_data, filename, **kwargs)
    
    def download_file(self, attachment_id: str, save_path=None, **kwargs):
        """Attachment dosyasını indirir (Attachment client'a delegate eder)."""
        return self.attachments.download_file(attachment_id, save_path, **kwargs)
    
    def download_to_bytes(self, attachment_id: str, **kwargs):
        """Attachment dosyasını bytes olarak indirir (Attachment client'a delegate eder)."""
        return self.attachments.download_to_bytes(attachment_id, **kwargs)
    
    def get_attachment(self, attachment_id: str, **kwargs):
        """Attachment bilgilerini getirir (Attachment client'a delegate eder)."""
        return self.attachments.get_attachment(attachment_id, **kwargs)
    
    def list_attachments(self, parent_type=None, parent_id=None, field=None, **kwargs):
        """Attachment listesini getirir (Attachment client'a delegate eder)."""
        return self.attachments.list_attachments(parent_type, parent_id, field, **kwargs)
    
    def delete_attachment(self, attachment_id: str, **kwargs):
        """Attachment'ı siler (Attachment client'a delegate eder)."""
        return self.attachments.delete_attachment(attachment_id, **kwargs)
    
    def bulk_upload_files(self, upload_request, **kwargs):
        """Bulk dosya yükleme (Attachment client'a delegate eder)."""
        return self.attachments.bulk_upload(upload_request, **kwargs)
    
    def bulk_download_files(self, attachment_ids, download_dir, **kwargs):
        """Bulk dosya indirme (Attachment client'a delegate eder)."""
        return self.attachments.bulk_download(attachment_ids, download_dir, **kwargs)
    
    def copy_attachment(self, source_attachment_id: str, **kwargs):
        """Attachment'ı kopyalar (Attachment client'a delegate eder)."""
        return self.attachments.copy_attachment(source_attachment_id, **kwargs)
    
    def get_file_info(self, attachment_id: str, **kwargs):
        """Dosya bilgilerini getirir (Attachment client'a delegate eder)."""
        return self.attachments.get_file_info(attachment_id, **kwargs)
    
    # Metadata convenience methods
    def get_application_metadata(self, force_refresh: bool = False, **kwargs):
        """Application metadata'sını alır (Metadata client'a delegate eder)."""
        return self.metadata.get_application_metadata(force_refresh=force_refresh, **kwargs)
    
    def get_entity_metadata(self, entity_type: str, force_refresh: bool = False, **kwargs):
        """Entity metadata'sını alır (Metadata client'a delegate eder)."""
        return self.metadata.get_entity_metadata(entity_type, force_refresh=force_refresh, **kwargs)
    
    def discover_entities(self, force_refresh: bool = False, **kwargs):
        """Mevcut entity türlerini keşfeder (Metadata client'a delegate eder)."""
        return self.metadata.discover_entities(force_refresh=force_refresh, **kwargs)
    
    def discover_entity_fields(self, entity_type: str, field_type=None, force_refresh: bool = False, **kwargs):
        """Entity field'larını keşfeder (Metadata client'a delegate eder)."""
        return self.metadata.discover_entity_fields(entity_type, field_type=field_type, force_refresh=force_refresh, **kwargs)
    
    def discover_entity_relationships(self, entity_type: str, relationship_type=None, force_refresh: bool = False, **kwargs):
        """Entity ilişkilerini keşfeder (Metadata client'a delegate eder)."""
        return self.metadata.discover_entity_relationships(entity_type, relationship_type=relationship_type, force_refresh=force_refresh, **kwargs)
    
    def validate_entity_data(self, entity_type: str, data, force_refresh: bool = False, **kwargs):
        """Entity verilerini schema'ya göre doğrular (Metadata client'a delegate eder)."""
        return self.metadata.validate_entity_data(entity_type, data, force_refresh=force_refresh, **kwargs)
    
    def get_enum_options(self, entity_type: str, field_name: str, force_refresh: bool = False, **kwargs):
        """Enum field seçeneklerini alır (Metadata client'a delegate eder)."""
        return self.metadata.get_enum_options(entity_type, field_name, force_refresh=force_refresh, **kwargs)
    
    def get_required_fields(self, entity_type: str, force_refresh: bool = False, **kwargs):
        """Entity'nin zorunlu field'larını alır (Metadata client'a delegate eder)."""
        return self.metadata.get_required_fields(entity_type, force_refresh=force_refresh, **kwargs)
    
    def detect_api_capabilities(self, force_refresh: bool = False, **kwargs):
        """API yeteneklerini tespit eder (Metadata client'a delegate eder)."""
        return self.metadata.detect_api_capabilities(force_refresh=force_refresh, **kwargs)
    
    def warm_metadata_cache(self, entity_types=None, **kwargs):
        """Metadata cache'ini önceden yükler (Metadata client'a delegate eder)."""
        return self.metadata.warm_cache(entity_types=entity_types, **kwargs)
    
    def clear_metadata_cache(self, **kwargs):
        """Metadata cache'ini temizler (Metadata client'a delegate eder)."""
        return self.metadata.clear_cache(**kwargs)
    
    def get_metadata_cache_info(self, **kwargs):
        """Metadata cache bilgilerini alır (Metadata client'a delegate eder)."""
        return self.metadata.get_cache_info(**kwargs)
    
    def entity_exists(self, entity_type: str, force_refresh: bool = False, **kwargs):
        """Entity'nin var olup olmadığını kontrol eder (Metadata client'a delegate eder)."""
        return self.metadata.entity_exists(entity_type, force_refresh=force_refresh, **kwargs)
    
    def field_exists(self, entity_type: str, field_name: str, force_refresh: bool = False, **kwargs):
        """Field'ın var olup olmadığını kontrol eder (Metadata client'a delegate eder)."""
        return self.metadata.field_exists(entity_type, field_name, force_refresh=force_refresh, **kwargs)
    
    def relationship_exists(self, entity_type: str, link_name: str, force_refresh: bool = False, **kwargs):
        """İlişkinin var olup olmadığını kontrol eder (Metadata client'a delegate eder)."""
        return self.metadata.relationship_exists(entity_type, link_name, force_refresh=force_refresh, **kwargs)


# Export edilecek sınıf ve fonksiyonlar
__all__ = [
    "EspoCRMClient",
    "create_client",
]