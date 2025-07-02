"""EspoCRM API request modelleri.

Bu modül EspoCRM API'ye gönderilecek request'ler için Pydantic modellerini içerir.
Relationship operations, link/unlink requests ve validation sağlar.
"""

import json
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from .base import EspoCRMBaseModel
from .search import SearchParams, WhereClause


class RelationshipRequest(EspoCRMBaseModel):
    """Relationship operasyonları için base request sınıfı."""
    
    entity_type: str = Field(
        description="Ana entity türü",
        min_length=1,
        max_length=100
    )
    
    entity_id: str = Field(
        description="Ana entity ID'si",
        min_length=17,
        max_length=17
    )
    
    link: str = Field(
        description="Relationship link adı",
        min_length=1,
        max_length=100
    )
    
    @field_validator("entity_id")
    @classmethod
    def validate_entity_id(cls, v: str) -> str:
        """Entity ID formatını doğrular."""
        if not v.isalnum():
            raise ValueError("Entity ID sadece alphanumeric karakterler içermelidir")
        return v
    
    @field_validator("link")
    @classmethod
    def validate_link(cls, v: str) -> str:
        """Link adını doğrular."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Link adı sadece alphanumeric karakterler, _ ve - içermelidir")
        return v
    
    def get_endpoint(self) -> str:
        """API endpoint'ini döndürür."""
        return f"{self.entity_type}/{self.entity_id}/{self.link}"


class LinkRequest(RelationshipRequest):
    """Entity'ler arası link oluşturma request'i.
    
    EspoCRM API'nin link operasyonları için kullanılır:
    - Tek kayıt ilişkilendirme (id parametresi)
    - Çoklu kayıt ilişkilendirme (ids parametresi)
    - Mass relate operasyonu (massRelate + where parametreleri)
    """
    
    # Link parametreleri - sadece biri kullanılmalı
    id: Optional[str] = Field(
        default=None,
        description="İlişkilendirilecek tek kayıt ID'si",
        min_length=17,
        max_length=17
    )
    
    ids: Optional[List[str]] = Field(
        default=None,
        description="İlişkilendirilecek kayıt ID'leri listesi",
        min_length=1,
        max_length=1000
    )
    
    mass_relate: Optional[bool] = Field(
        default=None,
        description="Mass relate operasyonu kullanılsın mı",
        alias="massRelate"
    )
    
    where: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Mass relate için search criteria"
    )
    
    # Ek parametreler
    foreign_id: Optional[str] = Field(
        default=None,
        description="Foreign entity ID (bazı relationship türleri için)",
        alias="foreignId",
        min_length=17,
        max_length=17
    )
    
    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
    }
    
    @field_validator("id", "foreign_id")
    @classmethod
    def validate_id_format(cls, v: Optional[str]) -> Optional[str]:
        """ID formatını doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("ID string formatında olmalıdır")
        
        if len(v) != 17:
            raise ValueError("EspoCRM ID'si 17 karakter uzunluğunda olmalıdır")
        
        if not v.isalnum():
            raise ValueError("EspoCRM ID'si sadece alphanumeric karakterler içermelidir")
        
        return v
    
    @field_validator("ids")
    @classmethod
    def validate_ids_format(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """ID listesi formatını doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("IDs liste formatında olmalıdır")
        
        if len(v) == 0:
            raise ValueError("IDs listesi boş olamaz")
        
        for i, id_val in enumerate(v):
            if not isinstance(id_val, str):
                raise ValueError(f"ID[{i}] string formatında olmalıdır")
            
            if len(id_val) != 17:
                raise ValueError(f"ID[{i}] 17 karakter uzunluğunda olmalıdır")
            
            if not id_val.isalnum():
                raise ValueError(f"ID[{i}] sadece alphanumeric karakterler içermelidir")
        
        # Duplicate ID kontrolü
        if len(set(v)) != len(v):
            raise ValueError("IDs listesinde duplicate değerler olamaz")
        
        return v
    
    @model_validator(mode='after')
    def validate_link_parameters(self):
        """Link parametrelerini doğrular."""
        # Sadece bir link parametresi kullanılmalı
        param_count = sum([
            self.id is not None,
            self.ids is not None,
            self.mass_relate is True
        ])
        
        if param_count == 0:
            raise ValueError("En az bir link parametresi (id, ids, massRelate) belirtilmelidir")
        
        if param_count > 1:
            raise ValueError("Sadece bir link parametresi (id, ids, massRelate) kullanılabilir")
        
        # Mass relate için where clause gerekli
        if self.mass_relate and not self.where:
            raise ValueError("Mass relate operasyonu için where clause gereklidir")
        
        # Where clause sadece mass relate ile kullanılabilir
        if self.where and not self.mass_relate:
            raise ValueError("Where clause sadece mass relate operasyonu ile kullanılabilir")
        
        return self
    
    def get_link_type(self) -> str:
        """Link operasyon türünü döndürür."""
        if self.id:
            return "single"
        elif self.ids:
            return "multiple"
        elif self.mass_relate:
            return "mass_relate"
        else:
            return "unknown"
    
    def get_target_count(self) -> int:
        """Hedef kayıt sayısını döndürür."""
        if self.id:
            return 1
        elif self.ids:
            return len(self.ids)
        else:
            return 0  # Mass relate için bilinmiyor
    
    def to_api_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """API için dictionary formatına çevirir."""
        data = self.model_dump(exclude_none=exclude_none, by_alias=True)
        
        # Endpoint bilgilerini çıkar
        data.pop("entity_type", None)
        data.pop("entity_id", None)
        data.pop("link", None)
        
        return data


