"""EspoCRM Stream API modelleri.

Bu modül EspoCRM Stream operasyonları için Pydantic modellerini içerir.
Stream note'ları, post request'leri ve stream filtering desteği sağlar.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from .base import EspoCRMBaseModel


class StreamNoteType(str, Enum):
    """Stream note türleri."""
    
    POST = "Post"
    CREATE = "Create"
    UPDATE = "Update"
    STATUS = "Status"
    ASSIGN = "Assign"
    RELATE = "Relate"
    UNRELATE = "Unrelate"
    EMAIL_RECEIVED = "EmailReceived"
    EMAIL_SENT = "EmailSent"
    CALL_MADE = "CallMade"
    CALL_RECEIVED = "CallReceived"
    MEETING_HELD = "MeetingHeld"
    TASK_COMPLETED = "TaskCompleted"


class StreamNoteData(BaseModel):
    """Stream note'un data field'ı için model."""
    
    # Field değişiklikleri (Update note'ları için)
    fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Değişen field'lar ve değerleri"
    )
    
    # Atama bilgileri (Assign note'ları için)
    assigned_user_id: Optional[str] = Field(
        default=None,
        description="Atanan kullanıcı ID'si",
        alias="assignedUserId"
    )
    
    assigned_user_name: Optional[str] = Field(
        default=None,
        description="Atanan kullanıcı adı",
        alias="assignedUserName"
    )
    
    # İlişki bilgileri (Relate/Unrelate note'ları için)
    related_entity_type: Optional[str] = Field(
        default=None,
        description="İlişkili entity türü",
        alias="relatedEntityType"
    )
    
    related_entity_id: Optional[str] = Field(
        default=None,
        description="İlişkili entity ID'si",
        alias="relatedEntityId"
    )
    
    related_entity_name: Optional[str] = Field(
        default=None,
        description="İlişkili entity adı",
        alias="relatedEntityName"
    )
    
    # Status değişiklikleri için
    status_value: Optional[str] = Field(
        default=None,
        description="Yeni status değeri",
        alias="statusValue"
    )
    
    # Email bilgileri için
    email_id: Optional[str] = Field(
        default=None,
        description="Email ID'si",
        alias="emailId"
    )
    
    email_subject: Optional[str] = Field(
        default=None,
        description="Email konusu",
        alias="emailSubject"
    )
    
    # Call/Meeting bilgileri için
    activity_id: Optional[str] = Field(
        default=None,
        description="Aktivite ID'si",
        alias="activityId"
    )
    
    activity_name: Optional[str] = Field(
        default=None,
        description="Aktivite adı",
        alias="activityName"
    )
    
    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }


class StreamNote(EspoCRMBaseModel):
    """Stream note modeli.
    
    EspoCRM'deki stream kayıtlarını temsil eder.
    Tüm stream aktivitelerinin base modeli.
    """
    
    # Stream note temel field'ları
    type: StreamNoteType = Field(
        description="Stream note türü"
    )
    
    post: Optional[str] = Field(
        default=None,
        description="Post içeriği (HTML formatında)"
    )
    
    parent_id: Optional[str] = Field(
        default=None,
        description="Bağlı entity ID'si",
        alias="parentId",
        max_length=17
    )
    
    parent_type: Optional[str] = Field(
        default=None,
        description="Bağlı entity türü",
        alias="parentType",
        max_length=100
    )
    
    parent_name: Optional[str] = Field(
        default=None,
        description="Bağlı entity adı",
        alias="parentName"
    )
    
    # Kullanıcı bilgileri
    created_by_name: Optional[str] = Field(
        default=None,
        description="Oluşturan kullanıcı adı",
        alias="createdByName"
    )
    
    # Stream note data
    data: Optional[StreamNoteData] = Field(
        default=None,
        description="Stream note verisi"
    )
    
    # Attachment bilgileri
    attachments_ids: Optional[List[str]] = Field(
        default=None,
        description="Attachment ID'leri",
        alias="attachmentsIds"
    )
    
    attachments_names: Optional[Dict[str, str]] = Field(
        default=None,
        description="Attachment ID -> name mapping",
        alias="attachmentsNames"
    )
    
    attachments_types: Optional[Dict[str, str]] = Field(
        default=None,
        description="Attachment ID -> type mapping",
        alias="attachmentsTypes"
    )
    
    # Mention bilgileri
    mentioned_users: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Mention edilen kullanıcılar",
        alias="mentionedUsers"
    )
    
    # Visibility
    is_global: Optional[bool] = Field(
        default=None,
        description="Global stream'de görünür mü",
        alias="isGlobal"
    )
    
    is_internal: Optional[bool] = Field(
        default=None,
        description="Internal note mu",
        alias="isInternal"
    )
    
    # Teams
    teams_ids: Optional[List[str]] = Field(
        default=None,
        description="Görünür team ID'leri",
        alias="teamsIds"
    )
    
    # Portal visibility
    portal_id: Optional[str] = Field(
        default=None,
        description="Portal ID'si",
        alias="portalId"
    )
    
    @field_validator("parent_id")
    @classmethod
    def validate_parent_id(cls, v: Optional[str]) -> Optional[str]:
        """Parent ID formatını doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("Parent ID string formatında olmalıdır")
        
        if len(v) != 17:
            raise ValueError("EspoCRM ID'si 17 karakter uzunluğunda olmalıdır")
        
        if not v.isalnum():
            raise ValueError("EspoCRM ID'si sadece alphanumeric karakterler içermelidir")
        
        return v
    
    @field_validator("attachments_ids")
    @classmethod
    def validate_attachments_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Attachment ID'lerini doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("Attachments IDs liste formatında olmalıdır")
        
        for i, attachment_id in enumerate(v):
            if not isinstance(attachment_id, str):
                raise ValueError(f"Attachment ID[{i}] string formatında olmalıdır")
            
            if len(attachment_id) != 17:
                raise ValueError(f"Attachment ID[{i}] 17 karakter uzunluğunda olmalıdır")
            
            if not attachment_id.isalnum():
                raise ValueError(f"Attachment ID[{i}] sadece alphanumeric karakterler içermelidir")
        
        return v
    
    def get_entity_type(self) -> str:
        """Entity type'ını döndürür."""
        return "Note"
    
    def is_post_type(self) -> bool:
        """Post türünde mi kontrol eder."""
        return self.type == StreamNoteType.POST
    
    def is_system_note(self) -> bool:
        """Sistem notu mu kontrol eder."""
        return self.type != StreamNoteType.POST
    
    def has_attachments(self) -> bool:
        """Attachment'ı var mı kontrol eder."""
        return bool(self.attachments_ids)
    
    def get_attachment_count(self) -> int:
        """Attachment sayısını döndürür."""
        return len(self.attachments_ids) if self.attachments_ids else 0
    
    def has_mentions(self) -> bool:
        """Mention'ı var mı kontrol eder."""
        return bool(self.mentioned_users)
    
    def get_mentioned_user_ids(self) -> List[str]:
        """Mention edilen kullanıcı ID'lerini döndürür."""
        if not self.mentioned_users:
            return []
        
        return [user["id"] for user in self.mentioned_users if user.get("id")]
    
    def get_mentioned_user_names(self) -> List[str]:
        """Mention edilen kullanıcı adlarını döndürür."""
        if not self.mentioned_users:
            return []
        
        return [user["name"] for user in self.mentioned_users if user.get("name")]
    
    def is_visible_to_team(self, team_id: str) -> bool:
        """Belirtilen team'e görünür mü kontrol eder."""
        if not self.teams_ids:
            return True  # Team kısıtlaması yoksa herkese görünür
        
        return team_id in self.teams_ids
    
    def get_display_text(self) -> str:
        """Görüntüleme metni döndürür."""
        if self.is_post_type() and self.post:
            # HTML tag'lerini temizle (basit)
            import re
            clean_text = re.sub(r'<[^>]+>', '', self.post)
            return clean_text.strip()
        
        # Sistem notları için tip bazlı mesaj
        type_messages = {
            StreamNoteType.CREATE: "Kayıt oluşturuldu",
            StreamNoteType.UPDATE: "Kayıt güncellendi",
            StreamNoteType.STATUS: "Durum değiştirildi",
            StreamNoteType.ASSIGN: "Atama yapıldı",
            StreamNoteType.RELATE: "İlişki oluşturuldu",
            StreamNoteType.UNRELATE: "İlişki kaldırıldı",
            StreamNoteType.EMAIL_RECEIVED: "Email alındı",
            StreamNoteType.EMAIL_SENT: "Email gönderildi",
            StreamNoteType.CALL_MADE: "Arama yapıldı",
            StreamNoteType.CALL_RECEIVED: "Arama alındı",
            StreamNoteType.MEETING_HELD: "Toplantı yapıldı",
            StreamNoteType.TASK_COMPLETED: "Görev tamamlandı",
        }
        
        return type_messages.get(self.type, f"{self.type} aktivitesi")


