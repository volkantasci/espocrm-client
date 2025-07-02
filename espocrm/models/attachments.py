"""EspoCRM Attachment modelleri.

Bu modül EspoCRM API'nin attachment (dosya) yönetimi için Pydantic modellerini içerir.
File upload, download, validation ve metadata yönetimi sağlar.
"""

import base64
import hashlib
import mimetypes
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field

from .base import EspoCRMBaseModel


class AttachmentRole(str, Enum):
    """Attachment role türleri."""
    ATTACHMENT = "Attachment"
    INLINE_ATTACHMENT = "Inline Attachment"


class AttachmentFieldType(str, Enum):
    """Attachment field türleri."""
    FILE = "file"  # Tek dosya (Document entity)
    ATTACHMENTS = "attachments"  # Çoklu dosya (Note, Email vb.)


class FileValidationError(Exception):
    """Dosya validation hatası."""
    pass


class SecurityValidationError(Exception):
    """Güvenlik validation hatası."""
    pass


class AttachmentMetadata(BaseModel):
    """Dosya metadata bilgileri."""
    
    size: int = Field(
        description="Dosya boyutu (bytes)",
        ge=0
    )
    
    mime_type: str = Field(
        description="MIME type",
        max_length=255
    )
    
    extension: Optional[str] = Field(
        default=None,
        description="Dosya uzantısı",
        max_length=10
    )
    
    checksum: Optional[str] = Field(
        default=None,
        description="Dosya checksum (MD5)",
        max_length=32
    )
    
    encoding: Optional[str] = Field(
        default=None,
        description="Dosya encoding",
        max_length=50
    )
    
    width: Optional[int] = Field(
        default=None,
        description="Görsel genişliği (px)",
        ge=0
    )
    
    height: Optional[int] = Field(
        default=None,
        description="Görsel yüksekliği (px)",
        ge=0
    )
    
    duration: Optional[float] = Field(
        default=None,
        description="Video/audio süresi (saniye)",
        ge=0
    )
    
    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """MIME type formatını doğrular."""
        if not v or "/" not in v:
            raise ValueError("Geçersiz MIME type formatı")
        
        main_type, sub_type = v.split("/", 1)
        if not main_type or not sub_type:
            raise ValueError("MIME type ana ve alt türü içermelidir")
        
        return v.lower()
    
    @field_validator("extension")
    @classmethod
    def validate_extension(cls, v: Optional[str]) -> Optional[str]:
        """Dosya uzantısını doğrular."""
        if v is None:
            return v
        
        # Nokta ile başlıyorsa kaldır
        if v.startswith("."):
            v = v[1:]
        
        # Sadece alphanumeric karakterler
        if not v.isalnum():
            raise ValueError("Dosya uzantısı sadece alphanumeric karakterler içermelidir")
        
        return v.lower()
    
    @field_validator("checksum")
    @classmethod
    def validate_checksum(cls, v: Optional[str]) -> Optional[str]:
        """Checksum formatını doğrular."""
        if v is None:
            return v
        
        if len(v) != 32 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("Checksum 32 karakterlik hexadecimal string olmalıdır")
        
        return v.lower()
    
    def is_image(self) -> bool:
        """Dosyanın görsel olup olmadığını kontrol eder."""
        return self.mime_type.startswith("image/")
    
    def is_video(self) -> bool:
        """Dosyanın video olup olmadığını kontrol eder."""
        return self.mime_type.startswith("video/")
    
    def is_audio(self) -> bool:
        """Dosyanın audio olup olmadığını kontrol eder."""
        return self.mime_type.startswith("audio/")
    
    def is_document(self) -> bool:
        """Dosyanın dokuman olup olmadığını kontrol eder."""
        document_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain",
            "text/csv",
        ]
        return self.mime_type in document_types
    
    def get_human_readable_size(self) -> str:
        """İnsan okunabilir dosya boyutu döndürür."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.size < 1024.0:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024.0
        return f"{self.size:.1f} PB"


class Attachment(EspoCRMBaseModel):
    """EspoCRM Attachment entity modeli."""
    
    # Temel attachment bilgileri
    name: str = Field(
        description="Dosya adı",
        max_length=255
    )
    
    type: str = Field(
        description="MIME type",
        max_length=255
    )
    
    size: int = Field(
        description="Dosya boyutu (bytes)",
        ge=0
    )
    
    role: AttachmentRole = Field(
        default=AttachmentRole.ATTACHMENT,
        description="Attachment rolü"
    )
    
    # İlişki bilgileri
    parent_type: Optional[str] = Field(
        default=None,
        description="Parent entity türü",
        alias="parentType",
        max_length=100
    )
    
    parent_id: Optional[str] = Field(
        default=None,
        description="Parent entity ID'si",
        alias="parentId",
        max_length=17
    )
    
    related_type: Optional[str] = Field(
        default=None,
        description="Related entity türü",
        alias="relatedType",
        max_length=100
    )
    
    related_id: Optional[str] = Field(
        default=None,
        description="Related entity ID'si",
        alias="relatedId",
        max_length=17
    )
    
    field: Optional[str] = Field(
        default=None,
        description="Field adı",
        max_length=100
    )
    
    # Dosya bilgileri
    source_id: Optional[str] = Field(
        default=None,
        description="Source attachment ID'si",
        alias="sourceId",
        max_length=17
    )
    
    storage: Optional[str] = Field(
        default=None,
        description="Storage türü",
        max_length=50
    )
    
    storage_file_path: Optional[str] = Field(
        default=None,
        description="Storage'daki dosya yolu",
        alias="storageFilePath",
        max_length=500
    )
    
    # Ek metadata
    contents: Optional[str] = Field(
        default=None,
        description="Base64 encoded dosya içeriği (upload için)"
    )
    
    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
    }
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Dosya adını doğrular."""
        if not v.strip():
            raise ValueError("Dosya adı boş olamaz")
        
        # Tehlikeli karakterleri kontrol et
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in v for char in dangerous_chars):
            raise ValueError("Dosya adı tehlikeli karakterler içeriyor")
        
        return v.strip()
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """MIME type'ı doğrular."""
        if not v or "/" not in v:
            raise ValueError("Geçersiz MIME type formatı")
        return v.lower()
    
    @field_validator("contents")
    @classmethod
    def validate_contents(cls, v: Optional[str]) -> Optional[str]:
        """Base64 içeriği doğrular."""
        if v is None:
            return v
        
        try:
            # Base64 decode test
            base64.b64decode(v, validate=True)
            return v
        except Exception:
            raise ValueError("Geçersiz Base64 içerik")
    
    @computed_field
    @property
    def metadata(self) -> AttachmentMetadata:
        """Attachment metadata'sını döndürür."""
        extension = None
        if "." in self.name:
            extension = self.name.split(".")[-1]
        
        return AttachmentMetadata(
            size=self.size,
            mime_type=self.type,
            extension=extension
        )
    
    def get_file_extension(self) -> Optional[str]:
        """Dosya uzantısını döndürür."""
        if "." in self.name:
            return self.name.split(".")[-1].lower()
        return None
    
    def is_image(self) -> bool:
        """Dosyanın görsel olup olmadığını kontrol eder."""
        return self.type.startswith("image/")
    
    def is_safe_file_type(self) -> bool:
        """Dosya türünün güvenli olup olmadığını kontrol eder."""
        safe_types = [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "application/pdf", "text/plain", "text/csv",
            "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]
        return self.type in safe_types
    
    def get_download_url(self, base_url: str) -> str:
        """Download URL'ini oluşturur."""
        return f"{base_url.rstrip('/')}/api/v1/Attachment/file/{self.id}"


class AttachmentUploadRequest(BaseModel):
    """Attachment upload request modeli."""
    
    name: str = Field(
        description="Dosya adı",
        max_length=255
    )
    
    type: str = Field(
        description="MIME type",
        max_length=255
    )
    
    role: AttachmentRole = Field(
        default=AttachmentRole.ATTACHMENT,
        description="Attachment rolü"
    )
    
    file: str = Field(
        description="Base64 encoded dosya içeriği"
    )
    
    # Field type'a göre farklı parametreler
    # File field için
    related_type: Optional[str] = Field(
        default=None,
        description="Related entity türü (File field için)",
        alias="relatedType",
        max_length=100
    )
    
    field: Optional[str] = Field(
        default=None,
        description="Field adı",
        max_length=100
    )
    
    # Attachment-Multiple field için
    parent_type: Optional[str] = Field(
        default=None,
        description="Parent entity türü (Attachment-Multiple field için)",
        alias="parentType",
        max_length=100
    )
    
    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
    }
    
    @field_validator("file")
    @classmethod
    def validate_file_content(cls, v: str) -> str:
        """Base64 dosya içeriğini doğrular."""
        try:
            # Base64 decode test
            decoded = base64.b64decode(v, validate=True)
            if len(decoded) == 0:
                raise ValueError("Dosya içeriği boş olamaz")
            return v
        except Exception:
            raise ValueError("Geçersiz Base64 dosya içeriği")
    
    @model_validator(mode='after')
    def validate_field_parameters(self):
        """Field parametrelerini doğrular."""
        # File field veya Attachment-Multiple field için gerekli parametreler
        if self.related_type and not self.field:
            raise ValueError("File field için field parametresi gereklidir")
        
        if self.parent_type and self.field != "attachments":
            raise ValueError("Attachment-Multiple field için field 'attachments' olmalıdır")
        
        return self
    
    def get_file_size(self) -> int:
        """Dosya boyutunu hesaplar."""
        try:
            decoded = base64.b64decode(self.file)
            return len(decoded)
        except Exception:
            return 0
    
    def get_file_checksum(self) -> str:
        """Dosya checksum'ını hesaplar."""
        try:
            decoded = base64.b64decode(self.file)
            return hashlib.md5(decoded).hexdigest()
        except Exception:
            return ""
    
    def to_api_dict(self) -> Dict[str, Any]:
        """API için dictionary formatına çevirir."""
        data = {
            "name": self.name,
            "type": self.type,
            "role": self.role.value,
            "file": self.file
        }
        
        if self.related_type:
            data["relatedType"] = self.related_type
        
        if self.field:
            data["field"] = self.field
        
        if self.parent_type:
            data["parentType"] = self.parent_type
        
        return data


