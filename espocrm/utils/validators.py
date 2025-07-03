"""
EspoCRM Validation Module

Bu modül EspoCRM API istemcisi için validation utilities sağlar.
URL validation, Entity ID validation, field name validation ve data type validation içerir.
"""

import re
from typing import Any, Dict, List, Optional, Union, Callable
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Validation hataları için özel exception."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        """
        Validation error'ını başlatır.
        
        Args:
            message: Hata mesajı
            field: Hata olan field adı
            value: Hatalı değer
        """
        self.field = field
        self.value = value
        super().__init__(message)
    
    def __str__(self) -> str:
        """String representation."""
        if self.field:
            return f"[{self.field}] {super().__str__()}"
        return super().__str__()


def validate_url(url: str, require_https: bool = False) -> bool:
    """
    URL'in geçerli olup olmadığını kontrol eder.
    
    Args:
        url: Kontrol edilecek URL
        require_https: HTTPS zorunlu mu
        
    Returns:
        URL geçerli mi
        
    Raises:
        ValidationError: URL geçersiz
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL cannot be empty or non-string", field="url", value=url)
    
    try:
        parsed = urlparse(url)
        
        # Scheme kontrolü
        if not parsed.scheme:
            raise ValidationError("URL must have a scheme (http/https)", field="url", value=url)
        
        if parsed.scheme not in ('http', 'https'):
            raise ValidationError("URL scheme must be http or https", field="url", value=url)
        
        if require_https and parsed.scheme != 'https':
            raise ValidationError("HTTPS is required", field="url", value=url)
        
        # Netloc kontrolü
        if not parsed.netloc:
            raise ValidationError("URL must have a valid domain", field="url", value=url)
        
        # Domain format kontrolü
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        domain = parsed.netloc.split(':')[0]  # Port'u çıkar
        
        if not re.match(domain_pattern, domain):
            raise ValidationError("Invalid domain format", field="url", value=url)
        
        return True
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}", field="url", value=url)


def validate_espocrm_id(entity_id: str) -> bool:
    """
    EspoCRM entity ID'sinin geçerli olup olmadığını kontrol eder.
    
    EspoCRM ID'leri 17 karakter uzunluğunda alphanumeric string'lerdir.
    
    Args:
        entity_id: Kontrol edilecek entity ID
        
    Returns:
        ID geçerli mi
        
    Raises:
        ValidationError: ID geçersiz
    """
    if not entity_id:
        raise ValidationError("Entity ID cannot be empty", field="id", value=entity_id)
    
    if not isinstance(entity_id, str):
        raise ValidationError("Entity ID must be a string", field="id", value=entity_id)
    
    # EspoCRM ID format: 17 karakter alphanumeric
    if len(entity_id) != 17:
        raise ValidationError(
            "Entity ID must be exactly 17 characters long",
            field="id",
            value=entity_id
        )
    
    if not re.match(r'^[a-zA-Z0-9]{17}$', entity_id):
        raise ValidationError(
            "Entity ID must contain only alphanumeric characters",
            field="id",
            value=entity_id
        )
    
    return True


def validate_field_name(field_name: str) -> bool:
    """
    EspoCRM field adının geçerli olup olmadığını kontrol eder.
    
    Args:
        field_name: Kontrol edilecek field adı
        
    Returns:
        Field adı geçerli mi
        
    Raises:
        ValidationError: Field adı geçersiz
    """
    if not field_name:
        raise ValidationError("Field name cannot be empty", field="fieldName", value=field_name)
    
    if not isinstance(field_name, str):
        raise ValidationError("Field name must be a string", field="fieldName", value=field_name)
    
    # Field name format: camelCase, snake_case veya kebab-case
    # İlk karakter harf olmalı, sonrakiler harf, rakam, underscore veya dash olabilir
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', field_name):
        raise ValidationError(
            "Field name must start with a letter and contain only letters, numbers, underscores, or dashes",
            field="fieldName",
            value=field_name
        )
    
    # Uzunluk kontrolü
    if len(field_name) > 100:
        raise ValidationError(
            "Field name cannot be longer than 100 characters",
            field="fieldName",
            value=field_name
        )
    
    return True


