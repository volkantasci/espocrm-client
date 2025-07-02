"""EspoCRM API response modelleri.

Bu modül EspoCRM API'den dönen response'lar için Pydantic modellerini içerir.
List response, entity response, error response ve API response parsing sağlar.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Generic
from pydantic import BaseModel, Field, field_validator, model_validator

from .base import EspoCRMBaseModel
from .entities import EntityRecord, create_entity


# Generic type variables
T = TypeVar("T", bound=BaseModel)
EntityT = TypeVar("EntityT", bound=EntityRecord)


class APIResponse(BaseModel, Generic[T]):
    """Genel API response wrapper'ı."""
    
    success: bool = Field(
        default=True,
        description="İşlem başarılı mı"
    )
    
    data: Optional[T] = Field(
        default=None,
        description="Response verisi"
    )
    
    message: Optional[str] = Field(
        default=None,
        description="Response mesajı"
    )
    
    errors: Optional[List[str]] = Field(
        default=None,
        description="Hata mesajları"
    )
    
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Meta bilgiler"
    )
    
    model_config = {
        "extra": "allow",
    }


class ErrorDetail(BaseModel):
    """Hata detayı modeli."""
    
    field: Optional[str] = Field(
        default=None,
        description="Hata ile ilgili field"
    )
    
    message: str = Field(
        description="Hata mesajı"
    )
    
    code: Optional[str] = Field(
        default=None,
        description="Hata kodu"
    )
    
    type: Optional[str] = Field(
        default=None,
        description="Hata türü"
    )


class ErrorResponse(BaseModel):
    """EspoCRM API hata response'u modeli."""
    
    success: bool = Field(
        default=False,
        description="İşlem başarısız"
    )
    
    message: str = Field(
        description="Ana hata mesajı"
    )
    
    errors: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Detaylı hata listesi"
    )
    
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status kodu",
        alias="statusCode"
    )
    
    error_code: Optional[str] = Field(
        default=None,
        description="EspoCRM hata kodu",
        alias="errorCode"
    )
    
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Hata zamanı"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID'si",
        alias="requestId"
    )
    
    model_config = {
        "populate_by_name": True,
    }
    
    def get_error_messages(self) -> List[str]:
        """Tüm hata mesajlarını döndürür."""
        messages = [self.message]
        
        if self.errors:
            for error in self.errors:
                messages.append(error.message)
        
        return messages
    
    def get_field_errors(self) -> Dict[str, List[str]]:
        """Field bazında hata mesajlarını döndürür."""
        field_errors = {}
        
        if self.errors:
            for error in self.errors:
                if error.field:
                    if error.field not in field_errors:
                        field_errors[error.field] = []
                    field_errors[error.field].append(error.message)
        
        return field_errors
    
    def has_field_error(self, field: str) -> bool:
        """Belirtilen field için hata var mı kontrol eder."""
        return field in self.get_field_errors()


class EntityResponse(BaseModel):
    """Tek entity response'u modeli."""
    
    success: bool = Field(
        default=True,
        description="İşlem başarılı mı"
    )
    
    entity_type: Optional[str] = Field(
        default=None,
        description="Entity türü",
        alias="entityType"
    )
    
    data: Dict[str, Any] = Field(
        description="Entity verisi"
    )
    
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Meta bilgiler"
    )
    
    model_config = {
        "populate_by_name": True,
    }
    
    def get_entity(self, entity_class: Optional[Type[EntityT]] = None) -> EntityT:
        """Entity instance'ını döndürür.
        
        Args:
            entity_class: Kullanılacak entity sınıfı (opsiyonel)
            
        Returns:
            Entity instance'ı
        """
        if entity_class:
            return entity_class.create_from_dict(self.data, self.entity_type)
        elif self.entity_type:
            return create_entity(self.entity_type, self.data)
        else:
            return EntityRecord.create_from_dict(self.data)
    
    def get_id(self) -> Optional[str]:
        """Entity ID'sini döndürür."""
        return self.data.get("id")
    
    def get_name(self) -> Optional[str]:
        """Entity adını döndürür."""
        return self.data.get("name")