class AttachmentDownloadRequest(BaseModel):
    """Attachment download request modeli."""
    
    attachment_id: str = Field(
        description="Attachment ID'si",
        min_length=17,
        max_length=17
    )
    
    save_path: Optional[Union[str, Path]] = Field(
        default=None,
        description="Dosyanın kaydedileceği yol"
    )
    
    overwrite: bool = Field(
        default=False,
        description="Mevcut dosyanın üzerine yazılsın mı"
    )
    
    validate_checksum: bool = Field(
        default=True,
        description="Checksum doğrulaması yapılsın mı"
    )
    
    @field_validator("attachment_id")
    @classmethod
    def validate_attachment_id(cls, v: str) -> str:
        """Attachment ID formatını doğrular."""
        if not v.isalnum():
            raise ValueError("Attachment ID sadece alphanumeric karakterler içermelidir")
        return v
    
    def get_save_path(self, filename: str) -> Path:
        """Kaydetme yolunu döndürür."""
        if self.save_path:
            save_path = Path(self.save_path)
            if save_path.is_dir():
                return save_path / filename
            else:
                return save_path
        else:
            return Path(filename)


class BulkAttachmentUploadRequest(BaseModel):
    """Bulk attachment upload request modeli."""
    
    files: List[AttachmentUploadRequest] = Field(
        description="Upload edilecek dosyalar",
        min_length=1,
        max_length=100
    )
    
    parent_type: Optional[str] = Field(
        default=None,
        description="Parent entity türü",
        alias="parentType"
    )
    
    parent_id: Optional[str] = Field(
        default=None,
        description="Parent entity ID'si",
        alias="parentId"
    )
    
    field: Optional[str] = Field(
        default=None,
        description="Field adı"
    )
    
    validate_files: bool = Field(
        default=True,
        description="Dosya validation yapılsın mı"
    )
    
    max_total_size: Optional[int] = Field(
        default=None,
        description="Maksimum toplam dosya boyutu (bytes)",
        ge=0
    )
    
    model_config = {
        "populate_by_name": True,
    }
    
    @model_validator(mode='after')
    def validate_bulk_upload(self):
        """Bulk upload parametrelerini doğrular."""
        # Toplam boyut kontrolü
        if self.max_total_size:
            total_size = sum(file.get_file_size() for file in self.files)
            if total_size > self.max_total_size:
                raise ValueError(f"Toplam dosya boyutu {self.max_total_size} bytes'ı aşamaz")
        
        # Dosya adı tekrarı kontrolü
        names = [file.name for file in self.files]
        if len(names) != len(set(names)):
            raise ValueError("Dosya adları tekrar edemez")
        
        return self
    
    def get_total_size(self) -> int:
        """Toplam dosya boyutunu döndürür."""
        return sum(file.get_file_size() for file in self.files)
    
    def get_file_count(self) -> int:
        """Dosya sayısını döndürür."""
        return len(self.files)