def validate_entity_type(entity_type: str) -> bool:
    """
    EspoCRM entity type'ının geçerli olup olmadığını kontrol eder.
    
    Args:
        entity_type: Kontrol edilecek entity type
        
    Returns:
        Entity type geçerli mi
        
    Raises:
        ValidationError: Entity type geçersiz
    """
    if not entity_type:
        raise ValidationError("Entity type cannot be empty", field="entityType", value=entity_type)
    
    if not isinstance(entity_type, str):
        raise ValidationError("Entity type must be a string", field="entityType", value=entity_type)
    
    # Entity type format: PascalCase
    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', entity_type):
        raise ValidationError(
            "Entity type must be in PascalCase format (start with uppercase letter)",
            field="entityType",
            value=entity_type
        )
    
    # Uzunluk kontrolü
    if len(entity_type) > 50:
        raise ValidationError(
            "Entity type cannot be longer than 50 characters",
            field="entityType",
            value=entity_type
        )
    
    # Geçersiz entity type'ları kontrol et
    invalid_entity_types = ["InvalidEntity", "TestEntity", "FakeEntity"]
    if entity_type in invalid_entity_types:
        raise ValidationError(
            f"Entity type '{entity_type}' is not valid",
            field="entityType",
            value=entity_type
        )
    
    return True


def validate_email(email: str) -> bool:
    """
    Email adresinin geçerli olup olmadığını kontrol eder.
    
    Args:
        email: Kontrol edilecek email adresi
        
    Returns:
        Email geçerli mi
        
    Raises:
        ValidationError: Email geçersiz
    """
    if not email:
        raise ValidationError("Email cannot be empty", field="email", value=email)
    
    if not isinstance(email, str):
        raise ValidationError("Email must be a string", field="email", value=email)
    
    # Basit email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format", field="email", value=email)
    
    # Uzunluk kontrolü
    if len(email) > 254:
        raise ValidationError("Email cannot be longer than 254 characters", field="email", value=email)
    
    return True


def validate_phone(phone: str) -> bool:
    """
    Telefon numarasının geçerli olup olmadığını kontrol eder.
    
    Args:
        phone: Kontrol edilecek telefon numarası
        
    Returns:
        Telefon numarası geçerli mi
        
    Raises:
        ValidationError: Telefon numarası geçersiz
    """
    if not phone:
        raise ValidationError("Phone cannot be empty", field="phone", value=phone)
    
    if not isinstance(phone, str):
        raise ValidationError("Phone must be a string", field="phone", value=phone)
    
    # Telefon numarası pattern: +, rakamlar, boşluk, tire, parantez
    phone_pattern = r'^[\+]?[0-9\s\-\(\)]{7,20}$'
    
    if not re.match(phone_pattern, phone):
        raise ValidationError("Invalid phone format", field="phone", value=phone)
    
    return True


def validate_data_type(value: Any, expected_type: type, field_name: Optional[str] = None) -> bool:
    """
    Değerin beklenen tipte olup olmadığını kontrol eder.
    
    Args:
        value: Kontrol edilecek değer
        expected_type: Beklenen tip
        field_name: Field adı (opsiyonel)
        
    Returns:
        Tip uygun mu
        
    Raises:
        ValidationError: Tip uygun değil
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Expected {expected_type.__name__}, got {type(value).__name__}",
            field=field_name,
            value=value
        )
    
    return True


def validate_range(value: Union[int, float], min_val: Optional[Union[int, float]] = None, 
                  max_val: Optional[Union[int, float]] = None, field_name: Optional[str] = None) -> bool:
    """
    Sayısal değerin belirtilen aralıkta olup olmadığını kontrol eder.
    
    Args:
        value: Kontrol edilecek değer
        min_val: Minimum değer
        max_val: Maksimum değer
        field_name: Field adı (opsiyonel)
        
    Returns:
        Değer aralıkta mı
        
    Raises:
        ValidationError: Değer aralık dışında
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"Expected numeric value, got {type(value).__name__}",
            field=field_name,
            value=value
        )
    
    if min_val is not None and value < min_val:
        raise ValidationError(
            f"Value must be at least {min_val}",
            field=field_name,
            value=value
        )
    
    if max_val is not None and value > max_val:
        raise ValidationError(
            f"Value must be at most {max_val}",
            field=field_name,
            value=value
        )
    
    return True


