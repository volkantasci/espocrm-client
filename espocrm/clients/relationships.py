"""EspoCRM Relationship operasyonları client'ı.

Bu modül EspoCRM API'nin relationship operasyonlarını gerçekleştiren
RelationshipClient sınıfını içerir. Entity'ler arası ilişki yönetimi,
link/unlink operasyonları ve related records listeleme sağlar.
"""

import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

from ..exceptions import EspoCRMError, EspoCRMValidationError
from ..models.entities import EntityRecord, create_entity
from ..models.search import SearchParams
from ..models.requests import (
    LinkRequest,
    UnlinkRequest,
    RelationshipListRequest,
    create_link_request,
    create_unlink_request,
    create_relationship_list_request
)
from ..models.responses import (
    EntityResponse,
    ListResponse,
    BulkOperationResult,
    parse_entity_response,
    parse_list_response
)
from ..utils.helpers import timing_decorator
from ..logging import get_logger


class RelationshipOperationResult:
    """Relationship operasyon sonucu."""
    
    def __init__(
        self,
        success: bool,
        operation_type: str,
        entity_type: str,
        entity_id: str,
        link: str,
        target_count: int = 0,
        successful_count: int = 0,
        failed_count: int = 0,
        errors: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.operation_type = operation_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.link = link
        self.target_count = target_count
        self.successful_count = successful_count
        self.failed_count = failed_count
        self.errors = errors or []
        self.data = data or {}
    
    def get_success_rate(self) -> float:
        """Başarı oranını döndürür."""
        if self.target_count == 0:
            return 100.0 if self.success else 0.0
        
        return (self.successful_count / self.target_count) * 100.0
    
    def has_errors(self) -> bool:
        """Hata var mı kontrol eder."""
        return len(self.errors) > 0
    
    def get_summary(self) -> str:
        """Operasyon özetini döndürür."""
        if self.target_count > 0:
            return (
                f"{self.operation_type} operation: "
                f"{self.successful_count}/{self.target_count} successful "
                f"({self.get_success_rate():.1f}%)"
            )
        else:
            return f"{self.operation_type} operation: {'Success' if self.success else 'Failed'}"


class RelationshipClient:
    """EspoCRM Relationship operasyonları için client sınıfı.
    
    Bu sınıf EspoCRM API'nin relationship operasyonlarını sağlar:
    - List related records (GET {entityType}/{id}/{link})
    - Link records (POST {entityType}/{id}/{link})
    - Unlink records (DELETE {entityType}/{id}/{link})
    - Mass relate operations
    - Relationship metadata operations
    """
    
    def __init__(self, main_client):
        """Relationship client'ı başlatır.
        
        Args:
            main_client: Ana EspoCRM client instance'ı
        """
        self.client = main_client
        self.logger = get_logger(f"{__name__}.RelationshipClient")
        
        # Base client özelliklerini proxy et
        self.base_url = getattr(main_client, 'base_url', None)
        self.api_version = getattr(main_client, 'api_version', None)
        self.entities = getattr(main_client, 'entities', None)
    
    @timing_decorator
    def list_related(
        self,
        entity_type: str,
        entity_id: str,
        link: str,
        search_params: Optional[SearchParams] = None,
        offset: Optional[int] = None,
        max_size: Optional[int] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = None,
        select: Optional[List[str]] = None,
        where: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ListResponse:
        """İlişkili kayıtları listeler.
        
        Args:
            entity_type: Ana entity türü
            entity_id: Ana entity ID'si
            link: Relationship link adı
            search_params: Arama parametreleri (SearchParams instance'ı)
            offset: Başlangıç offset'i
            max_size: Maksimum kayıt sayısı
            order_by: Sıralama field'ı
            order: Sıralama yönü ('asc' veya 'desc')
            select: Seçilecek field'lar
            where: Where clause'ları
            **kwargs: Ek request parametreleri
            
        Returns:
            İlişkili kayıtlar listesi
            
        Raises:
            EspoCRMValidationError: Validation hatası
            EspoCRMError: API hatası
            
        Example:
            >>> # Account'un Contact'larını listele
            >>> response = relationship_client.list_related(
            ...     "Account", "507f1f77bcf86cd799439011", "contacts",
            ...     max_size=20, order_by="name"
            ... )
            >>> contacts = response.get_entities()
        """
        self.logger.info(
            "Listing related records",
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            has_search_params=search_params is not None
        )
        
        # Request oluştur
        list_request = create_relationship_list_request(
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            search_params=search_params,
            offset=offset,
            max_size=max_size,
            order_by=order_by,
            order=order,
            select=select,
            where=where
        )
        
        try:
            # Query parameters oluştur
            params = list_request.to_query_params()
            
            # API request
            endpoint = list_request.get_endpoint()
            response_data = self.client.get(endpoint, params=params, **kwargs)
            
            # Response parse et
            list_response = parse_list_response(response_data, entity_type)
            
            self.logger.info(
                "Related records listed successfully",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                total=list_response.total,
                count=len(list_response.list)
            )
            
            return list_response
            
        except Exception as e:
            self.logger.error(
                "Failed to list related records",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def link_single(
        self,
        entity_type: str,
        entity_id: str,
        link: str,
        target_id: str,
        foreign_id: Optional[str] = None,
        **kwargs
    ) -> RelationshipOperationResult:
        """Tek kayıt ilişkilendirir.
        
        Args:
            entity_type: Ana entity türü
            entity_id: Ana entity ID'si
            link: Relationship link adı
            target_id: İlişkilendirilecek kayıt ID'si
            foreign_id: Foreign entity ID (opsiyonel)
            **kwargs: Ek request parametreleri
            
        Returns:
            Operasyon sonucu
            
        Example:
            >>> # Account'a Contact ilişkilendir
            >>> result = relationship_client.link_single(
            ...     "Account", "507f1f77bcf86cd799439011", 
            ...     "contacts", "507f1f77bcf86cd799439012"
            ... )
            >>> print(f"Success: {result.success}")
        """
        self.logger.info(
            "Linking single record",
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            target_id=target_id
        )
        
        # Request oluştur
        link_request = create_link_request(
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            target_id=target_id,
            foreign_id=foreign_id
        )
        
        try:
            # API request
            endpoint = link_request.get_endpoint()
            request_data = link_request.to_api_dict()
            
            response_data = self.client.post(endpoint, data=request_data, **kwargs)
            
            # Sonuç oluştur
            result = RelationshipOperationResult(
                success=True,
                operation_type="link_single",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=1,
                successful_count=1,
                failed_count=0,
                data=response_data
            )
            
            self.logger.info(
                "Single record linked successfully",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_id=target_id
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to link single record",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_id=target_id,
                error=str(e)
            )
            
            # Hata sonucu oluştur
            result = RelationshipOperationResult(
                success=False,
                operation_type="link_single",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=1,
                successful_count=0,
                failed_count=1,
                errors=[str(e)]
            )
            
            return result
    
    @timing_decorator
    def link_multiple(
        self,
        entity_type: str,
        entity_id: str,
        link: str,
        target_ids: List[str],
        foreign_id: Optional[str] = None,
        **kwargs
    ) -> RelationshipOperationResult:
        """Çoklu kayıt ilişkilendirir.
        
        Args:
            entity_type: Ana entity türü
            entity_id: Ana entity ID'si
            link: Relationship link adı
            target_ids: İlişkilendirilecek kayıt ID'leri
            foreign_id: Foreign entity ID (opsiyonel)
            **kwargs: Ek request parametreleri
            
        Returns:
            Operasyon sonucu
            
        Example:
            >>> # Account'a birden fazla Contact ilişkilendir
            >>> target_ids = ["507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"]
            >>> result = relationship_client.link_multiple(
            ...     "Account", "507f1f77bcf86cd799439011", 
            ...     "contacts", target_ids
            ... )
        """
        self.logger.info(
            "Linking multiple records",
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            target_count=len(target_ids)
        )
        
        # Request oluştur
        link_request = create_link_request(
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            target_ids=target_ids,
            foreign_id=foreign_id
        )
        
        try:
            # API request
            endpoint = link_request.get_endpoint()
            request_data = link_request.to_api_dict()
            
            response_data = self.client.post(endpoint, data=request_data, **kwargs)
            
            # Sonuç oluştur
            result = RelationshipOperationResult(
                success=True,
                operation_type="link_multiple",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=len(target_ids),
                successful_count=len(target_ids),
                failed_count=0,
                data=response_data
            )
            
            self.logger.info(
                "Multiple records linked successfully",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=len(target_ids)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to link multiple records",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=len(target_ids),
                error=str(e)
            )
            
            # Hata sonucu oluştur
            result = RelationshipOperationResult(
                success=False,
                operation_type="link_multiple",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=len(target_ids),
                successful_count=0,
                failed_count=len(target_ids),
                errors=[str(e)]
            )
            
            return result
    
    @timing_decorator
    def mass_relate(
        self,
        entity_type: str,
        entity_id: str,
        link: str,
        where: List[Dict[str, Any]],
        foreign_id: Optional[str] = None,
        **kwargs
    ) -> RelationshipOperationResult:
        """Mass relate operasyonu gerçekleştirir.
        
        Args:
            entity_type: Ana entity türü
            entity_id: Ana entity ID'si
            link: Relationship link adı
            where: Search criteria
            foreign_id: Foreign entity ID (opsiyonel)
            **kwargs: Ek request parametreleri
            
        Returns:
            Operasyon sonucu
            
        Example:
            >>> # Account'a belirli kriterlere uyan tüm Contact'ları ilişkilendir
            >>> where = [{"type": "equals", "attribute": "accountId", "value": None}]
            >>> result = relationship_client.mass_relate(
            ...     "Account", "507f1f77bcf86cd799439011", 
            ...     "contacts", where
            ... )
        """
        self.logger.info(
            "Mass relating records",
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            where_count=len(where)
        )
        
        # Request oluştur
        link_request = create_link_request(
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            mass_relate=True,
            where=where,
            foreign_id=foreign_id
        )
        
        try:
            # API request
            endpoint = link_request.get_endpoint()
            request_data = link_request.to_api_dict()
            
            response_data = self.client.post(endpoint, data=request_data, **kwargs)
            
            # Response'dan etkilenen kayıt sayısını çıkar
            affected_count = response_data.get("count", 0)
            
            # Sonuç oluştur
            result = RelationshipOperationResult(
                success=True,
                operation_type="mass_relate",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=affected_count,
                successful_count=affected_count,
                failed_count=0,
                data=response_data
            )
            
            self.logger.info(
                "Mass relate completed successfully",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                affected_count=affected_count
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to mass relate records",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                error=str(e)
            )
            
            # Hata sonucu oluştur
            result = RelationshipOperationResult(
                success=False,
                operation_type="mass_relate",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=0,
                successful_count=0,
                failed_count=0,
                errors=[str(e)]
            )
            
            return result
    
    @timing_decorator
    def unlink_single(
        self,
        entity_type: str,
        entity_id: str,
        link: str,
        target_id: str,
        foreign_id: Optional[str] = None,
        **kwargs
    ) -> RelationshipOperationResult:
        """Tek kayıt ilişkisini kaldırır.
        
        Args:
            entity_type: Ana entity türü
            entity_id: Ana entity ID'si
            link: Relationship link adı
            target_id: İlişkisi kaldırılacak kayıt ID'si
            foreign_id: Foreign entity ID (opsiyonel)
            **kwargs: Ek request parametreleri
            
        Returns:
            Operasyon sonucu
        """
        self.logger.info(
            "Unlinking single record",
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            target_id=target_id
        )
        
        # Request oluştur
        unlink_request = create_unlink_request(
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            target_id=target_id,
            foreign_id=foreign_id
        )
        
        try:
            # API request
            endpoint = unlink_request.get_endpoint()
            request_data = unlink_request.to_api_dict()
            
            # DELETE request - data varsa query params olarak gönder
            if request_data:
                response_data = self.client.delete(endpoint, params=request_data, **kwargs)
            else:
                response_data = self.client.delete(endpoint, **kwargs)
            
            # Sonuç oluştur
            result = RelationshipOperationResult(
                success=True,
                operation_type="unlink_single",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=1,
                successful_count=1,
                failed_count=0,
                data=response_data
            )
            
            self.logger.info(
                "Single record unlinked successfully",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_id=target_id
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to unlink single record",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_id=target_id,
                error=str(e)
            )
            
            # Hata sonucu oluştur
            result = RelationshipOperationResult(
                success=False,
                operation_type="unlink_single",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=1,
                successful_count=0,
                failed_count=1,
                errors=[str(e)]
            )
            
            return result
    
    @timing_decorator
    def unlink_multiple(
        self,
        entity_type: str,
        entity_id: str,
        link: str,
        target_ids: List[str],
        foreign_id: Optional[str] = None,
        **kwargs
    ) -> RelationshipOperationResult:
        """Çoklu kayıt ilişkisini kaldırır.
        
        Args:
            entity_type: Ana entity türü
            entity_id: Ana entity ID'si
            link: Relationship link adı
            target_ids: İlişkisi kaldırılacak kayıt ID'leri
            foreign_id: Foreign entity ID (opsiyonel)
            **kwargs: Ek request parametreleri
            
        Returns:
            Operasyon sonucu
        """
        self.logger.info(
            "Unlinking multiple records",
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            target_count=len(target_ids)
        )
        
        # Request oluştur
        unlink_request = create_unlink_request(
            entity_type=entity_type,
            entity_id=entity_id,
            link=link,
            target_ids=target_ids,
            foreign_id=foreign_id
        )
        
        try:
            # API request
            endpoint = unlink_request.get_endpoint()
            request_data = unlink_request.to_api_dict()
            
            # DELETE request - data varsa query params olarak gönder
            if request_data:
                response_data = self.client.delete(endpoint, params=request_data, **kwargs)
            else:
                response_data = self.client.delete(endpoint, **kwargs)
            
            # Sonuç oluştur
            result = RelationshipOperationResult(
                success=True,
                operation_type="unlink_multiple",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=len(target_ids),
                successful_count=len(target_ids),
                failed_count=0,
                data=response_data
            )
            
            self.logger.info(
                "Multiple records unlinked successfully",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=len(target_ids)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to unlink multiple records",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=len(target_ids),
                error=str(e)
            )
            
            # Hata sonucu oluştur
            result = RelationshipOperationResult(
                success=False,
                operation_type="unlink_multiple",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=len(target_ids),
                successful_count=0,
                failed_count=len(target_ids),
                errors=[str(e)]
            )
            
            return result
    
    @timing_decorator
    def unlink_all(
        self,
        entity_type: str,
        entity_id: str,
        link: str,
        **kwargs
    ) -> RelationshipOperationResult:
        """Tüm ilişkileri kaldırır.
        
        Args:
            entity_type: Ana entity türü
            entity_id: Ana entity ID'si
            link: Relationship link adı
            **kwargs: Ek request parametreleri
            
        Returns:
            Operasyon sonucu
        """
        self.logger.info(
            "Unlinking all records",
            entity_type=entity_type,
            entity_id=entity_id,
            link=link
        )
        
        # Request oluştur
        unlink_request = create_unlink_request(
            entity_type=entity_type,
            entity_id=entity_id,
            link=link
        )
        
        try:
            # API request
            endpoint = unlink_request.get_endpoint()
            response_data = self.client.delete(endpoint, **kwargs)
            
            # Response'dan etkilenen kayıt sayısını çıkar
            affected_count = response_data.get("count", 0)
            
            # Sonuç oluştur
            result = RelationshipOperationResult(
                success=True,
                operation_type="unlink_all",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=affected_count,
                successful_count=affected_count,
                failed_count=0,
                data=response_data
            )
            
            self.logger.info(
                "All records unlinked successfully",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                affected_count=affected_count
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to unlink all records",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                error=str(e)
            )
            
            # Hata sonucu oluştur
            result = RelationshipOperationResult(
                success=False,
                operation_type="unlink_all",
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                target_count=0,
                successful_count=0,
                failed_count=0,
                errors=[str(e)]
            )
            
            return result
    
    def get_relationship_metadata(
        self,
        entity_type: str,
        link: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Relationship metadata'sını getirir.
        
        Args:
            entity_type: Entity türü
            link: Belirli bir link adı (opsiyonel)
            **kwargs: Ek request parametreleri
            
        Returns:
            Relationship metadata'sı
        """
        self.logger.info(
            "Getting relationship metadata",
            entity_type=entity_type,
            link=link
        )
        
        try:
            # Metadata endpoint'i
            if link:
                endpoint = f"Metadata/entityDefs/{entity_type}/links/{link}"
            else:
                endpoint = f"Metadata/entityDefs/{entity_type}/links"
            
            response_data = self.client.get(endpoint, **kwargs)
            
            self.logger.info(
                "Relationship metadata retrieved successfully",
                entity_type=entity_type,
                link=link
            )
            
            return response_data
            
        except Exception as e:
            self.logger.error(
                "Failed to get relationship metadata",
                entity_type=entity_type,
                link=link,
                error=str(e)
            )
            raise
    
    def check_relationship_exists(
        self,
        entity_type: str,
        entity_id: str,
        link: str,
        target_id: str,
        **kwargs
    ) -> bool:
        """İlişkinin var olup olmadığını kontrol eder.
        
        Args:
            entity_type: Ana entity türü
            entity_id: Ana entity ID'si
            link: Relationship link adı
            target_id: Hedef kayıt ID'si
            **kwargs: Ek request parametreleri
            
        Returns:
            İlişki var ise True
        """
        try:
            # İlişkili kayıtları listele ve hedef ID'yi ara
            response = self.list_related(
                entity_type=entity_type,
                entity_id=entity_id,
                link=link,
                select=["id"],
                max_size=1000,  # Büyük sayı - tüm ilişkileri kontrol et
                **kwargs
            )
            
            # Hedef ID'yi ara
            target_ids = response.get_ids()
            return target_id in target_ids
            
        except Exception:
            # Hata durumunda False döndür
            return False
    
    # Convenience methods for common relationship types
    def link_account_contacts(
        self,
        account_id: str,
        contact_ids: Union[str, List[str]],
        **kwargs
    ) -> RelationshipOperationResult:
        """Account'a Contact'ları ilişkilendirir."""
        if isinstance(contact_ids, str):
            return self.link_single("Account", account_id, "contacts", contact_ids, **kwargs)
        else:
            return self.link_multiple("Account", account_id, "contacts", contact_ids, **kwargs)
    
    def unlink_account_contacts(
        self,
        account_id: str,
        contact_ids: Union[str, List[str], None] = None,
        **kwargs
    ) -> RelationshipOperationResult:
        """Account'tan Contact'ları kaldırır."""
        if contact_ids is None:
            return self.unlink_all("Account", account_id, "contacts", **kwargs)
        elif isinstance(contact_ids, str):
            return self.unlink_single("Account", account_id, "contacts", contact_ids, **kwargs)
        else:
            return self.unlink_multiple("Account", account_id, "contacts", contact_ids, **kwargs)
    
    def link_account_opportunities(
        self,
        account_id: str,
        opportunity_ids: Union[str, List[str]],
        **kwargs
    ) -> RelationshipOperationResult:
        """Account'a Opportunity'leri ilişkilendirir."""
        if isinstance(opportunity_ids, str):
            return self.link_single("Account", account_id, "opportunities", opportunity_ids, **kwargs)
        else:
            return self.link_multiple("Account", account_id, "opportunities", opportunity_ids, **kwargs)
    
    def unlink_account_opportunities(
        self,
        account_id: str,
        opportunity_ids: Union[str, List[str], None] = None,
        **kwargs
    ) -> RelationshipOperationResult:
        """Account'tan Opportunity'leri kaldırır."""
        if opportunity_ids is None:
            return self.unlink_all("Account", account_id, "opportunities", **kwargs)
        elif isinstance(opportunity_ids, str):
            return self.unlink_single("Account", account_id, "opportunities", opportunity_ids, **kwargs)
        else:
            return self.unlink_multiple("Account", account_id, "opportunities", opportunity_ids, **kwargs)
    
    def link_contact_teams(
        self,
        contact_id: str,
        team_ids: Union[str, List[str]],
        **kwargs
    ) -> RelationshipOperationResult:
        """Contact'a Team'leri ilişkilendirir."""
        if isinstance(team_ids, str):
            return self.link_single("Contact", contact_id, "teams", team_ids, **kwargs)
        else:
            return self.link_multiple("Contact", contact_id, "teams", team_ids, **kwargs)
    
    def unlink_contact_teams(
        self,
        contact_id: str,
        team_ids: Union[str, List[str], None] = None,
        **kwargs
    ) -> RelationshipOperationResult:
        """Contact'tan Team'leri kaldırır."""
        if team_ids is None:
            return self.unlink_all("Contact", contact_id, "teams", **kwargs)


# Backward compatibility alias
RelationshipsClient = RelationshipClient


# Export edilecek sınıflar
__all__ = [
    "RelationshipClient",
    "RelationshipsClient",
    "RelationshipOperationResult",
]