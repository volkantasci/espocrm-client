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
    value: Optional[Union[str, int, float, bool, List[Any], Dict[str, Any]]] = Field(
        default=None, 
        description="Karşılaştırma değeri"
    )
    
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


class EqualsClause(WhereClause):
    """Eşitlik kontrolü için where clause."""
    type: Literal[WhereOperator.EQUALS] = WhereOperator.EQUALS
    attribute: str
    value: Union[str, int, float, bool]


class NotEqualsClause(WhereClause):
    """Eşitsizlik kontrolü için where clause."""
    type: Literal[WhereOperator.NOT_EQUALS] = WhereOperator.NOT_EQUALS
    attribute: str
    value: Union[str, int, float, bool]


class GreaterThanClause(WhereClause):
    """Büyüktür kontrolü için where clause."""
    type: Literal[WhereOperator.GREATER_THAN] = WhereOperator.GREATER_THAN
    attribute: str
    value: Union[str, int, float, datetime, date]


class LessThanClause(WhereClause):
    """Küçüktür kontrolü için where clause."""
    type: Literal[WhereOperator.LESS_THAN] = WhereOperator.LESS_THAN
    attribute: str
    value: Union[str, int, float, datetime, date]


class GreaterThanOrEqualClause(WhereClause):
    """Büyük eşit kontrolü için where clause."""
    type: Literal[WhereOperator.GREATER_THAN_OR_EQUAL] = WhereOperator.GREATER_THAN_OR_EQUAL
    attribute: str
    value: Union[str, int, float, datetime, date]


class LessThanOrEqualClause(WhereClause):
    """Küçük eşit kontrolü için where clause."""
    type: Literal[WhereOperator.LESS_THAN_OR_EQUAL] = WhereOperator.LESS_THAN_OR_EQUAL
    attribute: str
    value: Union[str, int, float, datetime, date]


class IsNullClause(WhereClause):
    """Null kontrolü için where clause."""
    type: Literal[WhereOperator.IS_NULL] = WhereOperator.IS_NULL
    attribute: str
    value: Optional[Any] = None


class IsNotNullClause(WhereClause):
    """Not null kontrolü için where clause."""
    type: Literal[WhereOperator.IS_NOT_NULL] = WhereOperator.IS_NOT_NULL
    attribute: str
    value: Optional[Any] = None


class InClause(WhereClause):
    """Liste içinde kontrolü için where clause."""
    type: Literal[WhereOperator.IN] = WhereOperator.IN
    attribute: str
    value: List[Union[str, int, float]]


class NotInClause(WhereClause):
    """Liste dışında kontrolü için where clause."""
    type: Literal[WhereOperator.NOT_IN] = WhereOperator.NOT_IN
    attribute: str
    value: List[Union[str, int, float]]


class ContainsClause(WhereClause):
    """İçerir kontrolü için where clause."""
    type: Literal[WhereOperator.CONTAINS] = WhereOperator.CONTAINS
    attribute: str
    value: str


class NotContainsClause(WhereClause):
    """İçermez kontrolü için where clause."""
    type: Literal[WhereOperator.NOT_CONTAINS] = WhereOperator.NOT_CONTAINS
    attribute: str
    value: str


class StartsWithClause(WhereClause):
    """Başlar kontrolü için where clause."""
    type: Literal[WhereOperator.STARTS_WITH] = WhereOperator.STARTS_WITH
    attribute: str
    value: str


class EndsWithClause(WhereClause):
    """Biter kontrolü için where clause."""
    type: Literal[WhereOperator.ENDS_WITH] = WhereOperator.ENDS_WITH
    attribute: str
    value: str


class LikeClause(WhereClause):
    """Like kontrolü için where clause."""
    type: Literal[WhereOperator.LIKE] = WhereOperator.LIKE
    attribute: str
    value: str


class NotLikeClause(WhereClause):
    """Not like kontrolü için where clause."""
    type: Literal[WhereOperator.NOT_LIKE] = WhereOperator.NOT_LIKE
    attribute: str
    value: str