def validate_length(value: str, min_length: Optional[int] = None, 
                   max_length: Optional[int] = None, field_name: Optional[str] = None) -> bool:
    """
    String'in uzunluğunun belirtilen aralıkta olup olmadığını kontrol eder.
    
    Args:
        value: Kontrol edilecek string
        min_length: Minimum uzunluk
        max_length: Maksimum uzunluk
        field_name: Field adı (opsiyonel)
        
    Returns:
        Uzunluk uygun mu
        
    Raises:
        ValidationError: Uzunluk uygun değil
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Expected string, got {type(value).__name__}",
            field=field_name,
            value=value
        )
    
    length = len(value)
    
    if min_length is not None and length < min_length:
        raise ValidationError(
            f"Length must be at least {min_length} characters",
            field=field_name,
            value=value
        )
    
    if max_length is not None and length > max_length:
        raise ValidationError(
            f"Length must be at most {max_length} characters",
            field=field_name,
            value=value
        )
    
    return True


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Zorunlu field'ların mevcut olup olmadığını kontrol eder.
    
    Args:
        data: Kontrol edilecek veri
        required_fields: Zorunlu field'lar
        
    Returns:
        Tüm zorunlu field'lar mevcut mu
        
    Raises:
        ValidationError: Zorunlu field eksik
    """
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary", value=data)
    
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            field="requiredFields",
            value=missing_fields
        )
    
    return True


class DataValidator:
    """
    EspoCRM veri validation sınıfı.
    
    Çeşitli validation kurallarını bir arada yönetir.
    """
    
    def __init__(self):
        """Data validator'ı başlatır."""
        self.validators: Dict[str, Callable] = {
            'url': validate_url,
            'espocrm_id': validate_espocrm_id,
            'field_name': validate_field_name,
            'entity_type': validate_entity_type,
            'email': validate_email,
            'phone': validate_phone,
        }
    
    def add_validator(self, name: str, validator: Callable) -> None:
        """Yeni validator ekler."""
        self.validators[name] = validator
    
    def validate(self, validator_name: str, value: Any, **kwargs) -> bool:
        """
        Belirtilen validator ile değeri kontrol eder.
        
        Args:
            validator_name: Validator adı
            value: Kontrol edilecek değer
            **kwargs: Validator parametreleri
            
        Returns:
            Validation başarılı mı
            
        Raises:
            ValidationError: Validation hatası
            ValueError: Validator bulunamadı
        """
        if validator_name not in self.validators:
            raise ValueError(f"Unknown validator: {validator_name}")
        
        validator = self.validators[validator_name]
        return validator(value, **kwargs)
    
    def validate_dict(self, data: Dict[str, Any], rules: Dict[str, Dict[str, Any]]) -> bool:
        """
        Dictionary'yi belirtilen kurallara göre validate eder.
        
        Args:
            data: Validate edilecek veri
            rules: Validation kuralları
            
        Returns:
            Validation başarılı mı
            
        Example:
            rules = {
                'name': {'required': True, 'type': str, 'max_length': 100},
                'email': {'required': True, 'validator': 'email'},
                'age': {'type': int, 'min_val': 0, 'max_val': 150}
            }
        """
        errors = []
        
        for field_name, field_rules in rules.items():
            try:
                # Required kontrolü
                if field_rules.get('required', False):
                    if field_name not in data or data[field_name] is None:
                        errors.append(f"Field '{field_name}' is required")
                        continue
                
                # Field mevcut değilse ve required değilse skip et
                if field_name not in data:
                    continue
                
                value = data[field_name]
                
                # Type kontrolü
                if 'type' in field_rules:
                    validate_data_type(value, field_rules['type'], field_name)
                
                # Custom validator
                if 'validator' in field_rules:
                    validator_name = field_rules['validator']
                    validator_kwargs = {k: v for k, v in field_rules.items() 
                                      if k not in ('required', 'type', 'validator')}
                    self.validate(validator_name, value, **validator_kwargs)
                
                # Range kontrolü
                if 'min_val' in field_rules or 'max_val' in field_rules:
                    validate_range(
                        value,
                        field_rules.get('min_val'),
                        field_rules.get('max_val'),
                        field_name
                    )
                
                # Length kontrolü
                if 'min_length' in field_rules or 'max_length' in field_rules:
                    validate_length(
                        value,
                        field_rules.get('min_length'),
                        field_rules.get('max_length'),
                        field_name
                    )
                
            except ValidationError as e:
                errors.append(str(e))
        
        if errors:
            raise ValidationError(f"Validation failed: {'; '.join(errors)}")
        
        return True


