"""EspoCRM API arama parametreleri için modeller.

Bu modül EspoCRM API'nin arama ve filtreleme özelliklerini destekleyen
Pydantic modellerini içerir. EspoCRM dokümantasyonundaki tüm search
operatörlerini ve parametrelerini destekler.
"""

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

from .base import EspoCRMBaseModel


class OrderDirection(str, Enum):
    """Sıralama yönü enum'ı."""
    ASC = "asc"
    DESC = "desc"


class WhereOperator(str, Enum):
    """EspoCRM where operatörleri."""
    # Temel karşılaştırma operatörleri
    EQUALS = "equals"
    NOT_EQUALS = "notEquals"
    GREATER_THAN = "greaterThan"
    LESS_THAN = "lessThan"
    GREATER_THAN_OR_EQUAL = "greaterThanOrEqual"
    LESS_THAN_OR_EQUAL = "lessThanOrEqual"
    
    # Null kontrolleri
    IS_NULL = "isNull"
    IS_NOT_NULL = "isNotNull"
    
    # Liste operatörleri
    IN = "in"
    NOT_IN = "notIn"
    
    # String operatörleri
    CONTAINS = "contains"
    NOT_CONTAINS = "notContains"
    STARTS_WITH = "startsWith"
    ENDS_WITH = "endsWith"
    LIKE = "like"
    NOT_LIKE = "notLike"
    
    # Tarih operatörleri
    TODAY = "today"
    PAST = "past"
    FUTURE = "future"
    LAST_SEVEN_DAYS = "lastSevenDays"
    EVER = "ever"
    IS_EMPTY = "isEmpty"
    IS_NOT_EMPTY = "isNotEmpty"
    
    # Aralık operatörleri
    BETWEEN = "between"
    
    # Mantıksal operatörler
    OR = "or"
    AND = "and"
    NOT = "not"
    
    # Özel operatörler
    ARRAY_ANY_OF = "arrayAnyOf"
    ARRAY_NONE_OF = "arrayNoneOf"
    ARRAY_IS_EMPTY = "arrayIsEmpty"
    ARRAY_IS_NOT_EMPTY = "arrayIsNotEmpty"


class WhereClause(BaseModel):
    """EspoCRM where clause base sınıfı."""
    
    type: WhereOperator = Field(description="Where operatörü")
    attribute: Optional[str] = Field(default=None, description="Field adı")
    value: Optional[Any] = Field(default=None, description="Karşılaştırma değeri")
    
    model_config = {
        "extra": "allow",
        "use_enum_values": True,
    }
    
    @model_validator(mode='after')
    def validate_clause(self):
        """Where clause'u doğrular."""
        # Mantıksal operatörler için özel validasyon
        if self.type in (WhereOperator.OR, WhereOperator.AND):
            if not hasattr(self, 'value') or not isinstance(self.value, list):
                raise ValueError(f"{self.type} operatörü için value bir liste olmalıdır")
        
        # Null kontrolleri için value gerekmez
        elif self.type in (WhereOperator.IS_NULL, WhereOperator.IS_NOT_NULL):
            if not self.attribute:
                raise ValueError(f"{self.type} operatörü için attribute gereklidir")
        
        # Diğer operatörler için hem attribute hem value gerekir
        elif self.type not in (WhereOperator.TODAY, WhereOperator.PAST, WhereOperator.FUTURE):
            if not self.attribute:
                raise ValueError(f"{self.type} operatörü için attribute gereklidir")
        
        return self


# Specific clause types removed to avoid Pydantic inheritance issues
# Use WhereClause directly with appropriate type, attribute, and value


class OrderBy(BaseModel):
    """Sıralama parametresi modeli."""
    
    field: str = Field(description="Sıralanacak field adı")
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description="Sıralama yönü"
    )
    
    def to_dict(self) -> Dict[str, str]:
        """Dictionary formatına çevirir."""
        return {
            "field": self.field,
            "direction": self.direction.value
        }


class Pagination(BaseModel):
    """Sayfalama parametreleri modeli."""
    
    offset: int = Field(
        default=0,
        description="Başlangıç offset'i",
        ge=0
    )
    max_size: int = Field(
        default=20,
        description="Maksimum kayıt sayısı",
        alias="maxSize",
        ge=1,
        le=200  # EspoCRM genellikle 200 ile sınırlar
    )
    
    def to_dict(self) -> Dict[str, int]:
        """Dictionary formatına çevirir."""
        return {
            "offset": self.offset,
            "maxSize": self.max_size
        }


