"""
EspoCRM Python API İstemcisi

Modern, type-safe ve kapsamlı EspoCRM API kütüphanesi.
"""

__version__ = "0.1.0"
__author__ = "EspoCRM Python Client Team"
__email__ = "support@espocrm-python-client.com"

# Core client
from .client import EspoCRMClient, create_client

# Configuration
from .config import ClientConfig, create_config_from_env, get_default_config, set_default_config

# Authentication
from .auth import (
    AuthenticationBase,
    APIKeyAuth,
    BasicAuth,
    HMACAuth,
)

# Exceptions
from .exceptions import (
    EspoCRMAPIError,
    EspoCRMAuthenticationError,
    EspoCRMAuthorizationError,
    EspoCRMConnectionError,
    EspoCRMError,
    EspoCRMNotFoundError,
    EspoCRMRateLimitError,
    EspoCRMServerError,
    EspoCRMValidationError,
    create_exception_from_status_code,
)

# Logging
from .logging import (
    get_logger,
    setup_logging,
    configure_espocrm_logging,
)

# Utils (commonly used)
from .utils import (
    ValidationError,
    validate_url,
    validate_espocrm_id,
    build_query_string,
    serialize,
    deserialize,
)

# Models (commonly used)
from .models import (
    # Base models
    EspoCRMBaseModel,
    EntityRecord,
    
    # Search models
    SearchParams,
    WhereOperator,
    OrderDirection,
    
    # Entity models
    Account,
    Contact,
    Lead,
    Opportunity,
    
    # Response models
    EntityResponse,
    ListResponse,
    BulkOperationResult,
    
    # Convenience functions
    create_search_params,
    equals,
    not_equals,
    contains,
    starts_with,
    ends_with,
    is_null,
    is_not_null,
    greater_than,
    less_than,
    in_list,
    not_in_list,
    between,
    today,
    past,
    future,
    create_entity,
    
    # Metadata models
    FieldType,
    RelationshipType,
    FieldMetadata,
    RelationshipMetadata,
    EntityMetadata,
    ApplicationMetadata,
    MetadataRequest,
)

# Clients
from .clients import CrudClient, MetadataClient

__all__ = [
    # Core
    "EspoCRMClient",
    "create_client",
    
    # Configuration
    "ClientConfig",
    "create_config_from_env",
    "get_default_config",
    "set_default_config",
    
    # Authentication
    "AuthenticationBase",
    "APIKeyAuth",
    "BasicAuth",
    "HMACAuth",
    
    # Exceptions
    "EspoCRMError",
    "EspoCRMAPIError",
    "EspoCRMAuthenticationError",
    "EspoCRMAuthorizationError",
    "EspoCRMValidationError",
    "EspoCRMConnectionError",
    "EspoCRMRateLimitError",
    "EspoCRMNotFoundError",
    "EspoCRMServerError",
    "create_exception_from_status_code",
    
    # Logging
    "get_logger",
    "setup_logging",
    "configure_espocrm_logging",
    
    # Utils
    "ValidationError",
    "validate_url",
    "validate_espocrm_id",
    "build_query_string",
    "serialize",
    "deserialize",
    
    # Models
    "EspoCRMBaseModel",
    "EntityRecord",
    "SearchParams",
    "WhereOperator",
    "OrderDirection",
    "Account",
    "Contact",
    "Lead",
    "Opportunity",
    "EntityResponse",
    "ListResponse",
    "BulkOperationResult",
    
    # Model convenience functions
    "create_search_params",
    "equals",
    "not_equals",
    "contains",
    "starts_with",
    "ends_with",
    "is_null",
    "is_not_null",
    "greater_than",
    "less_than",
    "in_list",
    "not_in_list",
    "between",
    "today",
    "past",
    "future",
    "create_entity",
    
    # Metadata models
    "FieldType",
    "RelationshipType",
    "FieldMetadata",
    "RelationshipMetadata",
    "EntityMetadata",
    "ApplicationMetadata",
    "MetadataRequest",
    
    # Clients
    "CrudClient",
    "MetadataClient",
]