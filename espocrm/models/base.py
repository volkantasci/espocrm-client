"""EspoCRM API modelleri için base sınıflar.

Bu modül EspoCRM API modellerinin temel sınıflarını içerir.
Pydantic BaseModel'den türetilmiş ortak davranışları sağlar.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator
from typing_extensions import Self


# Generic type variable for model classes
ModelType = TypeVar("ModelType", bound="EspoCRMBaseModel")


class EspoCRMBaseModel(BaseModel):
    """EspoCRM API modelleri için temel sınıf.
    
    Bu sınıf tüm EspoCRM model sınıflarının base'idir.
    Ortak field'lar, validation kuralları ve utility metodları sağlar.
    
    Attributes:
        id: Kayıt ID'si (EspoCRM'de genellikle UUID formatında)
        name: Kayıt adı (çoğu entity'de mevcut)
        created_at: Oluşturulma tarihi
        modified_at: Son değişiklik tarihi
        created_by_id: Oluşturan kullanıcı ID'si
        modified_by_id: Son değiştiren kullanıcı ID'si
        deleted: Soft delete flag'i
    """
    
    # Temel field'lar - çoğu EspoCRM entity'sinde mevcut
    id: Optional[str] = Field(
        default=None,
        description="Kayıt ID'si",
        max_length=17,  # EspoCRM ID'leri genellikle 17 karakter
    )
    
    name: Optional[str] = Field(
        default=None,
        description="Kayıt adı",
        max_length=255,
    )
    
    created_at: Optional[datetime] = Field(
        default=None,
        description="Oluşturulma tarihi",
        alias="createdAt",
    )
    
    modified_at: Optional[datetime] = Field(
        default=None,
        description="Son değişiklik tarihi",
        alias="modifiedAt",
    )
    
    created_by_id: Optional[str] = Field(
        default=None,
        description="Oluşturan kullanıcı ID'si",
        alias="createdById",
        max_length=17,
    )
    
    modified_by_id: Optional[str] = Field(
        default=None,
        description="Son değiştiren kullanıcı ID'si",
        alias="modifiedById",
        max_length=17,
    )
    
    deleted: Optional[bool] = Field(
        default=None,
        description="Soft delete flag'i",
    )
    
    model_config = {
        "extra": "allow",  # EspoCRM'de custom field'lar olabilir
        "populate_by_name": True,  # Alias'ları destekle
        "validate_assignment": True,
        "str_strip_whitespace": True,
        "use_enum_values": True,
        "arbitrary_types_allowed": True,
    }
    
    @field_validator("id", "created_by_id", "modified_by_id")
    @classmethod
    def validate_espocrm_id(cls, v: Optional[str]) -> Optional[str]:
        """EspoCRM ID formatını doğrular.
        
        EspoCRM ID'leri genellikle 17 karakterlik alphanumeric string'lerdir.
        """
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("ID string formatında olmalıdır")
        
        if len(v) != 17:
            raise ValueError("EspoCRM ID'si 17 karakter uzunluğunda olmalıdır")
        
        if not v.isalnum():
            raise ValueError("EspoCRM ID'si sadece alphanumeric karakterler içermelidir")
        
        return v
    
    @field_serializer("created_at", "modified_at")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Datetime field'larını EspoCRM formatında serialize eder."""
        if value is None:
            return None
        return value.isoformat()
    
    def is_new(self) -> bool:
        """Kaydın yeni olup olmadığını kontrol eder (ID'si yoksa yeni)."""
        return self.id is None
    
    def is_deleted(self) -> bool:
        """Kaydın silinmiş olup olmadığını kontrol eder."""
        return bool(self.deleted)
    
    def get_entity_type(self) -> str:
        """Model'in EspoCRM entity type'ını döndürür.
        
        Default olarak sınıf adını döndürür, alt sınıflar override edebilir.
        """
        return self.__class__.__name__
    
    def get_display_name(self) -> str:
        """Kaydın görüntüleme adını döndürür.
        
        Önce 'name' field'ını, yoksa ID'yi, o da yoksa sınıf adını döndürür.
        """
        if self.name:
            return self.name
        elif self.id:
            return f"{self.get_entity_type()}#{self.id}"
        else:
            return f"New {self.get_entity_type()}"
    
    def to_dict(self, exclude_none: bool = True, by_alias: bool = True) -> Dict[str, Any]:
        """Model'i dictionary'ye çevirir.
        
        Args:
            exclude_none: None değerleri hariç tut
            by_alias: Field alias'larını kullan
            
        Returns:
            Model dictionary'si
        """
        return self.model_dump(
            exclude_none=exclude_none,
            by_alias=by_alias,
        )
    
    def to_json(self, exclude_none: bool = True, by_alias: bool = True) -> str:
        """Model'i JSON string'e çevirir.
        
        Args:
            exclude_none: None değerleri hariç tut
            by_alias: Field alias'larını kullan
            
        Returns:
            JSON string
        """
        return self.model_dump_json(
            exclude_none=exclude_none,
            by_alias=by_alias,
        )
    
    @classmethod
    def from_dict(cls: Type[ModelType], data: Dict[str, Any]) -> ModelType:
        """Dictionary'den model oluşturur.
        
        Args:
            data: Model verisi
            
        Returns:
            Model instance'ı
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls: Type[ModelType], json_str: str) -> ModelType:
        """JSON string'den model oluşturur.
        
        Args:
            json_str: JSON string
            
        Returns:
            Model instance'ı
        """
        return cls.model_validate_json(json_str)
    
    @classmethod
    def from_api_response(cls: Type[ModelType], data: Dict[str, Any]) -> ModelType:
        """EspoCRM API response'undan model oluşturur.
        
        Args:
            data: API response verisi
            
        Returns:
            Model instance'ı
        """
        # EspoCRM API'den gelen veriyi temizle ve dönüştür
        cleaned_data = cls._clean_api_data(data)
        return cls(**cleaned_data)
    
    @classmethod
    def _clean_api_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """API'den gelen veriyi temizler ve dönüştürür.
        
        Args:
            data: Ham API verisi
            
        Returns:
            Temizlenmiş veri
        """
        cleaned = {}
        
        for key, value in data.items():
            # None değerleri atla
            if value is None:
                continue
            
            # Datetime string'lerini parse et
            if key in ("createdAt", "modifiedAt", "created_at", "modified_at"):
                if isinstance(value, str):
                    try:
                        # ISO format datetime parse
                        cleaned[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        continue
                    except ValueError:
                        pass
            
            cleaned[key] = value
        
        return cleaned
    
    def update_from_dict(self, data: Dict[str, Any]) -> Self:
        """Model'i dictionary verisiyle günceller.
        
        Args:
            data: Güncellenecek veri
            
        Returns:
            Güncellenmiş model instance'ı
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
    
    def merge_with(self, other: "EspoCRMBaseModel") -> Self:
        """Başka bir model ile merge eder.
        
        Args:
            other: Merge edilecek model
            
        Returns:
            Merge edilmiş model instance'ı
        """
        if not isinstance(other, self.__class__):
            raise ValueError("Aynı tip modeller merge edilebilir")
        
        other_data = other.to_dict(exclude_none=True)
        return self.update_from_dict(other_data)
    
    def get_changed_fields(self, original: "EspoCRMBaseModel") -> Dict[str, Any]:
        """Orijinal model ile karşılaştırarak değişen field'ları döndürür.
        
        Args:
            original: Orijinal model
            
        Returns:
            Değişen field'lar
        """
        if not isinstance(original, self.__class__):
            raise ValueError("Aynı tip modeller karşılaştırılabilir")
        
        current_data = self.to_dict(exclude_none=False)
        original_data = original.to_dict(exclude_none=False)
        
        changed = {}
        for key, value in current_data.items():
            if key not in original_data or original_data[key] != value:
                changed[key] = value
        
        return changed
    
    def __str__(self) -> str:
        """String representation."""
        return self.get_display_name()
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.name!r})"