class PostRequest(EspoCRMBaseModel):
    """Stream'e post yapmak için request modeli."""
    
    type: str = Field(
        default="Post",
        description="Note türü (her zaman 'Post')"
    )
    
    post: str = Field(
        description="Post içeriği (HTML formatında)",
        min_length=1,
        max_length=10000
    )
    
    parent_id: str = Field(
        description="Bağlı entity ID'si",
        alias="parentId",
        min_length=17,
        max_length=17
    )
    
    parent_type: str = Field(
        description="Bağlı entity türü",
        alias="parentType",
        min_length=1,
        max_length=100
    )
    
    # Attachment support
    attachments_ids: Optional[List[str]] = Field(
        default=None,
        description="Attachment ID'leri",
        alias="attachmentsIds"
    )
    
    # Visibility options
    is_internal: Optional[bool] = Field(
        default=None,
        description="Internal note mu",
        alias="isInternal"
    )
    
    teams_ids: Optional[List[str]] = Field(
        default=None,
        description="Görünür team ID'leri",
        alias="teamsIds"
    )
    
    portal_id: Optional[str] = Field(
        default=None,
        description="Portal ID'si",
        alias="portalId"
    )
    
    @field_validator("parent_id")
    @classmethod
    def validate_parent_id(cls, v: str) -> str:
        """Parent ID formatını doğrular."""
        if not isinstance(v, str):
            raise ValueError("Parent ID string formatında olmalıdır")
        
        if len(v) != 17:
            raise ValueError("EspoCRM ID'si 17 karakter uzunluğunda olmalıdır")
        
        if not v.isalnum():
            raise ValueError("EspoCRM ID'si sadece alphanumeric karakterler içermelidir")
        
        return v
    
    @field_validator("attachments_ids")
    @classmethod
    def validate_attachments_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Attachment ID'lerini doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("Attachments IDs liste formatında olmalıdır")
        
        if len(v) > 10:  # Maksimum 10 attachment
            raise ValueError("Maksimum 10 attachment eklenebilir")
        
        for i, attachment_id in enumerate(v):
            if not isinstance(attachment_id, str):
                raise ValueError(f"Attachment ID[{i}] string formatında olmalıdır")
            
            if len(attachment_id) != 17:
                raise ValueError(f"Attachment ID[{i}] 17 karakter uzunluğunda olmalıdır")
            
            if not attachment_id.isalnum():
                raise ValueError(f"Attachment ID[{i}] sadece alphanumeric karakterler içermelidir")
        
        # Duplicate kontrolü
        if len(set(v)) != len(v):
            raise ValueError("Duplicate attachment ID'leri olamaz")
        
        return v
    
    @field_validator("teams_ids")
    @classmethod
    def validate_teams_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Team ID'lerini doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("Teams IDs liste formatında olmalıdır")
        
        for i, team_id in enumerate(v):
            if not isinstance(team_id, str):
                raise ValueError(f"Team ID[{i}] string formatında olmalıdır")
            
            if len(team_id) != 17:
                raise ValueError(f"Team ID[{i}] 17 karakter uzunluğunda olmalıdır")
            
            if not team_id.isalnum():
                raise ValueError(f"Team ID[{i}] sadece alphanumeric karakterler içermelidir")
        
        return v
    
    @field_validator("post")
    @classmethod
    def validate_post_content(cls, v: str) -> str:
        """Post içeriğini doğrular."""
        if not v or not v.strip():
            raise ValueError("Post içeriği boş olamaz")
        
        # Basit HTML validation (güvenlik için)
        dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<form']
        v_lower = v.lower()
        
        for tag in dangerous_tags:
            if tag in v_lower:
                raise ValueError(f"Güvenlik nedeniyle {tag} tag'i kullanılamaz")
        
        return v.strip()
    
    def has_attachments(self) -> bool:
        """Attachment'ı var mı kontrol eder."""
        return bool(self.attachments_ids)
    
    def get_attachment_count(self) -> int:
        """Attachment sayısını döndürür."""
        return len(self.attachments_ids) if self.attachments_ids else 0
    
    def is_team_restricted(self) -> bool:
        """Team kısıtlaması var mı kontrol eder."""
        return bool(self.teams_ids)
    
    def is_portal_post(self) -> bool:
        """Portal post'u mu kontrol eder."""
        return bool(self.portal_id)
    
    def to_api_dict(self) -> Dict[str, Any]:
        """API request için dict formatına çevirir."""
        data: Dict[str, Any] = {
            "type": self.type,
            "post": self.post,
            "parentType": self.parent_type,
            "parentId": self.parent_id
        }
        
        if self.attachments_ids:
            data["attachmentsIds"] = self.attachments_ids
        
        if self.is_internal is not None:
            data["isInternal"] = self.is_internal
        
        if self.teams_ids:
            data["teamsIds"] = self.teams_ids
        
        if self.portal_id:
            data["portalId"] = self.portal_id
        
        return data