class BetweenClause(WhereClause):
    """Aralık kontrolü için where clause."""
    type: Literal[WhereOperator.BETWEEN] = WhereOperator.BETWEEN
    attribute: str
    value: List[Union[str, int, float, datetime, date]]
    
    @field_validator('value')
    @classmethod
    def validate_between_value(cls, v):
        """Between değerinin 2 elemanlı liste olduğunu doğrular."""
        if not isinstance(v, list) or len(v) != 2:
            raise ValueError("Between operatörü için value 2 elemanlı liste olmalıdır")
        return v


class TodayClause(WhereClause):
    """Bugün kontrolü için where clause."""
    type: Literal[WhereOperator.TODAY] = WhereOperator.TODAY
    attribute: str
    value: Optional[Any] = None


class PastClause(WhereClause):
    """Geçmiş kontrolü için where clause."""
    type: Literal[WhereOperator.PAST] = WhereOperator.PAST
    attribute: str
    value: Optional[Any] = None


class FutureClause(WhereClause):
    """Gelecek kontrolü için where clause."""
    type: Literal[WhereOperator.FUTURE] = WhereOperator.FUTURE
    attribute: str
    value: Optional[Any] = None


class OrClause(WhereClause):
    """OR mantıksal operatörü için where clause."""
    type: Literal[WhereOperator.OR] = WhereOperator.OR
    attribute: Optional[str] = None
    value: List[Dict[str, Any]]


class AndClause(WhereClause):
    """AND mantıksal operatörü için where clause."""
    type: Literal[WhereOperator.AND] = WhereOperator.AND
    attribute: Optional[str] = None
    value: List[Dict[str, Any]]


