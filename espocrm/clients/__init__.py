"""
EspoCRM Client modülleri

Farklı API işlemleri için özelleşmiş client sınıfları:
- CRUD operasyonları
- İlişki yönetimi
- Stream işlemleri
- Dosya yönetimi
- Metadata işlemleri
"""

from .base import BaseClient, EntityClient, RateLimiter, ClientType
from .crud import CrudClient
from .relationships import RelationshipClient, RelationshipOperationResult
from .stream import StreamClient
from .attachments import AttachmentClient, ProgressCallback, StreamingUploader
from .metadata import MetadataClient, MetadataCache

__all__ = [
    "BaseClient",
    "EntityClient",
    "RateLimiter",
    "ClientType",
    "CrudClient",
    "RelationshipClient",
    "RelationshipOperationResult",
    "StreamClient",
    "AttachmentClient",
    "ProgressCallback",
    "StreamingUploader",
    "MetadataClient",
    "MetadataCache",
]