class StreamListRequest(EspoCRMBaseModel):
    """Stream listesi için request modeli."""
    
    # Pagination
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
    
    # Filtering
    after: Optional[str] = Field(
        default=None,
        description="Bu tarihten sonraki kayıtlar (ISO format)"
    )
    
    filter: Optional[str] = Field(
        default=None,
        description="Stream filter türü"
    )
    
    # Entity-specific stream
    entity_type: Optional[str] = Field(
        default=None,
        description="Belirli entity türü için stream",
        alias="entityType"
    )
    
    entity_id: Optional[str] = Field(
        default=None,
        description="Belirli entity ID'si için stream",
        alias="entityId"
    )
    
    # Note type filtering
    note_types: Optional[List[StreamNoteType]] = Field(
        default=None,
        description="Filtrelenecek note türleri",
        alias="noteTypes"
    )
    
    # User filtering
    user_id: Optional[str] = Field(
        default=None,
        description="Belirli kullanıcının aktiviteleri",
        alias="userId"
    )
    
    @field_validator("entity_id", "user_id")
    @classmethod
    def validate_id_format(cls, v: Optional[str]) -> Optional[str]:
        """ID formatını doğrular."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("ID string formatında olmalıdır")
        
        if len(v) != 17:
            raise ValueError("EspoCRM ID'si 17 karakter uzunluğunda olmalıdır")
        
        if not v.isalnum():
            raise ValueError("EspoCRM ID'si sadece alphanumeric karakterler içermelidir")
        
        return v
    
    @field_validator("after")
    @classmethod
    def validate_after_date(cls, v: Optional[str]) -> Optional[str]:
        """After tarihini doğrular."""
        if v is None:
            return v
        
        try:
            # ISO format kontrolü
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError("After tarihi ISO format'ında olmalıdır")
    
    @model_validator(mode='after')
    def validate_entity_params(self):
        """Entity parametrelerini doğrular."""
        # Entity stream için hem type hem ID gerekli
        if self.entity_type and not self.entity_id:
            raise ValueError("Entity type belirtildiğinde entity ID de gereklidir")
        
        if self.entity_id and not self.entity_type:
            raise ValueError("Entity ID belirtildiğinde entity type da gereklidir")
        
        return self
    
    def is_entity_stream(self) -> bool:
        """Entity-specific stream mi kontrol eder."""
        return bool(self.entity_type and self.entity_id)
    
    def is_user_stream(self) -> bool:
        """User-specific stream mi kontrol eder."""
        return bool(self.user_id)
    
    def is_filtered(self) -> bool:
        """Filtrelenmiş stream mi kontrol eder."""
        return bool(self.filter or self.note_types or self.after)
    
    def to_query_params(self) -> Dict[str, Any]:
        """Query parameters'a çevirir."""
        params: Dict[str, Any] = {
            "offset": self.offset,
            "maxSize": self.max_size,
        }
        
        if self.after:
            params["after"] = self.after
        
        if self.filter:
            params["filter"] = self.filter
        
        if self.note_types:
            params["noteTypes"] = [note_type.value for note_type in self.note_types]
        
        if self.user_id:
            params["userId"] = self.user_id
        
        return params


