"""EspoCRM Metadata Client.

Bu modül EspoCRM API'nin metadata sistemini yöneten MetadataClient sınıfını içerir.
Application metadata, entity discovery, field information, relationship mapping,
schema validation ve intelligent caching özellikleri sağlar.
"""

import time
import threading
from typing import Any, Dict, List, Optional, Set, Type, Union
from datetime import datetime, timedelta

from ..exceptions import EspoCRMError, EspoCRMValidationError
from ..models.metadata import (
    ApplicationMetadata,
    EntityMetadata,
    FieldMetadata,
    RelationshipMetadata,
    MetadataRequest,
    FieldType,
    RelationshipType
)
from ..models.responses import parse_entity_response
from ..utils.helpers import timing_decorator
from ..logging import get_logger


class MetadataCache:
    """Metadata caching sistemi."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """Cache'i başlatır.
        
        Args:
            ttl_seconds: Time to live (saniye)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den veri alır."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # TTL kontrolü
            if self._is_expired(key):
                self._remove(key)
                return None
            
            return self._cache[key].get("data")
    
    def set(self, key: str, data: Any) -> None:
        """Cache'e veri ekler."""
        with self._lock:
            self._cache[key] = {"data": data}
            self._timestamps[key] = datetime.now()
    
    def remove(self, key: str) -> None:
        """Cache'den veri siler."""
        with self._lock:
            self._remove(key)
    
    def clear(self) -> None:
        """Cache'i temizler."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def _remove(self, key: str) -> None:
        """Internal remove method."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def _is_expired(self, key: str) -> bool:
        """Key'in expire olup olmadığını kontrol eder."""
        if key not in self._timestamps:
            return True
        
        timestamp = self._timestamps[key]
        return datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Cache bilgilerini döndürür."""
        with self._lock:
            total_keys = len(self._cache)
            expired_keys = sum(1 for key in self._cache.keys() if self._is_expired(key))
            
            return {
                "total_keys": total_keys,
                "active_keys": total_keys - expired_keys,
                "expired_keys": expired_keys,
                "ttl_seconds": self.ttl_seconds
            }


class MetadataClient:
    """EspoCRM Metadata Client.
    
    Bu sınıf EspoCRM API'nin metadata sistemini yönetir:
    - Application metadata alma
    - Entity discovery
    - Field information
    - Relationship mapping
    - Schema validation
    - Intelligent caching
    - Dynamic typing
    """
    
    def __init__(self, main_client, cache_ttl: int = 3600):
        """Metadata client'ı başlatır.
        
        Args:
            main_client: Ana EspoCRM client instance'ı
            cache_ttl: Cache TTL (saniye)
        """
        self.client = main_client
        self.logger = get_logger(f"{__name__}.MetadataClient")
        self.cache = MetadataCache(ttl_seconds=cache_ttl)
        
        # Internal state
        self._application_metadata: Optional[ApplicationMetadata] = None
        self._entity_types: Optional[Set[str]] = None
        self._last_refresh: Optional[datetime] = None
    
    @timing_decorator
    def get_application_metadata(
        self,
        force_refresh: bool = False,
        include_client_defs: bool = True,
        include_scopes: bool = True,
        include_fields: bool = True
    ) -> ApplicationMetadata:
        """Application metadata'sını alır.
        
        Args:
            force_refresh: Cache'i bypass et
            include_client_defs: Client definitions dahil et
            include_scopes: Scopes dahil et
            include_fields: Global fields dahil et
            
        Returns:
            Application metadata
            
        Raises:
            EspoCRMError: API hatası
            
        Example:
            >>> metadata = client.metadata.get_application_metadata()
            >>> entity_types = metadata.get_entity_types()
            >>> print(f"Available entities: {entity_types}")
        """
        cache_key = f"app_metadata_{include_client_defs}_{include_scopes}_{include_fields}"
        
        # Cache kontrolü
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self.logger.debug("Application metadata loaded from cache")
                return cached_data
        
        self.logger.info("Fetching application metadata from API")
        
        try:
            # Request parametreleri
            request = MetadataRequest(
                include_client_defs=include_client_defs,
                include_scopes=include_scopes,
                include_fields=include_fields
            )
            
            # API request
            response_data = self.client.get("Metadata", params=request.to_query_params())
            
            # Parse metadata
            app_metadata = ApplicationMetadata(**response_data)
            
            # Cache'e kaydet
            self.cache.set(cache_key, app_metadata)
            self._application_metadata = app_metadata
            self._last_refresh = datetime.now()
            
            self.logger.info(
                "Application metadata fetched successfully",
                entity_count=len(app_metadata.get_entity_types())
            )
            
            return app_metadata
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch application metadata",
                error=str(e)
            )
            raise
    
    @timing_decorator
    def get_specific_metadata(
        self,
        key: str,
        force_refresh: bool = False
    ) -> Any:
        """Specific metadata path'ini alır.
        
        Args:
            key: Metadata path (örn: 'entityDefs.Lead.fields.status.options')
            force_refresh: Cache'i bypass et
            
        Returns:
            Metadata verisi
            
        Example:
            >>> options = client.metadata.get_specific_metadata(
            ...     'entityDefs.Lead.fields.status.options'
            ... )
            >>> print(f"Lead status options: {options}")
        """
        cache_key = f"specific_{key}"
        
        # Cache kontrolü
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self.logger.debug(f"Specific metadata loaded from cache: {key}")
                return cached_data
        
        self.logger.info(f"Fetching specific metadata: {key}")
        
        try:
            # Request parametreleri
            request = MetadataRequest(key=key)
            
            # API request
            response_data = self.client.get("Metadata", params=request.to_query_params())
            
            # Cache'e kaydet
            self.cache.set(cache_key, response_data)
            
            self.logger.info(f"Specific metadata fetched successfully: {key}")
            
            return response_data
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch specific metadata",
                key=key,
                error=str(e)
            )
            raise
    
    def get_entity_metadata(
        self,
        entity_type: str,
        force_refresh: bool = False
    ) -> Optional[EntityMetadata]:
        """Entity metadata'sını alır.
        
        Args:
            entity_type: Entity türü
            force_refresh: Cache'i bypass et
            
        Returns:
            Entity metadata (yoksa None)
            
        Example:
            >>> account_meta = client.metadata.get_entity_metadata("Account")
            >>> if account_meta:
            ...     fields = list(account_meta.fields.keys())
            ...     print(f"Account fields: {fields}")
        """
        app_metadata = self.get_application_metadata(force_refresh=force_refresh)
        return app_metadata.get_entity_metadata(entity_type)
    
    def get_entity_field_metadata(
        self,
        entity_type: str,
        field_name: str,
        force_refresh: bool = False
    ) -> Optional[FieldMetadata]:
        """Entity field metadata'sını alır.
        
        Args:
            entity_type: Entity türü
            field_name: Field adı
            force_refresh: Cache'i bypass et
            
        Returns:
            Field metadata (yoksa None)
        """
        entity_meta = self.get_entity_metadata(entity_type, force_refresh)
        if entity_meta:
            return entity_meta.get_field(field_name)
        return None
    
    def get_entity_relationship_metadata(
        self,
        entity_type: str,
        link_name: str,
        force_refresh: bool = False
    ) -> Optional[RelationshipMetadata]:
        """Entity relationship metadata'sını alır.
        
        Args:
            entity_type: Entity türü
            link_name: Link adı
            force_refresh: Cache'i bypass et
            
        Returns:
            Relationship metadata (yoksa None)
        """
        entity_meta = self.get_entity_metadata(entity_type, force_refresh)
        if entity_meta:
            return entity_meta.get_link(link_name)
        return None
    
    def discover_entities(self, force_refresh: bool = False) -> List[str]:
        """Mevcut entity türlerini keşfeder.
        
        Args:
            force_refresh: Cache'i bypass et
            
        Returns:
            Entity türleri listesi
            
        Example:
            >>> entities = client.metadata.discover_entities()
            >>> print(f"Available entities: {entities}")
        """
        app_metadata = self.get_application_metadata(force_refresh=force_refresh)
        entity_types = app_metadata.get_entity_types()
        
        self._entity_types = set(entity_types)
        
        self.logger.info(
            "Entity discovery completed",
            entity_count=len(entity_types)
        )
        
        return entity_types
    
    def discover_entity_fields(
        self,
        entity_type: str,
        field_type: Optional[FieldType] = None,
        force_refresh: bool = False
    ) -> Dict[str, FieldMetadata]:
        """Entity field'larını keşfeder.
        
        Args:
            entity_type: Entity türü
            field_type: Belirli field türü (opsiyonel)
            force_refresh: Cache'i bypass et
            
        Returns:
            Field metadata dictionary
            
        Example:
            >>> # Tüm field'lar
            >>> fields = client.metadata.discover_entity_fields("Account")
            >>> 
            >>> # Sadece enum field'lar
            >>> enum_fields = client.metadata.discover_entity_fields(
            ...     "Account", 
            ...     field_type=FieldType.ENUM
            ... )
        """
        entity_meta = self.get_entity_metadata(entity_type, force_refresh)
        if not entity_meta:
            return {}
        
        fields = entity_meta.fields
        
        # Field type filtresi
        if field_type:
            fields = {
                name: field_meta
                for name, field_meta in fields.items()
                if field_meta.type == field_type
            }
        
        self.logger.info(
            "Entity field discovery completed",
            entity_type=entity_type,
            field_count=len(fields),
            field_type=field_type.value if field_type else "all"
        )
        
        return fields
    
    def discover_entity_relationships(
        self,
        entity_type: str,
        relationship_type: Optional[RelationshipType] = None,
        force_refresh: bool = False
    ) -> Dict[str, RelationshipMetadata]:
        """Entity ilişkilerini keşfeder.
        
        Args:
            entity_type: Entity türü
            relationship_type: Belirli ilişki türü (opsiyonel)
            force_refresh: Cache'i bypass et
            
        Returns:
            Relationship metadata dictionary
            
        Example:
            >>> # Tüm ilişkiler
            >>> relationships = client.metadata.discover_entity_relationships("Account")
            >>> 
            >>> # Sadece one-to-many ilişkiler
            >>> one_to_many = client.metadata.discover_entity_relationships(
            ...     "Account",
            ...     relationship_type=RelationshipType.ONE_TO_MANY
            ... )
        """
        entity_meta = self.get_entity_metadata(entity_type, force_refresh)
        if not entity_meta:
            return {}
        
        relationships = entity_meta.links
        
        # Relationship type filtresi
        if relationship_type:
            relationships = {
                name: rel_meta
                for name, rel_meta in relationships.items()
                if rel_meta.type == relationship_type
            }
        
        self.logger.info(
            "Entity relationship discovery completed",
            entity_type=entity_type,
            relationship_count=len(relationships),
            relationship_type=relationship_type.value if relationship_type else "all"
        )
        
        return relationships
    
    def validate_entity_data(
        self,
        entity_type: str,
        data: Dict[str, Any],
        force_refresh: bool = False
    ) -> Dict[str, List[str]]:
        """Entity verilerini schema'ya göre doğrular.
        
        Args:
            entity_type: Entity türü
            data: Doğrulanacak veri
            force_refresh: Cache'i bypass et
            
        Returns:
            Validation hataları (field_name -> error_list)
            
        Example:
            >>> data = {"name": "Test", "invalid_field": "value"}
            >>> errors = client.metadata.validate_entity_data("Account", data)
            >>> if errors:
            ...     print(f"Validation errors: {errors}")
        """
        app_metadata = self.get_application_metadata(force_refresh=force_refresh)
        return app_metadata.validate_entity_data(entity_type, data)
    
    def get_field_validation_rules(
        self,
        entity_type: str,
        field_name: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Field validation kurallarını alır.
        
        Args:
            entity_type: Entity türü
            field_name: Field adı
            force_refresh: Cache'i bypass et
            
        Returns:
            Validation kuralları
        """
        field_meta = self.get_entity_field_metadata(entity_type, field_name, force_refresh)
        if field_meta:
            return field_meta.get_validation_rules()
        return {}
    
    def get_enum_options(
        self,
        entity_type: str,
        field_name: str,
        force_refresh: bool = False
    ) -> Optional[List[str]]:
        """Enum field seçeneklerini alır.
        
        Args:
            entity_type: Entity türü
            field_name: Field adı
            force_refresh: Cache'i bypass et
            
        Returns:
            Enum seçenekleri (yoksa None)
            
        Example:
            >>> options = client.metadata.get_enum_options("Lead", "status")
            >>> if options:
            ...     print(f"Lead status options: {options}")
        """
        field_meta = self.get_entity_field_metadata(entity_type, field_name, force_refresh)
        if field_meta and field_meta.is_enum_field():
            return field_meta.options
        return None
    
    def get_required_fields(
        self,
        entity_type: str,
        force_refresh: bool = False
    ) -> List[str]:
        """Entity'nin zorunlu field'larını alır.
        
        Args:
            entity_type: Entity türü
            force_refresh: Cache'i bypass et
            
        Returns:
            Zorunlu field'lar listesi
        """
        entity_meta = self.get_entity_metadata(entity_type, force_refresh)
        if entity_meta:
            return entity_meta.get_required_fields()
        return []
    
    def get_relationship_fields(
        self,
        entity_type: str,
        force_refresh: bool = False
    ) -> Dict[str, FieldMetadata]:
        """Entity'nin ilişki field'larını alır.
        
        Args:
            entity_type: Entity türü
            force_refresh: Cache'i bypass et
            
        Returns:
            İlişki field'ları
        """
        entity_meta = self.get_entity_metadata(entity_type, force_refresh)
        if entity_meta:
            return entity_meta.get_relationship_fields()
        return {}
    
    def detect_api_capabilities(self, force_refresh: bool = False) -> Dict[str, Any]:
        """API yeteneklerini tespit eder.
        
        Args:
            force_refresh: Cache'i bypass et
            
        Returns:
            API capabilities bilgisi
        """
        cache_key = "api_capabilities"
        
        # Cache kontrolü
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        self.logger.info("Detecting API capabilities")
        
        try:
            app_metadata = self.get_application_metadata(force_refresh=force_refresh)
            
            capabilities = {
                "entities": app_metadata.get_entity_types(),
                "entity_count": len(app_metadata.get_entity_types()),
                "has_client_defs": bool(app_metadata.client_defs),
                "has_scopes": bool(app_metadata.scopes),
                "has_global_fields": bool(app_metadata.fields),
                "has_app_config": bool(app_metadata.app),
                "supported_field_types": list(set(
                    field_meta.type.value
                    for entity_meta in app_metadata.entity_defs.values()
                    for field_meta in entity_meta.fields.values()
                )),
                "supported_relationship_types": list(set(
                    rel_meta.type.value
                    for entity_meta in app_metadata.entity_defs.values()
                    for rel_meta in entity_meta.links.values()
                )),
                "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None
            }
            
            # Cache'e kaydet
            self.cache.set(cache_key, capabilities)
            
            self.logger.info(
                "API capabilities detected",
                entity_count=capabilities["entity_count"],
                field_types=len(capabilities["supported_field_types"]),
                relationship_types=len(capabilities["supported_relationship_types"])
            )
            
            return capabilities
            
        except Exception as e:
            self.logger.error(
                "Failed to detect API capabilities",
                error=str(e)
            )
            raise
    
    def warm_cache(self, entity_types: Optional[List[str]] = None) -> None:
        """Cache'i önceden yükler.
        
        Args:
            entity_types: Belirli entity'ler (yoksa tümü)
            
        Example:
            >>> # Tüm metadata'yı cache'e yükle
            >>> client.metadata.warm_cache()
            >>> 
            >>> # Sadece belirli entity'leri yükle
            >>> client.metadata.warm_cache(["Account", "Contact"])
        """
        self.logger.info("Starting cache warming")
        
        try:
            # Application metadata'yı yükle
            app_metadata = self.get_application_metadata(force_refresh=True)
            
            # Entity types belirle
            if entity_types is None:
                entity_types = app_metadata.get_entity_types()
            
            # Her entity için metadata'yı cache'e yükle
            for entity_type in entity_types:
                try:
                    self.get_entity_metadata(entity_type, force_refresh=True)
                    self.logger.debug(f"Cached metadata for entity: {entity_type}")
                except Exception as e:
                    self.logger.warning(
                        f"Failed to cache metadata for entity: {entity_type}",
                        error=str(e)
                    )
            
            # API capabilities'i yükle
            self.detect_api_capabilities(force_refresh=True)
            
            self.logger.info(
                "Cache warming completed",
                entity_count=len(entity_types)
            )
            
        except Exception as e:
            self.logger.error(
                "Cache warming failed",
                error=str(e)
            )
            raise
    
    def clear_cache(self) -> None:
        """Cache'i temizler.
        
        Example:
            >>> client.metadata.clear_cache()
        """
        self.cache.clear()
        self._application_metadata = None
        self._entity_types = None
        self._last_refresh = None
        
        self.logger.info("Metadata cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Cache bilgilerini döndürür.
        
        Returns:
            Cache istatistikleri
        """
        cache_info = self.cache.get_cache_info()
        cache_info.update({
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "cached_entity_count": len(self._entity_types) if self._entity_types else 0
        })
        
        return cache_info
    
    def entity_exists(self, entity_type: str, force_refresh: bool = False) -> bool:
        """Entity'nin var olup olmadığını kontrol eder.
        
        Args:
            entity_type: Entity türü
            force_refresh: Cache'i bypass et
            
        Returns:
            Entity var ise True
        """
        if not force_refresh and self._entity_types:
            return entity_type in self._entity_types
        
        entity_types = self.discover_entities(force_refresh=force_refresh)
        return entity_type in entity_types
    
    def field_exists(
        self,
        entity_type: str,
        field_name: str,
        force_refresh: bool = False
    ) -> bool:
        """Field'ın var olup olmadığını kontrol eder.
        
        Args:
            entity_type: Entity türü
            field_name: Field adı
            force_refresh: Cache'i bypass et
            
        Returns:
            Field var ise True
        """
        entity_meta = self.get_entity_metadata(entity_type, force_refresh)
        if entity_meta:
            return entity_meta.has_field(field_name)
        return False
    
    def relationship_exists(
        self,
        entity_type: str,
        link_name: str,
        force_refresh: bool = False
    ) -> bool:
        """İlişkinin var olup olmadığını kontrol eder.
        
        Args:
            entity_type: Entity türü
            link_name: Link adı
            force_refresh: Cache'i bypass et
            
        Returns:
            İlişki var ise True
        """
        entity_meta = self.get_entity_metadata(entity_type, force_refresh)
        if entity_meta:
            return entity_meta.has_link(link_name)
        return False


# Export edilecek sınıflar
__all__ = [
    "MetadataCache",
    "MetadataClient",
]