class UnlinkRequest(RelationshipRequest):
    """Entity'ler arası link kaldırma request'i.
    
    EspoCRM API'nin unlink operasyonları için kullanılır:
    - Tek kayıt ilişki kaldırma (id parametresi)
    - Çoklu kayıt ilişki kaldırma (ids parametresi)
    - Tüm ilişkileri kaldırma (parametresiz)
    """
    
    # Unlink parametreleri - opsiyonel
    id: Optional[str] = Field(
        default=None,
        description="İlişkisi kaldırılacak tek kayıt ID'si",
        min_length=17,
        max_length=17
    )
    
    ids: Optional[List[str]] = Field(
        default=None,
        description="İlişkisi kaldırılacak kayıt ID'leri listesi",
        min_length=1,
        max_length=1000
    )
    
    # Ek parametreler
    foreign_id: Optional[str] = Field(
        default=None,
        description="Foreign entity ID (bazı relationship türleri için)",
        alias="foreignId",
        min_length=17,
        max_length=17
    )
    
    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
    }
    
    @field_validator("id", "foreign_id")
    @classmethod
    def validate_id_format(cls, v: Optional[str]) -> Optional[str]:
        """ID formatını doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("ID string formatında olmalıdır")
        
        if len(v) != 17:
            raise ValueError("EspoCRM ID'si 17 karakter uzunluğunda olmalıdır")
        
        if not v.isalnum():
            raise ValueError("EspoCRM ID'si sadece alphanumeric karakterler içermelidir")
        
        return v
    
    @field_validator("ids")
    @classmethod
    def validate_ids_format(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """ID listesi formatını doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("IDs liste formatında olmalıdır")
        
        if len(v) == 0:
            raise ValueError("IDs listesi boş olamaz")
        
        for i, id_val in enumerate(v):
            if not isinstance(id_val, str):
                raise ValueError(f"ID[{i}] string formatında olmalıdır")
            
            if len(id_val) != 17:
                raise ValueError(f"ID[{i}] 17 karakter uzunluğunda olmalıdır")
            
            if not id_val.isalnum():
                raise ValueError(f"ID[{i}] sadece alphanumeric karakterler içermelidir")
        
        # Duplicate ID kontrolü
        if len(set(v)) != len(v):
            raise ValueError("IDs listesinde duplicate değerler olamaz")
        
        return v
    
    @model_validator(mode='after')
    def validate_unlink_parameters(self):
        """Unlink parametrelerini doğrular."""
        # ID ve IDs aynı anda kullanılamaz
        if self.id and self.ids:
            raise ValueError("ID ve IDs parametreleri aynı anda kullanılamaz")
        
        return self
    
    def get_unlink_type(self) -> str:
        """Unlink operasyon türünü döndürür."""
        if self.id:
            return "single"
        elif self.ids:
            return "multiple"
        else:
            return "all"  # Tüm ilişkileri kaldır
    
    def get_target_count(self) -> int:
        """Hedef kayıt sayısını döndürür."""
        if self.id:
            return 1
        elif self.ids:
            return len(self.ids)
        else:
            return 0  # Tüm ilişkiler için bilinmiyor
    
    def to_api_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """API için dictionary formatına çevirir."""
        data = self.model_dump(exclude_none=exclude_none, by_alias=True)
        
        # Endpoint bilgilerini çıkar
        data.pop("entity_type", None)
        data.pop("entity_id", None)
        data.pop("link", None)
        
        return data