class SubscriptionRequest(EspoCRMBaseModel):
    """Entity subscription (follow/unfollow) için request modeli."""
    
    entity_type: str = Field(
        description="Entity türü",
        min_length=1,
        max_length=100
    )
    
    entity_id: str = Field(
        description="Entity ID'si",
        min_length=17,
        max_length=17
    )
    
    @field_validator("entity_id")
    @classmethod
    def validate_entity_id(cls, v: str) -> str:
        """Entity ID formatını doğrular."""
        if not isinstance(v, str):
            raise ValueError("Entity ID string formatında olmalıdır")
        
        if len(v) != 17:
            raise ValueError("EspoCRM ID'si 17 karakter uzunluğunda olmalıdır")
        
        if not v.isalnum():
            raise ValueError("EspoCRM ID'si sadece alphanumeric karakterler içermelidir")
        
        return v
    
    def get_endpoint(self) -> str:
        """API endpoint'ini döndürür."""
        return f"{self.entity_type}/{self.entity_id}/subscription"


# Factory functions
def create_post_request(
    parent_type: str,
    parent_id: str,
    post: str,
    attachments_ids: Optional[List[str]] = None,
    is_internal: Optional[bool] = None,
    teams_ids: Optional[List[str]] = None,
    portal_id: Optional[str] = None
) -> PostRequest:
    """PostRequest oluşturur.
    
    Args:
        parent_type: Bağlı entity türü
        parent_id: Bağlı entity ID'si
        post: Post içeriği
        attachments_ids: Attachment ID'leri
        is_internal: Internal note mu
        teams_ids: Görünür team ID'leri
        portal_id: Portal ID'si
        
    Returns:
        PostRequest instance'ı
    """
    return PostRequest(
        parentType=parent_type,
        parentId=parent_id,
        post=post,
        attachmentsIds=attachments_ids,
        isInternal=is_internal,
        teamsIds=teams_ids,
        portalId=portal_id
    )