class ListMeta(BaseModel):
    """Liste meta bilgileri modeli."""
    
    total: int = Field(
        description="Toplam kayıt sayısı",
        ge=0
    )
    
    offset: int = Field(
        default=0,
        description="Başlangıç offset'i",
        ge=0
    )
    
    max_size: int = Field(
        description="Maksimum sayfa boyutu",
        alias="maxSize",
        ge=1
    )
    
    count: int = Field(
        description="Dönen kayıt sayısı",
        ge=0
    )
    
    has_more: bool = Field(
        default=False,
        description="Daha fazla kayıt var mı",
        alias="hasMore"
    )
    
    page: Optional[int] = Field(
        default=None,
        description="Sayfa numarası",
        ge=1
    )
    
    total_pages: Optional[int] = Field(
        default=None,
        description="Toplam sayfa sayısı",
        alias="totalPages",
        ge=1
    )
    
    model_config = {
        "populate_by_name": True,
    }
    
    @model_validator(mode='after')
    def validate_meta(self):
        """Meta bilgilerini doğrular."""
        # has_more hesapla
        if self.offset + self.count < self.total:
            self.has_more = True
        else:
            self.has_more = False
        
        # Sayfa bilgilerini hesapla
        if self.max_size > 0:
            self.page = (self.offset // self.max_size) + 1
            self.total_pages = (self.total + self.max_size - 1) // self.max_size
        
        return self
    
    def get_next_offset(self) -> Optional[int]:
        """Sonraki sayfa offset'ini döndürür."""
        if self.has_more:
            return self.offset + self.max_size
        return None
    
    def get_prev_offset(self) -> Optional[int]:
        """Önceki sayfa offset'ini döndürür."""
        if self.offset > 0:
            return max(0, self.offset - self.max_size)
        return None


class ListResponse(BaseModel, Generic[EntityT]):
    """Liste response'u modeli."""
    
    success: bool = Field(
        default=True,
        description="İşlem başarılı mı"
    )
    
    entity_type: Optional[str] = Field(
        default=None,
        description="Entity türü",
        alias="entityType"
    )
    
    list: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Entity listesi"
    )
    
    total: int = Field(
        description="Toplam kayıt sayısı",
        ge=0
    )
    
    offset: Optional[int] = Field(
        default=None,
        description="Başlangıç offset'i",
        ge=0
    )
    
    max_size: Optional[int] = Field(
        default=None,
        description="Maksimum sayfa boyutu",
        alias="maxSize",
        ge=1
    )
    
    meta: Optional[ListMeta] = Field(
        default=None,
        description="Liste meta bilgileri"
    )
    
    model_config = {
        "populate_by_name": True,
    }
    
    @model_validator(mode='after')
    def create_meta(self):
        """Meta bilgilerini oluşturur."""
        if not self.meta:
            self.meta = ListMeta(
                total=self.total,
                offset=self.offset or 0,
                max_size=self.max_size or len(self.list),
                count=len(self.list)
            )
        
        return self
    
    def get_entities(self, entity_class: Optional[Type[EntityT]] = None) -> List[EntityT]:
        """Entity instance'larını döndürür.
        
        Args:
            entity_class: Kullanılacak entity sınıfı (opsiyonel)
            
        Returns:
            Entity instance'ları listesi
        """
        entities = []
        
        for item_data in self.list:
            if entity_class:
                entity = entity_class.create_from_dict(item_data, self.entity_type)
            elif self.entity_type:
                entity = create_entity(self.entity_type, item_data)
            else:
                entity = EntityRecord.create_from_dict(item_data)
            
            entities.append(entity)
        
        return entities
    
    def get_ids(self) -> List[str]:
        """Entity ID'lerini döndürür."""
        return [item.get("id") for item in self.list if item.get("id")]
    
    def get_names(self) -> List[str]:
        """Entity adlarını döndürür."""
        return [item.get("name") for item in self.list if item.get("name")]
    
    def is_empty(self) -> bool:
        """Liste boş mu kontrol eder."""
        return len(self.list) == 0
    
    def has_more(self) -> bool:
        """Daha fazla kayıt var mı kontrol eder."""
        return self.meta.has_more if self.meta else False
    
    def get_page_info(self) -> Dict[str, Any]:
        """Sayfa bilgilerini döndürür."""
        if not self.meta:
            return {}
        
        return {
            "current_page": self.meta.page,
            "total_pages": self.meta.total_pages,
            "has_next": self.meta.has_more,
            "has_prev": self.meta.offset > 0,
            "next_offset": self.meta.get_next_offset(),
            "prev_offset": self.meta.get_prev_offset(),
        }