class Select(BaseModel):
    """Seçilecek field'lar modeli."""
    
    fields: List[str] = Field(
        default_factory=list,
        description="Seçilecek field'lar listesi"
    )
    
    @field_validator('fields')
    @classmethod
    def validate_fields(cls, v):
        """Field'ların boş olmadığını doğrular."""
        if not v:
            return v
        
        for field in v:
            if not isinstance(field, str) or not field.strip():
                raise ValueError("Tüm field'lar boş olmayan string olmalıdır")
        
        return [field.strip() for field in v]
    
    def to_string(self) -> str:
        """Comma-separated string formatına çevirir."""
        return ",".join(self.fields)


class SearchParams(BaseModel):
    """EspoCRM API arama parametreleri ana modeli."""
    
    where: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Where clause'ları"
    )
    
    order_by: Optional[str] = Field(
        default=None,
        description="Sıralama field'ı",
        alias="orderBy"
    )
    
    order: OrderDirection = Field(
        default=OrderDirection.ASC,
        description="Sıralama yönü"
    )
    
    offset: int = Field(
        default=0,
        description="Başlangıç offset'i",
        ge=0
    )
    
    max_size: int = Field(
        default=20,
        description="Maksimum kayıt sayısı",
        alias="maxSize",
        ge=1,
        le=200
    )
    
    select: Optional[List[str]] = Field(
        default=None,
        description="Seçilecek field'lar"
    )
    
    model_config = {
        "populate_by_name": True,
        "use_enum_values": True,
    }
    
    def add_where_clause(self, clause: WhereClause) -> "SearchParams":
        """Where clause ekler."""
        if self.where is None:
            self.where = []
        
        self.where.append(clause.model_dump(exclude_none=True, by_alias=True))
        return self
    
    def add_equals(self, field: str, value: Union[str, int, float, bool]) -> "SearchParams":
        """Eşitlik kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.EQUALS, attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_not_equals(self, field: str, value: Union[str, int, float, bool]) -> "SearchParams":
        """Eşitsizlik kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.NOT_EQUALS, attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_greater_than(self, field: str, value: Union[str, int, float, datetime, date]) -> "SearchParams":
        """Büyüktür kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.GREATER_THAN, attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_less_than(self, field: str, value: Union[str, int, float, datetime, date]) -> "SearchParams":
        """Küçüktür kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.LESS_THAN, attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_in(self, field: str, values: List[Union[str, int, float]]) -> "SearchParams":
        """Liste içinde kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.IN, attribute=field, value=values)
        return self.add_where_clause(clause)
    
    def add_not_in(self, field: str, values: List[Union[str, int, float]]) -> "SearchParams":
        """Liste dışında kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.NOT_IN, attribute=field, value=values)
        return self.add_where_clause(clause)
    
    def add_contains(self, field: str, value: str) -> "SearchParams":
        """İçerir kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.CONTAINS, attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_starts_with(self, field: str, value: str) -> "SearchParams":
        """Başlar kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.STARTS_WITH, attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_ends_with(self, field: str, value: str) -> "SearchParams":
        """Biter kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.ENDS_WITH, attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_is_null(self, field: str) -> "SearchParams":
        """Null kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.IS_NULL, attribute=field)
        return self.add_where_clause(clause)
    
    def add_is_not_null(self, field: str) -> "SearchParams":
        """Not null kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.IS_NOT_NULL, attribute=field)
        return self.add_where_clause(clause)
    
    def add_between(self, field: str, start: Union[str, int, float, datetime, date],
                   end: Union[str, int, float, datetime, date]) -> "SearchParams":
        """Aralık kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.BETWEEN, attribute=field, value=[start, end])
        return self.add_where_clause(clause)
    
    def add_today(self, field: str) -> "SearchParams":
        """Bugün kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.TODAY, attribute=field)
        return self.add_where_clause(clause)
    
    def add_past(self, field: str) -> "SearchParams":
        """Geçmiş kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.PAST, attribute=field)
        return self.add_where_clause(clause)
    
    def add_future(self, field: str) -> "SearchParams":
        """Gelecek kontrolü ekler."""
        clause = WhereClause(type=WhereOperator.FUTURE, attribute=field)
        return self.add_where_clause(clause)
    
    def set_order(self, field: str, direction: OrderDirection = OrderDirection.ASC) -> "SearchParams":
        """Sıralama ayarlar."""
        self.order_by = field
        self.order = direction
        return self
    
    def set_pagination(self, offset: int = 0, max_size: int = 20) -> "SearchParams":
        """Sayfalama ayarlar."""
        self.offset = offset
        self.max_size = max_size
        return self
    
    def set_select(self, fields: List[str]) -> "SearchParams":
        """Seçilecek field'ları ayarlar."""
        self.select = fields
        return self
    
    def to_query_params(self) -> Dict[str, Any]:
        """Query parametrelerine çevirir."""
        params = {}
        
        # Pagination
        params["offset"] = self.offset
        params["maxSize"] = self.max_size
        
        # Ordering
        if self.order_by:
            params["orderBy"] = self.order_by
            # order field'ı enum veya string olabilir
            if isinstance(self.order, OrderDirection):
                params["order"] = self.order.value
            else:
                params["order"] = str(self.order)
        
        # Selection
        if self.select:
            params["select"] = ",".join(self.select)
        
        # Where clauses
        if self.where:
            # EspoCRM where parametresi doğrudan array olarak gönderilir
            params["where"] = self.where
        
        return params
    
    def to_dict(self) -> Dict[str, Any]:
        """Dictionary formatına çevirir."""
        return self.model_dump(exclude_none=True, by_alias=True)


