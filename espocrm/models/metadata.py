"""EspoCRM Metadata modelleri.

Bu modül EspoCRM API'nin metadata sistemini temsil eden Pydantic modellerini içerir.
Application metadata, entity definitions, field definitions ve relationship definitions sağlar.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Type, TypeVar
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

from .base import EspoCRMBaseModel


# Type variables
MetadataT = TypeVar("MetadataT", bound="BaseMetadata")


class FieldType(str, Enum):
    """EspoCRM field türleri."""
    
    # Basic types
    VARCHAR = "varchar"
    TEXT = "text"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    DATE = "date"
    DATETIME = "datetime"
    
    # Special types
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    CURRENCY = "currency"
    ENUM = "enum"
    MULTI_ENUM = "multiEnum"
    
    # Relationship types
    LINK = "link"
    LINK_MULTIPLE = "linkMultiple"
    LINK_PARENT = "linkParent"
    
    # File types
    FILE = "file"
    IMAGE = "image"
    ATTACHMENT_MULTIPLE = "attachmentMultiple"
    
    # Complex types
    JSON_ARRAY = "jsonArray"
    JSON_OBJECT = "jsonObject"
    ARRAY = "array"
    
    # System types
    ID = "id"
    FOREIGN = "foreign"
    FOREIGN_ID = "foreignId"
    FOREIGN_TYPE = "foreignType"


class RelationshipType(str, Enum):
    """EspoCRM ilişki türleri."""
    
    ONE_TO_MANY = "oneToMany"
    MANY_TO_ONE = "manyToOne"
    MANY_TO_MANY = "manyToMany"
    ONE_TO_ONE_RIGHT = "oneToOneRight"
    ONE_TO_ONE_LEFT = "oneToOneLeft"
    BELONGS_TO = "belongsTo"
    HAS_ONE = "hasOne"
    HAS_MANY = "hasMany"
    HAS_CHILDREN = "hasChildren"
    BELONGS_TO_PARENT = "belongsToParent"


class BaseMetadata(BaseModel):
    """Metadata için temel sınıf."""
    
    model_config = {
        "extra": "allow",
        "populate_by_name": True,
        "validate_assignment": True,
        "use_enum_values": True,
    }


class FieldMetadata(BaseMetadata):
    """EspoCRM field metadata modeli."""
    
    type: FieldType = Field(
        description="Field türü"
    )
    
    required: Optional[bool] = Field(
        default=None,
        description="Zorunlu field mi"
    )
    
    max_length: Optional[int] = Field(
        default=None,
        description="Maksimum uzunluk",
        alias="maxLength"
    )
    
    min: Optional[Union[int, float]] = Field(
        default=None,
        description="Minimum değer"
    )
    
    max: Optional[Union[int, float]] = Field(
        default=None,
        description="Maksimum değer"
    )
    
    default: Optional[Any] = Field(
        default=None,
        description="Varsayılan değer"
    )
    
    options: Optional[List[str]] = Field(
        default=None,
        description="Enum seçenekleri"
    )
    
    options_reference: Optional[str] = Field(
        default=None,
        description="Options referansı",
        alias="optionsReference"
    )
    
    entity: Optional[str] = Field(
        default=None,
        description="İlişkili entity türü"
    )
    
    foreign: Optional[str] = Field(
        default=None,
        description="Foreign field adı"
    )
    
    link: Optional[str] = Field(
        default=None,
        description="Link field adı"
    )
    
    view: Optional[str] = Field(
        default=None,
        description="View sınıfı"
    )
    
    not_null: Optional[bool] = Field(
        default=None,
        description="NULL değer alabilir mi",
        alias="notNull"
    )
    
    unique: Optional[bool] = Field(
        default=None,
        description="Unique constraint var mı"
    )
    
    index: Optional[bool] = Field(
        default=None,
        description="Index var mı"
    )
    
    audited: Optional[bool] = Field(
        default=None,
        description="Audit edilir mi"
    )
    
    read_only: Optional[bool] = Field(
        default=None,
        description="Salt okunur mu",
        alias="readOnly"
    )
    
    tooltip: Optional[str] = Field(
        default=None,
        description="Tooltip metni"
    )
    
    translation: Optional[str] = Field(
        default=None,
        description="Çeviri anahtarı"
    )
    
    def is_required(self) -> bool:
        """Field zorunlu mu kontrol eder."""
        return bool(self.required)
    
    def is_relationship_field(self) -> bool:
        """İlişki field'ı mı kontrol eder."""
        return self.type in [
            FieldType.LINK,
            FieldType.LINK_MULTIPLE,
            FieldType.LINK_PARENT,
            FieldType.FOREIGN,
            FieldType.FOREIGN_ID,
            FieldType.FOREIGN_TYPE
        ]
    
    def is_enum_field(self) -> bool:
        """Enum field'ı mı kontrol eder."""
        return self.type in [FieldType.ENUM, FieldType.MULTI_ENUM]
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Field validation kurallarını döndürür."""
        rules = {}
        
        if self.required:
            rules["required"] = True
        
        if self.max_length:
            rules["max_length"] = self.max_length
        
        if self.min is not None:
            rules["min"] = self.min
        
        if self.max is not None:
            rules["max"] = self.max
        
        if self.options:
            rules["choices"] = self.options
        
        return rules


class RelationshipMetadata(BaseMetadata):
    """EspoCRM relationship metadata modeli."""
    
    type: RelationshipType = Field(
        description="İlişki türü"
    )
    
    entity: str = Field(
        description="İlişkili entity türü"
    )
    
    foreign: Optional[str] = Field(
        default=None,
        description="Foreign field adı"
    )
    
    foreign_key: Optional[str] = Field(
        default=None,
        description="Foreign key field adı",
        alias="foreignKey"
    )
    
    mid_keys: Optional[List[str]] = Field(
        default=None,
        description="Many-to-many ara tablo key'leri",
        alias="midKeys"
    )
    
    relationship_name: Optional[str] = Field(
        default=None,
        description="İlişki tablosu adı",
        alias="relationshipName"
    )
    
    conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="İlişki koşulları"
    )
    
    audited: Optional[bool] = Field(
        default=None,
        description="Audit edilir mi"
    )
    
    def is_many_to_many(self) -> bool:
        """Many-to-many ilişkisi mi kontrol eder."""
        return self.type == RelationshipType.MANY_TO_MANY
    
    def is_one_to_many(self) -> bool:
        """One-to-many ilişkisi mi kontrol eder."""
        return self.type == RelationshipType.ONE_TO_MANY
    
    def is_many_to_one(self) -> bool:
        """Many-to-one ilişkisi mi kontrol eder."""
        return self.type == RelationshipType.MANY_TO_ONE


class EntityMetadata(BaseMetadata):
    """EspoCRM entity metadata modeli."""
    
    fields: Dict[str, FieldMetadata] = Field(
        default_factory=dict,
        description="Entity field'ları"
    )
    
    links: Dict[str, RelationshipMetadata] = Field(
        default_factory=dict,
        description="Entity ilişkileri"
    )
    
    collection: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Collection ayarları"
    )
    
    indexes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Database index'leri"
    )
    
    attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Entity attribute'ları"
    )
    
    @model_validator(mode='after')
    def validate_fields_and_links(self):
        """Field'ları ve link'leri doğrular."""
        # Field'ları FieldMetadata instance'larına çevir
        if isinstance(self.fields, dict):
            for field_name, field_data in self.fields.items():
                if not isinstance(field_data, FieldMetadata):
                    if isinstance(field_data, dict):
                        self.fields[field_name] = FieldMetadata(**field_data)
        
        # Link'leri RelationshipMetadata instance'larına çevir
        if isinstance(self.links, dict):
            for link_name, link_data in self.links.items():
                if not isinstance(link_data, RelationshipMetadata):
                    if isinstance(link_data, dict):
                        self.links[link_name] = RelationshipMetadata(**link_data)
        
        return self
    
    def get_field(self, field_name: str) -> Optional[FieldMetadata]:
        """Belirtilen field'ı döndürür."""
        return self.fields.get(field_name)
    
    def get_link(self, link_name: str) -> Optional[RelationshipMetadata]:
        """Belirtilen link'i döndürür."""
        return self.links.get(link_name)
    
    def get_required_fields(self) -> List[str]:
        """Zorunlu field'ları döndürür."""
        return [
            field_name 
            for field_name, field_meta in self.fields.items() 
            if field_meta.is_required()
        ]
    
    def get_relationship_fields(self) -> Dict[str, FieldMetadata]:
        """İlişki field'larını döndürür."""
        return {
            field_name: field_meta
            for field_name, field_meta in self.fields.items()
            if field_meta.is_relationship_field()
        }
    
    def get_enum_fields(self) -> Dict[str, FieldMetadata]:
        """Enum field'larını döndürür."""
        return {
            field_name: field_meta
            for field_name, field_meta in self.fields.items()
            if field_meta.is_enum_field()
        }
    
    def has_field(self, field_name: str) -> bool:
        """Field var mı kontrol eder."""
        return field_name in self.fields
    
    def has_link(self, link_name: str) -> bool:
        """Link var mı kontrol eder."""
        return link_name in self.links


