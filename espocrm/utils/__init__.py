"""
EspoCRM Utils Module

Bu modül EspoCRM API istemcisi için utility sınıfları ve fonksiyonları sağlar.
HTTP adapter, serializers, validators ve helper utilities içerir.
"""

# HTTP utilities
from .http import (
    EspoCRMHTTPAdapter,
    HTTPClient,
    create_http_client,
)

# Serialization utilities
from .serializers import (
    EspoCRMJSONEncoder,
    EspoCRMJSONDecoder,
    DataSerializer,
    build_query_string,
    parse_espocrm_response,
    validate_espocrm_data,
    serialize,
    deserialize,
    to_espocrm_format,
    from_espocrm_format,
)

# Validation utilities
from .validators import (
    ValidationError,
    DataValidator,
    validate_url,
    validate_espocrm_id,
    validate_field_name,
    validate_entity_type,
    validate_email,
    validate_phone,
    validate_data_type,
    validate_range,
    validate_length,
    validate_required_fields,
    validate,
    validate_dict,
)

# Helper utilities
from .helpers import (
    snake_to_camel,
    camel_to_snake,
    pascal_to_snake,
    snake_to_pascal,
    deep_merge,
    flatten_dict,
    unflatten_dict,
    filter_dict,
    clean_dict,
    generate_request_id,
    generate_hash,
    mask_sensitive_data,
    chunk_list,
    retry_on_exception,
    timing_decorator,
    get_utc_timestamp,
    parse_iso_datetime,
    safe_get,
    safe_set,
    format_bytes,
)

# Version info
__version__ = "1.0.0"

# Public API
__all__ = [
    # HTTP utilities
    "EspoCRMHTTPAdapter",
    "HTTPClient",
    "create_http_client",
    
    # Serialization utilities
    "EspoCRMJSONEncoder",
    "EspoCRMJSONDecoder",
    "DataSerializer",
    "build_query_string",
    "parse_espocrm_response",
    "validate_espocrm_data",
    "serialize",
    "deserialize",
    "to_espocrm_format",
    "from_espocrm_format",
    
    # Validation utilities
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
    
    # Helper utilities
    "snake_to_camel",
    "camel_to_snake",
    "pascal_to_snake",
    "snake_to_pascal",
    "deep_merge",
    "flatten_dict",
    "unflatten_dict",
    "filter_dict",
    "clean_dict",
    "generate_request_id",
    "generate_hash",
    "mask_sensitive_data",
    "chunk_list",
    "retry_on_exception",
    "timing_decorator",
    "get_utc_timestamp",
    "parse_iso_datetime",
    "safe_get",
    "safe_set",
    "format_bytes",
]