class EspoCRMListResponse(BaseModel):
    """EspoCRM API list response'u için model.
    
    EspoCRM API'den dönen liste response'larını temsil eder.
    Pagination bilgilerini ve kayıtları içerir.
    """
    
    total: int = Field(
        description="Toplam kayıt sayısı",
        ge=0,
    )
    
    list: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Kayıt listesi",
    )
    
    offset: Optional[int] = Field(
        default=None,
        description="Offset değeri",
        ge=0,
    )
    
    max_size: Optional[int] = Field(
        default=None,
        description="Maksimum sayfa boyutu",
        alias="maxSize",
        ge=1,
    )
    
    def get_records(self, model_class: Type[ModelType]) -> List[ModelType]:
        """Kayıtları belirtilen model sınıfına dönüştürür.
        
        Args:
            model_class: Dönüştürülecek model sınıfı
            
        Returns:
            Model instance'ları listesi
        """
        return [model_class.from_api_response(record) for record in self.list]
    
    def is_empty(self) -> bool:
        """Liste boş mu kontrol eder."""
        return self.total == 0 or len(self.list) == 0
    
    def has_more(self) -> bool:
        """Daha fazla kayıt var mı kontrol eder."""
        if self.offset is None:
            return False
        return (self.offset + len(self.list)) < self.total


# Export edilecek sınıflar
__all__ = [
    "EspoCRMBaseModel",
    "EspoCRMListResponse",
    "ModelType",
]