# Convenience functions for creating search parameters
def create_search_params(
    offset: int = 0,
    max_size: int = 20,
    order_by: Optional[str] = None,
    order: OrderDirection = OrderDirection.ASC,
    select: Optional[List[str]] = None
) -> SearchParams:
    """SearchParams oluşturur."""
    return SearchParams(
        offset=offset,
        maxSize=max_size,
        orderBy=order_by,
        order=order,
        select=select
    )


def equals(field: str, value: Union[str, int, float, bool]) -> WhereClause:
    """Eşitlik clause'u oluşturur."""
    return WhereClause(type=WhereOperator.EQUALS, attribute=field, value=value)


def not_equals(field: str, value: Union[str, int, float, bool]) -> WhereClause:
    """Eşitsizlik clause'u oluşturur."""
    return WhereClause(type=WhereOperator.NOT_EQUALS, attribute=field, value=value)


def greater_than(field: str, value: Union[str, int, float, datetime, date]) -> WhereClause:
    """Büyüktür clause'u oluşturur."""
    return WhereClause(type=WhereOperator.GREATER_THAN, attribute=field, value=value)


def less_than(field: str, value: Union[str, int, float, datetime, date]) -> WhereClause:
    """Küçüktür clause'u oluşturur."""
    return WhereClause(type=WhereOperator.LESS_THAN, attribute=field, value=value)


def in_list(field: str, values: List[Union[str, int, float]]) -> WhereClause:
    """Liste içinde clause'u oluşturur."""
    return WhereClause(type=WhereOperator.IN, attribute=field, value=values)


def not_in_list(field: str, values: List[Union[str, int, float]]) -> WhereClause:
    """Liste dışında clause'u oluşturur."""
    return WhereClause(type=WhereOperator.NOT_IN, attribute=field, value=values)


def contains(field: str, value: str) -> WhereClause:
    """İçerir clause'u oluşturur."""
    return WhereClause(type=WhereOperator.CONTAINS, attribute=field, value=value)


def starts_with(field: str, value: str) -> WhereClause:
    """Başlar clause'u oluşturur."""
    return WhereClause(type=WhereOperator.STARTS_WITH, attribute=field, value=value)


def ends_with(field: str, value: str) -> WhereClause:
    """Biter clause'u oluşturur."""
    return WhereClause(type=WhereOperator.ENDS_WITH, attribute=field, value=value)


def is_null(field: str) -> WhereClause:
    """Null clause'u oluşturur."""
    return WhereClause(type=WhereOperator.IS_NULL, attribute=field)


def is_not_null(field: str) -> WhereClause:
    """Not null clause'u oluşturur."""
    return WhereClause(type=WhereOperator.IS_NOT_NULL, attribute=field)


def between(field: str, start: Union[str, int, float, datetime, date],
           end: Union[str, int, float, datetime, date]) -> WhereClause:
    """Aralık clause'u oluşturur."""
    return WhereClause(type=WhereOperator.BETWEEN, attribute=field, value=[start, end])


def today(field: str) -> WhereClause:
    """Bugün clause'u oluşturur."""
    return WhereClause(type=WhereOperator.TODAY, attribute=field)


def past(field: str) -> WhereClause:
    """Geçmiş clause'u oluşturur."""
    return WhereClause(type=WhereOperator.PAST, attribute=field)


def future(field: str) -> WhereClause:
    """Gelecek clause'u oluşturur."""
    return WhereClause(type=WhereOperator.FUTURE, attribute=field)


# Export edilecek sınıflar ve fonksiyonlar
__all__ = [
    # Enums
    "OrderDirection",
    "WhereOperator",
    
    # Base classes
    "WhereClause",
    "OrderBy",
    "Pagination",
    "Select",
    "SearchParams",
    
    # Convenience functions
    "create_search_params",
    "equals",
    "not_equals",
    "greater_than",
    "less_than",
    "in_list",
    "not_in_list",
    "contains",
    "starts_with",
    "ends_with",
    "is_null",
    "is_not_null",
    "between",
    "today",
    "past",
    "future",
]