class FileValidationConfig(BaseModel):
    """Dosya validation konfigürasyonu."""
    
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maksimum dosya boyutu (bytes)",
        ge=0
    )
    
    allowed_mime_types: Optional[List[str]] = Field(
        default=None,
        description="İzin verilen MIME type'lar"
    )
    
    blocked_mime_types: List[str] = Field(
        default_factory=lambda: [
            "application/x-executable",
            "application/x-msdownload",
            "application/x-msdos-program",
            "application/x-sh",
            "text/x-shellscript",
        ],
        description="Yasaklı MIME type'lar"
    )
    
    allowed_extensions: Optional[List[str]] = Field(
        default=None,
        description="İzin verilen dosya uzantıları"
    )
    
    blocked_extensions: List[str] = Field(
        default_factory=lambda: [
            "exe", "bat", "cmd", "com", "pif", "scr", "vbs", "js",
            "jar", "sh", "ps1", "php", "asp", "aspx", "jsp"
        ],
        description="Yasaklı dosya uzantıları"
    )
    
    scan_for_malware: bool = Field(
        default=True,
        description="Malware taraması yapılsın mı"
    )
    
    validate_file_headers: bool = Field(
        default=True,
        description="Dosya header'ları doğrulansın mı"
    )
    
    def validate_file(self, attachment: Union[Attachment, AttachmentUploadRequest]) -> None:
        """Dosyayı validation kurallarına göre doğrular."""
        # Boyut kontrolü
        if hasattr(attachment, 'size'):
            size = attachment.size
        else:
            size = attachment.get_file_size()
        
        if size > self.max_file_size:
            raise FileValidationError(f"Dosya boyutu {self.max_file_size} bytes'ı aşamaz")
        
        # MIME type kontrolü
        mime_type = attachment.type
        
        if self.blocked_mime_types and mime_type in self.blocked_mime_types:
            raise SecurityValidationError(f"MIME type '{mime_type}' yasaklıdır")
        
        if self.allowed_mime_types and mime_type not in self.allowed_mime_types:
            raise FileValidationError(f"MIME type '{mime_type}' izin verilmemiştir")
        
        # Uzantı kontrolü
        extension = None
        if "." in attachment.name:
            extension = attachment.name.split(".")[-1].lower()
        
        if extension:
            if self.blocked_extensions and extension in self.blocked_extensions:
                raise SecurityValidationError(f"Dosya uzantısı '{extension}' yasaklıdır")
            
            if self.allowed_extensions and extension not in self.allowed_extensions:
                raise FileValidationError(f"Dosya uzantısı '{extension}' izin verilmemiştir")