class NotClause(WhereClause):
    """NOT mantıksal operatörü için where clause."""
    type: Literal[WhereOperator.NOT] = WhereOperator.NOT
    attribute: Optional[str] = None
    value: Dict[str, Any]


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
        clause = EqualsClause(attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_not_equals(self, field: str, value: Union[str, int, float, bool]) -> "SearchParams":
        """Eşitsizlik kontrolü ekler."""
        clause = NotEqualsClause(attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_greater_than(self, field: str, value: Union[str, int, float, datetime, date]) -> "SearchParams":
        """Büyüktür kontrolü ekler."""
        clause = GreaterThanClause(attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_less_than(self, field: str, value: Union[str, int, float, datetime, date]) -> "SearchParams":
        """Küçüktür kontrolü ekler."""
        clause = LessThanClause(attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_in(self, field: str, values: List[Union[str, int, float]]) -> "SearchParams":
        """Liste içinde kontrolü ekler."""
        clause = InClause(attribute=field, value=values)
        return self.add_where_clause(clause)
    
    def add_not_in(self, field: str, values: List[Union[str, int, float]]) -> "SearchParams":
        """Liste dışında kontrolü ekler."""
        clause = NotInClause(attribute=field, value=values)
        return self.add_where_clause(clause)
    
    def add_contains(self, field: str, value: str) -> "SearchParams":
        """İçerir kontrolü ekler."""
        clause = ContainsClause(attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_starts_with(self, field: str, value: str) -> "SearchParams":
        """Başlar kontrolü ekler."""
        clause = StartsWithClause(attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_ends_with(self, field: str, value: str) -> "SearchParams":
        """Biter kontrolü ekler."""
        clause = EndsWithClause(attribute=field, value=value)
        return self.add_where_clause(clause)
    
    def add_is_null(self, field: str) -> "SearchParams":
        """Null kontrolü ekler."""
        clause = IsNullClause(attribute=field)
        return self.add_where_clause(clause)
    
    def add_is_not_null(self, field: str) -> "SearchParams":
        """Not null kontrolü ekler."""
        clause = IsNotNullClause(attribute=field)
        return self.add_where_clause(clause)
    
    def add_between(self, field: str, start: Union[str, int, float, datetime, date], 
                   end: Union[str, int, float, datetime, date]) -> "SearchParams":
        """Aralık kontrolü ekler."""
        clause = BetweenClause(attribute=field, value=[start, end])
        return self.add_where_clause(clause)
    
    def add_today(self, field: str) -> "SearchParams":
        """Bugün kontrolü ekler."""
        clause = TodayClause(attribute=field)
        return self.add_where_clause(clause)
    
    def add_past(self, field: str) -> "SearchParams":
        """Geçmiş kontrolü ekler."""
        clause = PastClause(attribute=field)
        return self.add_where_clause(clause)
    
    def add_future(self, field: str) -> "SearchParams":
        """Gelecek kontrolü ekler."""
        clause = FutureClause(attribute=field)
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
            params["order"] = self.order.value
        
        # Selection
        if self.select:
            params["select"] = ",".join(self.select)
        
        # Where clauses
        if self.where:
            # EspoCRM where parametresi JSON array olarak gönderilir
            import json
            params["where"] = json.dumps(self.where)
        
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
        max_size=max_size,
        order_by=order_by,
        order=order,
        select=select
    )


def equals(field: str, value: Union[str, int, float, bool]) -> EqualsClause:
    """Eşitlik clause'u oluşturur."""
    return EqualsClause(attribute=field, value=value)


def not_equals(field: str, value: Union[str, int, float, bool]) -> NotEqualsClause:
    """Eşitsizlik clause'u oluşturur."""
    return NotEqualsClause(attribute=field, value=value)


def greater_than(field: str, value: Union[str, int, float, datetime, date]) -> GreaterThanClause:
    """Büyüktür clause'u oluşturur."""
    return GreaterThanClause(attribute=field, value=value)


def less_than(field: str, value: Union[str, int, float, datetime, date]) -> LessThanClause:
    """Küçüktür clause'u oluşturur."""
    return LessThanClause(attribute=field, value=value)


def in_list(field: str, values: List[Union[str, int, float]]) -> InClause:
    """Liste içinde clause'u oluşturur."""
    return InClause(attribute=field, value=values)


def not_in_list(field: str, values: List[Union[str, int, float]]) -> NotInClause:
    """Liste dışında clause'u oluşturur."""
    return NotInClause(attribute=field, value=values)


def contains(field: str, value: str) -> ContainsClause:
    """İçerir clause'u oluşturur."""
    return ContainsClause(attribute=field, value=value)


def starts_with(field: str, value: str) -> StartsWithClause:
    """Başlar clause'u oluşturur."""
    return StartsWithClause(attribute=field, value=value)


def ends_with(field: str, value: str) -> EndsWithClause:
    """Biter clause'u oluşturur."""
    return EndsWithClause(attribute=field, value=value)


def is_null(field: str) -> IsNullClause:
    """Null clause'u oluşturur."""
    return IsNullClause(attribute=field)


def is_not_null(field: str) -> IsNotNullClause:
    """Not null clause'u oluşturur."""
    return IsNotNullClause(attribute=field)


def between(field: str, start: Union[str, int, float, datetime, date], 
           end: Union[str, int, float, datetime, date]) -> BetweenClause:
    """Aralık clause'u oluşturur."""
    return BetweenClause(attribute=field, value=[start, end])


def today(field: str) -> TodayClause:
    """Bugün clause'u oluşturur."""
    return TodayClause(attribute=field)


def past(field: str) -> PastClause:
    """Geçmiş clause'u oluşturur."""
    return PastClause(attribute=field)


def future(field: str) -> FutureClause:
    """Gelecek clause'u oluşturur."""
    return FutureClause(attribute=field)


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
    
    # Specific clause types
    "EqualsClause",
    "NotEqualsClause",
    "GreaterThanClause",
    "LessThanClause",
    "GreaterThanOrEqualClause",
    "LessThanOrEqualClause",
    "IsNullClause",
    "IsNotNullClause",
    "InClause",
    "NotInClause",
    "ContainsClause",
    "NotContainsClause",
    "StartsWithClause",
    "EndsWithClause",
    "LikeClause",
    "NotLikeClause",
    "BetweenClause",
    "TodayClause",
    "PastClause",
    "FutureClause",
    "OrClause",
    "AndClause",
    "NotClause",
    
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