def create_stream_list_request(
    offset: int = 0,
    max_size: int = 20,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    after: Optional[str] = None,
    filter: Optional[str] = None,
    note_types: Optional[List[StreamNoteType]] = None,
    user_id: Optional[str] = None
) -> StreamListRequest:
    """StreamListRequest oluşturur.
    
    Args:
        offset: Başlangıç offset'i
        max_size: Maksimum kayıt sayısı
        entity_type: Entity türü
        entity_id: Entity ID'si
        after: Bu tarihten sonraki kayıtlar
        filter: Stream filter türü
        note_types: Filtrelenecek note türleri
        user_id: Kullanıcı ID'si
        
    Returns:
        StreamListRequest instance'ı
    """
    return StreamListRequest(
        offset=offset,
        maxSize=max_size,
        entityType=entity_type,
        entityId=entity_id,
        after=after,
        filter=filter,
        noteTypes=note_types,
        userId=user_id
    )


def create_subscription_request(
    entity_type: str,
    entity_id: str
) -> SubscriptionRequest:
    """SubscriptionRequest oluşturur.
    
    Args:
        entity_type: Entity türü
        entity_id: Entity ID'si
        
    Returns:
        SubscriptionRequest instance'ı
    """
    return SubscriptionRequest(
        entity_type=entity_type,
        entity_id=entity_id
    )


# Alias'lar - backward compatibility için
StreamPost = PostRequest
StreamUpdate = StreamNote


# Export edilecek sınıflar ve fonksiyonlar
__all__ = [
    # Enums
    "StreamNoteType",
    
    # Models
    "StreamNoteData",
    "StreamNote",
    "PostRequest",
    "StreamListRequest",
    "SubscriptionRequest",
    
    # Aliases
    "StreamPost",
    "StreamUpdate",
    
    # Factory functions
    "create_post_request",
    "create_stream_list_request",
    "create_subscription_request",
]