class ApplicationMetadata(BaseMetadata):
    """EspoCRM application metadata modeli."""
    
    entity_defs: Dict[str, EntityMetadata] = Field(
        default_factory=dict,
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
        description="Global field tanımları"
    )
    
    app: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Uygulama konfigürasyonu"
    )
    
    language: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dil tanımları"
    )
    
    themes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Tema tanımları"
    )
    
    @model_validator(mode='after')
    def validate_entity_defs(self):
        """Entity definitions'ları doğrular."""
        if isinstance(self.entity_defs, dict):
            for entity_name, entity_data in self.entity_defs.items():
                if not isinstance(entity_data, EntityMetadata):
                    if isinstance(entity_data, dict):
                        self.entity_defs[entity_name] = EntityMetadata(**entity_data)
        
        return self
    
    def get_entity_metadata(self, entity_type: str) -> Optional[EntityMetadata]:
        """Belirtilen entity'nin metadata'sını döndürür."""
        return self.entity_defs.get(entity_type)
    
    def get_entity_types(self) -> List[str]:
        """Mevcut entity türlerini döndürür."""
        return list(self.entity_defs.keys())
    
    def has_entity(self, entity_type: str) -> bool:
        """Entity var mı kontrol eder."""
        return entity_type in self.entity_defs
    
    def get_entity_field(self, entity_type: str, field_name: str) -> Optional[FieldMetadata]:
        """Belirtilen entity'nin field'ını döndürür."""
        entity_meta = self.get_entity_metadata(entity_type)
        if entity_meta:
            return entity_meta.get_field(field_name)
        return None
    
    def get_entity_link(self, entity_type: str, link_name: str) -> Optional[RelationshipMetadata]:
        """Belirtilen entity'nin link'ini döndürür."""
        entity_meta = self.get_entity_metadata(entity_type)
        if entity_meta:
            return entity_meta.get_link(link_name)
        return None
    
    def validate_entity_data(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Entity verilerini doğrular ve hataları döndürür."""
        errors = {}
        entity_meta = self.get_entity_metadata(entity_type)
        
        if not entity_meta:
            errors["entity"] = [f"Entity türü '{entity_type}' bulunamadı"]
            return errors
        
        # Required field kontrolü
        required_fields = entity_meta.get_required_fields()
        for field_name in required_fields:
            if field_name not in data or data[field_name] is None:
                if "required" not in errors:
                    errors["required"] = []
                errors["required"].append(f"'{field_name}' field'ı zorunludur")
        
        # Field validation
        for field_name, value in data.items():
            field_meta = entity_meta.get_field(field_name)
            if field_meta:
                field_errors = self._validate_field_value(field_meta, value)
                if field_errors:
                    errors[field_name] = field_errors
        
        return errors
    
    def _validate_field_value(self, field_meta: FieldMetadata, value: Any) -> List[str]:
        """Field değerini doğrular."""
        errors = []
        
        if value is None:
            if field_meta.is_required():
                errors.append("Bu field zorunludur")
            return errors
        
        # String length kontrolü
        if field_meta.max_length and isinstance(value, str):
            if len(value) > field_meta.max_length:
                errors.append(f"Maksimum {field_meta.max_length} karakter olmalıdır")
        
        # Numeric range kontrolü
        if isinstance(value, (int, float)):
            if field_meta.min is not None and value < field_meta.min:
                errors.append(f"Minimum değer {field_meta.min} olmalıdır")
            if field_meta.max is not None and value > field_meta.max:
                errors.append(f"Maksimum değer {field_meta.max} olmalıdır")
        
        # Enum kontrolü
        if field_meta.is_enum_field() and field_meta.options:
            if field_meta.type == FieldType.ENUM:
                if value not in field_meta.options:
                    errors.append(f"Geçerli değerler: {', '.join(field_meta.options)}")
            elif field_meta.type == FieldType.MULTI_ENUM:
                if isinstance(value, list):
                    invalid_values = [v for v in value if v not in field_meta.options]
                    if invalid_values:
                        errors.append(f"Geçersiz değerler: {', '.join(invalid_values)}")
        
        return errors


class MetadataRequest(BaseModel):
    """Metadata request modeli."""
    
    key: Optional[str] = Field(
        default=None,
        description="Specific metadata path (örn: 'entityDefs.Lead.fields.status.options')"
    )
    
    entity_type: Optional[str] = Field(
        default=None,
        description="Belirli entity türü için metadata",
        alias="entityType"
    )
    
    include_client_defs: bool = Field(
        default=True,
        description="Client definitions dahil edilsin mi",
        alias="includeClientDefs"
    )
    
    include_scopes: bool = Field(
        default=True,
        description="Scopes dahil edilsin mi",
        alias="includeScopes"
    )
    
    include_fields: bool = Field(
        default=True,
        description="Global fields dahil edilsin mi",
        alias="includeFields"
    )
    
    model_config = {
        "populate_by_name": True,
    }
    
    def to_query_params(self) -> Dict[str, Any]:
        """Query parameters'a çevirir."""
        params = {}
        
        if self.key:
            params["key"] = self.key
        
        if self.entity_type:
            params["entityType"] = self.entity_type
        
        if not self.include_client_defs:
            params["includeClientDefs"] = "false"
        
        if not self.include_scopes:
            params["includeScopes"] = "false"
        
        if not self.include_fields:
            params["includeFields"] = "false"
        
        return params


# Export edilecek sınıflar
__all__ = [
    # Enums
    "FieldType",
    "RelationshipType",
    
    # Base classes
    "BaseMetadata",
    "MetadataT",
    
    # Metadata models
    "FieldMetadata",
    "RelationshipMetadata",
    "EntityMetadata",
    "ApplicationMetadata",
    "MetadataRequest",
]