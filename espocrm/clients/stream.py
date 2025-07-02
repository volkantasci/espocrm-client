"""EspoCRM Stream Client.

Bu modül EspoCRM Stream API operasyonları için client sınıfını içerir.
Stream listeleme, post oluşturma, follow/unfollow işlemleri sağlar.
"""

import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

from ..models.base import EspoCRMListResponse
from ..models.stream import (
    StreamNote,
    PostRequest,
    StreamListRequest,
    SubscriptionRequest,
    StreamNoteType,
    create_post_request,
    create_stream_list_request,
    create_subscription_request,
)
from ..exceptions import EspoCRMError, EspoCRMValidationError
from ..utils.helpers import timing_decorator


class StreamClient:
    """EspoCRM Stream operasyonları için client sınıfı.
    
    Bu sınıf EspoCRM Stream API'si ile etkileşim sağlar:
    - User stream listeleme
    - Entity stream listeleme
    - Stream'e post yapma
    - Entity follow/unfollow
    - Stream filtering ve pagination
    """
    
    def __init__(self, main_client):
        """Stream client'ını başlatır.
        
        Args:
            main_client: Ana EspoCRM client instance'ı
        """
        self.client = main_client
        self.logger = main_client.logger
    
    @property
    def base_url(self) -> str:
        """Ana client'tan base_url'e erişim sağlar."""
        return self.client.base_url
    
    @property
    def api_version(self) -> str:
        """Ana client'tan api_version'a erişim sağlar."""
        return self.client.api_version
    
    @timing_decorator
    def list_user_stream(
        self,
        offset: int = 0,
        max_size: int = 20,
        after: Optional[str] = None,
        filter: Optional[str] = None,
        note_types: Optional[List[StreamNoteType]] = None,
        user_id: Optional[str] = None
    ) -> List[StreamNote]:
        """Kullanıcı stream'ini listeler.
        
        Args:
            offset: Başlangıç offset'i
            max_size: Maksimum kayıt sayısı
            after: Bu tarihten sonraki kayıtlar (ISO format)
            filter: Stream filter türü
            note_types: Filtrelenecek note türleri
            user_id: Belirli kullanıcının aktiviteleri
            
        Returns:
            Stream note'ları listesi
            
        Raises:
            EspoCRMError: API hatası
            EspoCRMValidationError: Validation hatası
        """
        try:
            # Request oluştur
            request = create_stream_list_request(
                offset=offset,
                max_size=max_size,
                after=after,
                filter=filter,
                note_types=note_types,
                user_id=user_id
            )
            
            # Query parameters hazırla
            params = request.to_query_params()
            
            self.logger.info(
                "Listing user stream",
                offset=offset,
                max_size=max_size,
                filter=filter,
                user_id=user_id
            )
            
            # API request
            response_data = self.client.get("Stream", params=params)
            
            # Response parse et
            if isinstance(response_data, dict) and "list" in response_data:
                # List response formatı
                stream_notes = []
                for note_data in response_data["list"]:
                    stream_note = StreamNote.from_api_response(note_data)
                    stream_notes.append(stream_note)
                
                self.logger.info(
                    "User stream listed successfully",
                    count=len(stream_notes),
                    total=response_data.get("total", len(stream_notes))
                )
                
                return stream_notes
            else:
                # Direct list formatı
                stream_notes = []
                if isinstance(response_data, list):
                    for note_data in response_data:
                        stream_note = StreamNote.from_api_response(note_data)
                        stream_notes.append(stream_note)
                
                self.logger.info(
                    "User stream listed successfully",
                    count=len(stream_notes)
                )
                
                return stream_notes
                
        except Exception as e:
            self.logger.error(
                "Failed to list user stream",
                error=str(e),
                offset=offset,
                max_size=max_size
            )
            
            if isinstance(e, EspoCRMError):
                raise
            else:
                raise EspoCRMError(f"User stream listeleme hatası: {str(e)}")
    
    @timing_decorator
    def list_entity_stream(
        self,
        entity_type: str,
        entity_id: str,
        offset: int = 0,
        max_size: int = 20,
        after: Optional[str] = None,
        filter: Optional[str] = None,
        note_types: Optional[List[StreamNoteType]] = None
    ) -> List[StreamNote]:
        """Entity stream'ini listeler.
        
        Args:
            entity_type: Entity türü
            entity_id: Entity ID'si
            offset: Başlangıç offset'i
            max_size: Maksimum kayıt sayısı
            after: Bu tarihten sonraki kayıtlar (ISO format)
            filter: Stream filter türü
            note_types: Filtrelenecek note türleri
            
        Returns:
            Stream note'ları listesi
            
        Raises:
            EspoCRMError: API hatası
            EspoCRMValidationError: Validation hatası
        """
        try:
            # Request oluştur
            request = create_stream_list_request(
                offset=offset,
                max_size=max_size,
                entity_type=entity_type,
                entity_id=entity_id,
                after=after,
                filter=filter,
                note_types=note_types
            )
            
            # Query parameters hazırla
            params = request.to_query_params()
            
            # Endpoint oluştur
            endpoint = f"{entity_type}/{entity_id}/stream"
            
            self.logger.info(
                "Listing entity stream",
                entity_type=entity_type,
                entity_id=entity_id,
                offset=offset,
                max_size=max_size,
                filter=filter
            )
            
            # API request
            response_data = self.client.get(endpoint, params=params)
            
            # Response parse et
            if isinstance(response_data, dict) and "list" in response_data:
                # List response formatı
                stream_notes = []
                for note_data in response_data["list"]:
                    stream_note = StreamNote.from_api_response(note_data)
                    stream_notes.append(stream_note)
                
                self.logger.info(
                    "Entity stream listed successfully",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    count=len(stream_notes),
                    total=response_data.get("total", len(stream_notes))
                )
                
                return stream_notes
            else:
                # Direct list formatı
                stream_notes = []
                if isinstance(response_data, list):
                    for note_data in response_data:
                        stream_note = StreamNote.from_api_response(note_data)
                        stream_notes.append(stream_note)
                
                self.logger.info(
                    "Entity stream listed successfully",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    count=len(stream_notes)
                )
                
                return stream_notes
                
        except Exception as e:
            self.logger.error(
                "Failed to list entity stream",
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e),
                offset=offset,
                max_size=max_size
            )
            
            if isinstance(e, EspoCRMError):
                raise
            else:
                raise EspoCRMError(f"Entity stream listeleme hatası: {str(e)}")
    
    @timing_decorator
    def post_to_stream(
        self,
        parent_type: str,
        parent_id: str,
        post: str,
        attachments_ids: Optional[List[str]] = None,
        is_internal: Optional[bool] = None,
        teams_ids: Optional[List[str]] = None,
        portal_id: Optional[str] = None
    ) -> StreamNote:
        """Stream'e post yapar.
        
        Args:
            parent_type: Bağlı entity türü
            parent_id: Bağlı entity ID'si
            post: Post içeriği (HTML formatında)
            attachments_ids: Attachment ID'leri
            is_internal: Internal note mu
            teams_ids: Görünür team ID'leri
            portal_id: Portal ID'si
            
        Returns:
            Oluşturulan stream note
            
        Raises:
            EspoCRMError: API hatası
            EspoCRMValidationError: Validation hatası
        """
        try:
            # Request oluştur
            post_request = create_post_request(
                parent_type=parent_type,
                parent_id=parent_id,
                post=post,
                attachments_ids=attachments_ids,
                is_internal=is_internal,
                teams_ids=teams_ids,
                portal_id=portal_id
            )
            
            # Request data hazırla
            request_data = post_request.to_api_dict()
            
            self.logger.info(
                "Creating stream post",
                parent_type=parent_type,
                parent_id=parent_id,
                has_attachments=bool(attachments_ids),
                is_internal=is_internal
            )
            
            # API request
            response_data = self.client.post("Note", data=request_data)
            
            # Response'u StreamNote'a çevir
            stream_note = StreamNote.from_api_response(response_data)
            
            self.logger.info(
                "Stream post created successfully",
                note_id=stream_note.id,
                parent_type=parent_type,
                parent_id=parent_id
            )
            
            return stream_note
            
        except Exception as e:
            self.logger.error(
                "Failed to create stream post",
                parent_type=parent_type,
                parent_id=parent_id,
                error=str(e)
            )
            
            if isinstance(e, EspoCRMError):
                raise
            else:
                raise EspoCRMError(f"Stream post oluşturma hatası: {str(e)}")
    
    @timing_decorator
    def follow_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> bool:
        """Entity'yi takip eder.
        
        Args:
            entity_type: Entity türü
            entity_id: Entity ID'si
            
        Returns:
            İşlem başarılı ise True
            
        Raises:
            EspoCRMError: API hatası
            EspoCRMValidationError: Validation hatası
        """
        try:
            # Request oluştur
            subscription_request = create_subscription_request(
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            # Endpoint oluştur
            endpoint = subscription_request.get_endpoint()
            
            self.logger.info(
                "Following entity",
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            # API request (PUT)
            response_data = self.client.put(endpoint)
            
            # Success kontrolü
            success = response_data.get("success", True)
            
            if success:
                self.logger.info(
                    "Entity followed successfully",
                    entity_type=entity_type,
                    entity_id=entity_id
                )
            else:
                self.logger.warning(
                    "Entity follow operation returned false",
                    entity_type=entity_type,
                    entity_id=entity_id
                )
            
            return success
            
        except Exception as e:
            self.logger.error(
                "Failed to follow entity",
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e)
            )
            
            if isinstance(e, EspoCRMError):
                raise
            else:
                raise EspoCRMError(f"Entity takip etme hatası: {str(e)}")
    
    @timing_decorator
    def unfollow_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> bool:
        """Entity takibini bırakır.
        
        Args:
            entity_type: Entity türü
            entity_id: Entity ID'si
            
        Returns:
            İşlem başarılı ise True
            
        Raises:
            EspoCRMError: API hatası
            EspoCRMValidationError: Validation hatası
        """
        try:
            # Request oluştur
            subscription_request = create_subscription_request(
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            # Endpoint oluştur
            endpoint = subscription_request.get_endpoint()
            
            self.logger.info(
                "Unfollowing entity",
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            # API request (DELETE)
            response_data = self.client.delete(endpoint)
            
            # Success kontrolü
            success = response_data.get("success", True)
            
            if success:
                self.logger.info(
                    "Entity unfollowed successfully",
                    entity_type=entity_type,
                    entity_id=entity_id
                )
            else:
                self.logger.warning(
                    "Entity unfollow operation returned false",
                    entity_type=entity_type,
                    entity_id=entity_id
                )
            
            return success
            
        except Exception as e:
            self.logger.error(
                "Failed to unfollow entity",
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e)
            )
            
            if isinstance(e, EspoCRMError):
                raise
            else:
                raise EspoCRMError(f"Entity takip bırakma hatası: {str(e)}")
    
    @timing_decorator
    def is_following_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> bool:
        """Entity'nin takip edilip edilmediğini kontrol eder.
        
        Args:
            entity_type: Entity türü
            entity_id: Entity ID'si
            
        Returns:
            Takip ediliyor ise True
            
        Raises:
            EspoCRMError: API hatası
        """
        try:
            # Request oluştur
            subscription_request = create_subscription_request(
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            # Endpoint oluştur
            endpoint = subscription_request.get_endpoint()
            
            self.logger.debug(
                "Checking entity follow status",
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            # API request (GET)
            response_data = self.client.get(endpoint)
            
            # Follow status kontrolü
            is_following = response_data.get("isFollowing", False)
            
            self.logger.debug(
                "Entity follow status checked",
                entity_type=entity_type,
                entity_id=entity_id,
                is_following=is_following
            )
            
            return is_following
            
        except Exception as e:
            self.logger.error(
                "Failed to check entity follow status",
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e)
            )
            
            if isinstance(e, EspoCRMError):
                raise
            else:
                raise EspoCRMError(f"Entity takip durumu kontrol hatası: {str(e)}")
    
    @timing_decorator
    def get_stream_note(
        self,
        note_id: str
    ) -> StreamNote:
        """Belirli bir stream note'u getirir.
        
        Args:
            note_id: Note ID'si
            
        Returns:
            Stream note
            
        Raises:
            EspoCRMError: API hatası
        """
        try:
            self.logger.debug(
                "Getting stream note",
                note_id=note_id
            )
            
            # API request
            response_data = self.client.get(f"Note/{note_id}")
            
            # Response'u StreamNote'a çevir
            stream_note = StreamNote.from_api_response(response_data)
            
            self.logger.debug(
                "Stream note retrieved successfully",
                note_id=note_id,
                note_type=stream_note.type
            )
            
            return stream_note
            
        except Exception as e:
            self.logger.error(
                "Failed to get stream note",
                note_id=note_id,
                error=str(e)
            )
            
            if isinstance(e, EspoCRMError):
                raise
            else:
                raise EspoCRMError(f"Stream note getirme hatası: {str(e)}")
    
    @timing_decorator
    def delete_stream_note(
        self,
        note_id: str
    ) -> bool:
        """Stream note'u siler.
        
        Args:
            note_id: Note ID'si
            
        Returns:
            İşlem başarılı ise True
            
        Raises:
            EspoCRMError: API hatası
        """
        try:
            self.logger.info(
                "Deleting stream note",
                note_id=note_id
            )
            
            # API request
            response_data = self.client.delete(f"Note/{note_id}")
            
            # Success kontrolü
            success = response_data.get("success", True)
            
            if success:
                self.logger.info(
                    "Stream note deleted successfully",
                    note_id=note_id
                )
            else:
                self.logger.warning(
                    "Stream note delete operation returned false",
                    note_id=note_id
                )
            
            return success
            
        except Exception as e:
            self.logger.error(
                "Failed to delete stream note",
                note_id=note_id,
                error=str(e)
            )
            
            if isinstance(e, EspoCRMError):
                raise
            else:
                raise EspoCRMError(f"Stream note silme hatası: {str(e)}")
    
    # Convenience methods
    def post_to_account(
        self,
        account_id: str,
        post: str,
        **kwargs
    ) -> StreamNote:
        """Account'a post yapar."""
        return self.post_to_stream("Account", account_id, post, **kwargs)
    
    def post_to_contact(
        self,
        contact_id: str,
        post: str,
        **kwargs
    ) -> StreamNote:
        """Contact'a post yapar."""
        return self.post_to_stream("Contact", contact_id, post, **kwargs)
    
    def post_to_opportunity(
        self,
        opportunity_id: str,
        post: str,
        **kwargs
    ) -> StreamNote:
        """Opportunity'ye post yapar."""
        return self.post_to_stream("Opportunity", opportunity_id, post, **kwargs)
    
    def post_to_lead(
        self,
        lead_id: str,
        post: str,
        **kwargs
    ) -> StreamNote:
        """Lead'e post yapar."""
        return self.post_to_stream("Lead", lead_id, post, **kwargs)
    
    def get_account_stream(
        self,
        account_id: str,
        **kwargs
    ) -> List[StreamNote]:
        """Account stream'ini getirir."""
        return self.list_entity_stream("Account", account_id, **kwargs)
    
    def get_contact_stream(
        self,
        contact_id: str,
        **kwargs
    ) -> List[StreamNote]:
        """Contact stream'ini getirir."""
        return self.list_entity_stream("Contact", contact_id, **kwargs)
    
    def get_opportunity_stream(
        self,
        opportunity_id: str,
        **kwargs
    ) -> List[StreamNote]:
        """Opportunity stream'ini getirir."""
        return self.list_entity_stream("Opportunity", opportunity_id, **kwargs)
    
    def get_lead_stream(
        self,
        lead_id: str,
        **kwargs
    ) -> List[StreamNote]:
        """Lead stream'ini getirir."""
        return self.list_entity_stream("Lead", lead_id, **kwargs)
    
    def follow_account(self, account_id: str) -> bool:
        """Account'u takip eder."""
        return self.follow_entity("Account", account_id)
    
    def follow_contact(self, contact_id: str) -> bool:
        """Contact'ı takip eder."""
        return self.follow_entity("Contact", contact_id)
    
    def follow_opportunity(self, opportunity_id: str) -> bool:
        """Opportunity'yi takip eder."""
        return self.follow_entity("Opportunity", opportunity_id)
    
    def follow_lead(self, lead_id: str) -> bool:
        """Lead'i takip eder."""
        return self.follow_entity("Lead", lead_id)
    
    def unfollow_account(self, account_id: str) -> bool:
        """Account takibini bırakır."""
        return self.unfollow_entity("Account", account_id)
    
    def unfollow_contact(self, contact_id: str) -> bool:
        """Contact takibini bırakır."""
        return self.unfollow_entity("Contact", contact_id)
    
    def unfollow_opportunity(self, opportunity_id: str) -> bool:
        """Opportunity takibini bırakır."""
        return self.unfollow_entity("Opportunity", opportunity_id)
    
    def unfollow_lead(self, lead_id: str) -> bool:
        """Lead takibini bırakır."""
        return self.unfollow_entity("Lead", lead_id)


# Export edilecek sınıflar
__all__ = [
    "StreamClient",
]