class BulkOperationResult(BaseModel):
    """Bulk operasyon sonucu modeli."""
    
    success: bool = Field(
        description="Genel başarı durumu"
    )
    
    total: int = Field(
        description="Toplam işlem sayısı",
        ge=0
    )
    
    successful: int = Field(
        description="Başarılı işlem sayısı",
        ge=0
    )
    
    failed: int = Field(
        description="Başarısız işlem sayısı",
        ge=0
    )
    
    results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detaylı sonuçlar"
    )
    
    errors: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Hata detayları"
    )
    
    @model_validator(mode='after')
    def validate_counts(self):
        """Sayıları doğrular."""
        if self.successful + self.failed != self.total:
            raise ValueError("Başarılı + başarısız işlem sayısı toplam ile eşleşmiyor")
        
        return self
    
    def get_success_rate(self) -> float:
        """Başarı oranını döndürür."""
        if self.total == 0:
            return 0.0
        
        return (self.successful / self.total) * 100.0
    
    def get_successful_ids(self) -> List[str]:
        """Başarılı işlemlerin ID'lerini döndürür."""
        return [
            result.get("id") 
            for result in self.results 
            if result.get("success") and result.get("id")
        ]
    
    def get_failed_results(self) -> List[Dict[str, Any]]:
        """Başarısız işlemleri döndürür."""
        return [
            result 
            for result in self.results 
            if not result.get("success", True)
        ]


class StreamResponse(BaseModel):
    """Stream response modeli."""
    
    success: bool = Field(
        default=True,
        description="İşlem başarılı mı"
    )
    
    list: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Stream kayıtları"
    )
    
    total: int = Field(
        description="Toplam kayıt sayısı",
        ge=0
    )
    
    offset: Optional[int] = Field(
        default=None,
        description="Başlangıç offset'i",
        ge=0
    )
    
    max_size: Optional[int] = Field(
        default=None,
        description="Maksimum sayfa boyutu",
        alias="maxSize",
        ge=1
    )
    
    model_config = {
        "populate_by_name": True,
    }


class MetadataResponse(BaseModel):
    """Metadata response modeli."""
    
    success: bool = Field(
        default=True,
        description="İşlem başarılı mı"
    )
    
    entity_defs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Entity tanımları",
        alias="entityDefs"
    )
    
    client_defs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Client tanımları",
        alias="clientDefs"
    )
    
    scopes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Scope tanımları"
    )
    
    fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Field tanımları"
    )
    
    model_config = {
        "populate_by_name": True,
    }


# Response parsing functions
def parse_entity_response(data: Dict[str, Any], entity_type: Optional[str] = None) -> EntityResponse:
    """Entity response'unu parse eder.
    
    Args:
        data: Ham response verisi
        entity_type: Entity türü
        
    Returns:
        Parse edilmiş EntityResponse
    """
    # EspoCRM bazen direkt entity verisini döndürür
    if "success" not in data and "id" in data:
        return EntityResponse(
            success=True,
            entity_type=entity_type,
            data=data
        )
    
    return EntityResponse(**data, entity_type=entity_type)


def parse_list_response(data: Dict[str, Any], entity_type: Optional[str] = None) -> ListResponse:
    """Liste response'unu parse eder.
    
    Args:
        data: Ham response verisi
        entity_type: Entity türü
        
    Returns:
        Parse edilmiş ListResponse
    """
    # EspoCRM liste formatını normalize et
    if "list" not in data and isinstance(data, list):
        return ListResponse(
            success=True,
            entity_type=entity_type,
            list=data,
            total=len(data)
        )
    
    return ListResponse(**data, entity_type=entity_type)


def parse_error_response(data: Dict[str, Any], status_code: Optional[int] = None) -> ErrorResponse:
    """Hata response'unu parse eder.
    
    Args:
        data: Ham response verisi
        status_code: HTTP status kodu
        
    Returns:
        Parse edilmiş ErrorResponse
    """
    # Basit hata mesajı formatını normalize et
    if isinstance(data, str):
        return ErrorResponse(
            message=data,
            status_code=status_code
        )
    
    # Message field'ı yoksa error field'ından al
    if "message" not in data and "error" in data:
        data["message"] = data["error"]
    
    return ErrorResponse(**data, status_code=status_code)


# Export edilecek sınıflar ve fonksiyonlar
__all__ = [
    # Generic types
    "APIResponse",
    "T",
    "EntityT",
    
    # Response models
    "ErrorDetail",
    "ErrorResponse",
    "EntityResponse",
    "ListMeta",
    "ListResponse",
    "BulkOperationResult",
    "StreamResponse",
    "MetadataResponse",
    
    # Parsing functions
    "parse_entity_response",
    "parse_list_response",
    "parse_error_response",
]