class RelationshipListRequest(RelationshipRequest):
    """İlişkili kayıtları listeleme request'i.
    
    EspoCRM API'nin related records listesi için kullanılır.
    Search parameters ve pagination desteği sağlar.
    """
    
    # Search parameters
    search_params: Optional[SearchParams] = Field(
        default=None,
        description="Arama parametreleri"
    )
    
    # Manuel pagination parametreleri
    offset: Optional[int] = Field(
        default=None,
        description="Başlangıç offset'i",
        ge=0
    )
    
    max_size: Optional[int] = Field(
        default=None,
        description="Maksimum kayıt sayısı",
        alias="maxSize",
        ge=1,
        le=200
    )
    
    # Sorting parametreleri
    order_by: Optional[str] = Field(
        default=None,
        description="Sıralama field'ı",
        alias="orderBy",
        max_length=100
    )
    
    order: Optional[str] = Field(
        default=None,
        description="Sıralama yönü ('asc' veya 'desc')",
        pattern="^(asc|desc)$"
    )
    
    # Field selection
    select: Optional[List[str]] = Field(
        default=None,
        description="Seçilecek field'lar",
        max_length=100
    )
    
    # Filtering
    where: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Where clause'ları"
    )
    
    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
    }
    
    @field_validator("select")
    @classmethod
    def validate_select_fields(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Select field'larını doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("Select liste formatında olmalıdır")
        
        if len(v) == 0:
            raise ValueError("Select listesi boş olamaz")
        
        for i, field in enumerate(v):
            if not isinstance(field, str):
                raise ValueError(f"Select field[{i}] string formatında olmalıdır")
            
            if not field.strip():
                raise ValueError(f"Select field[{i}] boş olamaz")
            
            # Field name validation (basic)
            if not field.replace("_", "").replace(".", "").isalnum():
                raise ValueError(f"Select field[{i}] geçersiz karakter içeriyor")
        
        return v
    
    def to_query_params(self) -> Dict[str, Any]:
        """Query parameters'a çevirir."""
        params = {}
        
        # SearchParams kullan
        if self.search_params:
            params.update(self.search_params.to_query_params())
        else:
            # Manuel parametreler
            if self.offset is not None:
                params["offset"] = self.offset
            if self.max_size is not None:
                params["maxSize"] = self.max_size
            if self.order_by:
                params["orderBy"] = self.order_by
            if self.order:
                params["order"] = self.order
            if self.select:
                params["select"] = ",".join(self.select)
            if self.where:
                params["where"] = self.where
        
        return params


# Factory functions
def create_link_request(
    entity_type: str,
    entity_id: str,
    link: str,
    target_id: Optional[str] = None,
    target_ids: Optional[List[str]] = None,
    mass_relate: bool = False,
    where: Optional[List[Dict[str, Any]]] = None,
    foreign_id: Optional[str] = None
) -> LinkRequest:
    """LinkRequest oluşturur.
    
    Args:
        entity_type: Ana entity türü
        entity_id: Ana entity ID'si
        link: Relationship link adı
        target_id: Tek hedef ID
        target_ids: Çoklu hedef ID'leri
        mass_relate: Mass relate operasyonu
        where: Mass relate için search criteria
        foreign_id: Foreign entity ID
        
    Returns:
        LinkRequest instance'ı
    """
    return LinkRequest(
        entity_type=entity_type,
        entity_id=entity_id,
        link=link,
        id=target_id,
        ids=target_ids,
        massRelate=mass_relate if mass_relate else None,
        where=where,
        foreignId=foreign_id
    )


def create_unlink_request(
    entity_type: str,
    entity_id: str,
    link: str,
    target_id: Optional[str] = None,
    target_ids: Optional[List[str]] = None,
    foreign_id: Optional[str] = None
) -> UnlinkRequest:
    """UnlinkRequest oluşturur.
    
    Args:
        entity_type: Ana entity türü
        entity_id: Ana entity ID'si
        link: Relationship link adı
        target_id: Tek hedef ID
        target_ids: Çoklu hedef ID'leri
        foreign_id: Foreign entity ID
        
    Returns:
        UnlinkRequest instance'ı
    """
    return UnlinkRequest(
        entity_type=entity_type,
        entity_id=entity_id,
        link=link,
        id=target_id,
        ids=target_ids,
        foreignId=foreign_id
    )


def create_relationship_list_request(
    entity_type: str,
    entity_id: str,
    link: str,
    search_params: Optional[SearchParams] = None,
    offset: Optional[int] = None,
    max_size: Optional[int] = None,
    order_by: Optional[str] = None,
    order: Optional[str] = None,
    select: Optional[List[str]] = None,
    where: Optional[List[Dict[str, Any]]] = None
) -> RelationshipListRequest:
    """RelationshipListRequest oluşturur.
    
    Args:
        entity_type: Ana entity türü
        entity_id: Ana entity ID'si
        link: Relationship link adı
        search_params: Arama parametreleri
        offset: Başlangıç offset'i
        max_size: Maksimum kayıt sayısı
        order_by: Sıralama field'ı
        order: Sıralama yönü
        select: Seçilecek field'lar
        where: Where clause'ları
        
    Returns:
        RelationshipListRequest instance'ı
    """
    return RelationshipListRequest(
        entity_type=entity_type,
        entity_id=entity_id,
        link=link,
        search_params=search_params,
        offset=offset,
        maxSize=max_size,
        orderBy=order_by,
        order=order,
        select=select,
        where=where
    )


# Export edilecek sınıflar ve fonksiyonlar
__all__ = [
    # Base classes
    "RelationshipRequest",
    
    # Request classes
    "LinkRequest",
    "UnlinkRequest", 
    "RelationshipListRequest",
    
    # Factory functions
    "create_link_request",
    "create_unlink_request",
    "create_relationship_list_request",
]