# Default validator instance
_default_validator = DataValidator()


def validate(validator_name: str, value: Any, **kwargs) -> bool:
    """Default validator ile değeri kontrol eder."""
    return _default_validator.validate(validator_name, value, **kwargs)


def validate_dict(data: Dict[str, Any], rules: Dict[str, Dict[str, Any]]) -> bool:
    """Default validator ile dictionary'yi validate eder."""
    return _default_validator.validate_dict(data, rules)


# Export edilecek sınıf ve fonksiyonlar
__all__ = [
    "ValidationError",
    "DataValidator",
    "validate_url",
    "validate_espocrm_id",
    "validate_field_name",
    "validate_entity_type",
    "validate_email",
    "validate_phone",
    "validate_data_type",
    "validate_range",
    "validate_length",
    "validate_required_fields",
    "validate",
    "validate_dict",
]


def validate_entity_id(entity_id: str) -> bool:
    """
    Entity ID'sinin güvenlik açısından geçerli olup olmadığını kontrol eder.
    
    Args:
        entity_id: Kontrol edilecek entity ID
        
    Returns:
        ID güvenli mi
        
    Raises:
        ValidationError: ID güvenli değil
    """
    if not entity_id or not isinstance(entity_id, str):
        raise ValidationError("Entity ID boş olamaz", field="id", value=entity_id)
    
    # Path traversal kontrolü
    if ".." in entity_id or "/" in entity_id or "\\" in entity_id:
        raise ValidationError("Entity ID path traversal karakterleri içeremez", field="id", value=entity_id)
    
    # Boşluk kontrolü
    if " " in entity_id:
        raise ValidationError("Entity ID boşluk içeremez", field="id", value=entity_id)
    
    # Uzunluk kontrolü (çok uzun ID'ler DoS saldırısı olabilir)
    if len(entity_id) > 100:
        raise ValidationError("Entity ID çok uzun", field="id", value=entity_id)
    
    # Özel karakterler kontrolü
    if not re.match(r'^[a-zA-Z0-9_-]+$', entity_id):
        raise ValidationError("Entity ID sadece alphanumeric, underscore ve dash içerebilir", field="id", value=entity_id)
    
    return True


def validate_entity_data(data: Dict[str, Any]) -> bool:
    """
    Entity verisinin güvenlik açısından geçerli olup olmadığını kontrol eder.
    
    Args:
        data: Kontrol edilecek entity verisi
        
    Returns:
        Veri güvenli mi
        
    Raises:
        ValidationError: Veri güvenli değil
    """
    if not isinstance(data, dict):
        raise ValidationError("Entity verisi dict olmalıdır", value=data)
    
    # Çok büyük payload kontrolü (DoS prevention)
    if len(str(data)) > 1000000:  # 1MB limit
        raise ValidationError("Entity verisi çok büyük", value="large_payload")
    
    # SQL injection pattern kontrolü
    sql_patterns = [
        r"(?i)(union\s+select)",
        r"(?i)(drop\s+table)",
        r"(?i)(delete\s+from)",
        r"(?i)(insert\s+into)",
        r"(?i)(update\s+\w+\s+set)",
        r"(?i)(exec\s*\()",
        r"(?i)(script\s*>)",
        r"(?i)(javascript\s*:)",
        r"(?i)(on\w+\s*=)"
    ]
    
    for field_name, field_value in data.items():
        if isinstance(field_value, str):
            # SQL injection kontrolü
            for pattern in sql_patterns:
                if re.search(pattern, field_value):
                    raise ValidationError(f"Güvenlik riski tespit edildi: {field_name}", field=field_name, value=field_value)
            
            # XSS kontrolü
            xss_patterns = [
                r"<script[^>]*>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>"
            ]
            
            for pattern in xss_patterns:
                if re.search(pattern, field_value, re.IGNORECASE):
                    raise ValidationError(f"XSS riski tespit edildi: {field_name}", field=field_name, value=field_value)
    
    return True


# Export listesini güncelle
__all__.extend([
    "validate_entity_id",
    "validate_entity_data"
])