# Factory functions
def create_file_upload_request(
    file_path: Union[str, Path],
    related_type: str,
    field: str = "file",
    mime_type: Optional[str] = None
) -> AttachmentUploadRequest:
    """File field için upload request oluşturur."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
    
    # MIME type detect et
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"
    
    # Dosyayı base64'e encode et
    with open(file_path, "rb") as f:
        file_content = base64.b64encode(f.read()).decode("utf-8")
    
    return AttachmentUploadRequest(
        name=file_path.name,
        type=mime_type,
        role=AttachmentRole.ATTACHMENT,
        file=file_content,
        related_type=related_type,
        field=field
    )


def create_attachment_upload_request(
    file_path: Union[str, Path],
    parent_type: str,
    mime_type: Optional[str] = None
) -> AttachmentUploadRequest:
    """Attachment-Multiple field için upload request oluşturur."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
    
    # MIME type detect et
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"
    
    # Dosyayı base64'e encode et
    with open(file_path, "rb") as f:
        file_content = base64.b64encode(f.read()).decode("utf-8")
    
    return AttachmentUploadRequest(
        name=file_path.name,
        type=mime_type,
        role=AttachmentRole.ATTACHMENT,
        file=file_content,
        parent_type=parent_type,
        field="attachments"
    )


def create_attachment_from_bytes(
    file_data: bytes,
    filename: str,
    mime_type: Optional[str] = None
) -> AttachmentUploadRequest:
    """Bytes veriden attachment upload request oluşturur."""
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            mime_type = "application/octet-stream"
    
    file_content = base64.b64encode(file_data).decode("utf-8")
    
    return AttachmentUploadRequest(
        name=filename,
        type=mime_type,
        role=AttachmentRole.ATTACHMENT,
        file=file_content
    )


# Export edilecek sınıflar ve fonksiyonlar
__all__ = [
    # Enums
    "AttachmentRole",
    "AttachmentFieldType",
    
    # Exceptions
    "FileValidationError",
    "SecurityValidationError",
    
    # Models
    "AttachmentMetadata",
    "Attachment",
    "AttachmentUploadRequest",
    "AttachmentDownloadRequest",
    "BulkAttachmentUploadRequest",
    "FileValidationConfig",
    
    # Factory functions
    "create_file_upload_request",
    "create_attachment_upload_request",
    "create_attachment_from_bytes",
]