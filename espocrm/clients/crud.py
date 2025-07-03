"""EspoCRM CRUD operasyonları client'ı.

Bu modül EspoCRM API'nin CRUD operasyonlarını gerçekleştiren
CrudClient sınıfını içerir. Arama parametreleri entegrasyonu,
bulk operasyonlar ve entity-specific metodlar sağlar.
"""

import json
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from urllib.parse import urljoin

from ..exceptions import EspoCRMError, EspoCRMValidationError
from ..utils.validators import validate_entity_data, validate_entity_id, validate_entity_type, ValidationError
from ..models.base import EspoCRMBaseModel
from ..models.entities import EntityRecord, create_entity, EntityType
from ..models.search import SearchParams, WhereClause
from ..models.responses import (
    EntityResponse, 
    ListResponse, 
    BulkOperationResult,
    ErrorResponse,
    parse_entity_response,
    parse_list_response,
    parse_error_response
)
from ..utils.helpers import timing_decorator
from ..logging import get_logger


# Type variables
EntityT = TypeVar("EntityT", bound=EntityRecord)


class CrudClient:
    """EspoCRM CRUD operasyonları için client sınıfı.
    
    Bu sınıf EspoCRM API'nin temel CRUD operasyonlarını sağlar:
    - Create (POST)
    - Read (GET)
    - Update (PUT/PATCH)
    - Delete (DELETE)
    - List (GET with search parameters)
    - Bulk operations
    """
    
    def __init__(self, main_client):
        """CRUD client'ı başlatır.
        
        Args:
            main_client: Ana EspoCRM client instance'ı
        """
        self.client = main_client
        self.logger = get_logger(f"{__name__}.CrudClient")
    
    @timing_decorator
    def create(
        self,
        entity_type: str,
        data: Union[Dict[str, Any], EntityRecord],
        **kwargs
    ) -> EntityResponse:
        """Yeni entity kaydı oluşturur.
        
        Args:
            entity_type: Entity türü (örn: 'Account', 'Contact')
            data: Entity verisi (dict veya EntityRecord)
            **kwargs: Ek request parametreleri
            
        Returns:
            Oluşturulan entity response'u
            
        Raises:
            EspoCRMValidationError: Validation hatası
            EspoCRMError: API hatası
            
        Example:
            >>> account_data = {
            ...     "name": "Test Company",
            ...     "website": "https://test.com"
            ... }
            >>> response = crud_client.create("Account", account_data)
            >>> print(response.get_id())
        """
        self.logger.info(
            "Creating entity",
            entity_type=entity_type,
            has_data=bool(data)
        )
        
        # Entity type validation
        if not entity_type or not entity_type.strip():
            raise EspoCRMValidationError("Entity türü boş olamaz")
        
        # Security validation
        try:
            validate_entity_type(entity_type)
        except ValidationError as e:
            raise EspoCRMValidationError(str(e))
        
        # Data validation
        if data is None:
            raise EspoCRMValidationError("Entity verisi boş olamaz")
        
        if isinstance(data, str):
            raise EspoCRMValidationError("Entity verisi string olamaz")
        
        # Data'yı normalize et
        if isinstance(data, EntityRecord):
            request_data = data.to_api_dict()
        else:
            request_data = data
        
        # Validation
        if not request_data:
            raise EspoCRMValidationError("Entity verisi boş olamaz")
        
        # Security validation for data
        try:
            validate_entity_data(request_data)
        except ValidationError as e:
            raise EspoCRMValidationError(str(e))
        
        try:
            # API request
            response_data = self.client.post(entity_type, data=request_data, **kwargs)
            
            # Response parse et
            entity_response = parse_entity_response(response_data, entity_type)
            
            self.logger.info(
                "Entity created successfully",
                entity_type=entity_type,
                entity_id=entity_response.get_id()
            )
            
            return entity_response
            
        except Exception as e:
            self.logger.error(
                "Failed to create entity",
                entity_type=entity_type,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def read(
        self,
        entity_type: str,
        entity_id: str,
        select: Optional[List[str]] = None,
        **kwargs
    ) -> EntityResponse:
        """Entity kaydını ID'ye göre okur.
        
        Args:
            entity_type: Entity türü
            entity_id: Entity ID'si
            select: Seçilecek field'lar (opsiyonel)
            **kwargs: Ek request parametreleri
            
        Returns:
            Entity response'u
            
        Raises:
            EspoCRMError: API hatası
            
        Example:
            >>> response = crud_client.read("Account", "507f1f77bcf86cd799439011")
            >>> account = response.get_entity()
            >>> print(account.name)
        """
        self.logger.info(
            "Reading entity",
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        # Validation
        if not entity_type or not entity_type.strip():
            raise EspoCRMValidationError("Entity türü boş olamaz")
        
        if not entity_id or not entity_id.strip():
            raise EspoCRMValidationError("Entity ID boş olamaz")
        
        # Security validation
        try:
            validate_entity_type(entity_type)
            validate_entity_id(entity_id)
        except ValidationError as e:
            raise EspoCRMValidationError(str(e))
        
        # Query parameters
        params = {}
        if select:
            params["select"] = ",".join(select)
        
        try:
            # API request
            endpoint = f"{entity_type}/{entity_id}"
            response_data = self.client.get(endpoint, params=params, **kwargs)
            
            # Response parse et
            entity_response = parse_entity_response(response_data, entity_type)
            
            self.logger.info(
                "Entity read successfully",
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            return entity_response
            
        except Exception as e:
            self.logger.error(
                "Failed to read entity",
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def update(
        self,
        entity_type: str,
        entity_id: str,
        data: Union[Dict[str, Any], EntityRecord],
        partial: bool = True,
        **kwargs
    ) -> EntityResponse:
        """Entity kaydını günceller.
        
        Args:
            entity_type: Entity türü
            entity_id: Entity ID'si
            data: Güncellenecek veri
            partial: Partial update (PATCH) mi yoksa full update (PUT) mi
            **kwargs: Ek request parametreleri
            
        Returns:
            Güncellenmiş entity response'u
            
        Raises:
            EspoCRMValidationError: Validation hatası
            EspoCRMError: API hatası
            
        Example:
            >>> update_data = {"website": "https://newsite.com"}
            >>> response = crud_client.update("Account", "507f1f77bcf86cd799439011", update_data)
        """
        self.logger.info(
            "Updating entity",
            entity_type=entity_type,
            entity_id=entity_id,
            partial=partial
        )
        
        # Validation
        if not entity_type or not entity_type.strip():
            raise EspoCRMValidationError("Entity türü boş olamaz")
        
        if not entity_id or not entity_id.strip():
            raise EspoCRMValidationError("Entity ID boş olamaz")
        
        # Security validation
        try:
            validate_entity_type(entity_type)
            validate_entity_id(entity_id)
        except ValidationError as e:
            raise EspoCRMValidationError(str(e))
        
        # Data validation
        if data is None:
            raise EspoCRMValidationError("Güncellenecek veri boş olamaz")
        
        # Data'yı normalize et
        if isinstance(data, EntityRecord):
            request_data = data.to_api_dict()
        else:
            request_data = data
        
        if not request_data:
            raise EspoCRMValidationError("Güncellenecek veri boş olamaz")
        
        # Security validation for data
        try:
            validate_entity_data(request_data)
        except ValidationError as e:
            raise EspoCRMValidationError(str(e))
        
        try:
            # API request
            endpoint = f"{entity_type}/{entity_id}"
            
            if partial:
                response_data = self.client.patch(endpoint, data=request_data, **kwargs)
            else:
                response_data = self.client.put(endpoint, data=request_data, **kwargs)
            
            # Response parse et
            entity_response = parse_entity_response(response_data, entity_type)
            
            self.logger.info(
                "Entity updated successfully",
                entity_type=entity_type,
                entity_id=entity_id
            )
            
            return entity_response
            
        except Exception as e:
            self.logger.error(
                "Failed to update entity",
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def delete(
        self,
        entity_type: str,
        entity_id: str,
        **kwargs
    ) -> bool:
        """Entity kaydını siler.
        
        Args:
            entity_type: Entity türü
            entity_id: Entity ID'si
            **kwargs: Ek request parametreleri
            
        Returns:
            Silme işlemi başarılı ise True
            
        Raises:
            EspoCRMValidationError: Validation hatası
            EspoCRMError: API hatası
            
        Example:
            >>> success = crud_client.delete("Account", "507f1f77bcf86cd799439011")
            >>> print(f"Deleted: {success}")
        """
        self.logger.info(
            "Deleting entity",
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        # Validation
        if not entity_type or not entity_type.strip():
            raise EspoCRMValidationError("Entity türü boş olamaz")
        
        if not entity_id or not entity_id.strip():
            raise EspoCRMValidationError("Entity ID boş olamaz")
        
        # Security validation
        try:
            validate_entity_type(entity_type)
            validate_entity_id(entity_id)
        except ValidationError as e:
            raise EspoCRMValidationError(str(e))
        
        try:
            # API request
            endpoint = f"{entity_type}/{entity_id}"
            response_data = self.client.delete(endpoint, **kwargs)
            
            # EspoCRM delete response'unu kontrol et
            # Başarılı delete genellikle True döndürür veya boş response
            if response_data is True or response_data is None or response_data == {}:
                success = True
            elif isinstance(response_data, dict) and response_data.get("success") is True:
                success = True
            elif isinstance(response_data, bool):
                success = response_data
            else:
                # Beklenmeyen response format
                success = True  # Default olarak başarılı kabul et
            
            self.logger.info(
                "Entity deleted successfully",
                entity_type=entity_type,
                entity_id=entity_id,
                response_data=response_data
            )
            
            return success
            
        except Exception as e:
            self.logger.error(
                "Failed to delete entity",
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def list(
        self,
        entity_type: str,
        search_params: Optional[SearchParams] = None,
        offset: Optional[int] = None,
        max_size: Optional[int] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = None,
        select: Optional[List[str]] = None,
        where: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ListResponse:
        """Entity listesini getirir.
        
        Args:
            entity_type: Entity türü
            search_params: Arama parametreleri (SearchParams instance'ı)
            offset: Başlangıç offset'i
            max_size: Maksimum kayıt sayısı
            order_by: Sıralama field'ı
            order: Sıralama yönü ('asc' veya 'desc')
            select: Seçilecek field'lar
            where: Where clause'ları
            **kwargs: Ek request parametreleri
            
        Returns:
            Liste response'u
            
        Raises:
            EspoCRMError: API hatası
            
        Example:
            >>> # Basit liste
            >>> response = crud_client.list("Account", max_size=10)
            >>> accounts = response.get_entities()
            >>> 
            >>> # Arama parametreleri ile
            >>> from espocrm.models.search import SearchParams
            >>> search = SearchParams().add_contains("name", "Test").set_pagination(0, 20)
            >>> response = crud_client.list("Account", search_params=search)
        """
        # Validation
        if not entity_type or not entity_type.strip():
            raise EspoCRMValidationError("Entity türü boş olamaz")
        
        # Security validation
        try:
            validate_entity_type(entity_type)
        except ValidationError as e:
            raise EspoCRMValidationError(str(e))
        
        # Search params validation
        if search_params is not None and isinstance(search_params, str):
            raise EspoCRMValidationError("Search parametreleri string olamaz")
        
        self.logger.info(
            "Listing entities",
            entity_type=entity_type,
            has_search_params=search_params is not None
        )
        
        try:
            # Query parameters oluştur
            params = {}
            
            # SearchParams kullan
            if search_params:
                # SearchParams validation
                if not hasattr(search_params, 'to_query_params'):
                    raise EspoCRMValidationError("Geçersiz search parametreleri")
                try:
                    params.update(search_params.to_query_params())
                except AttributeError:
                    raise EspoCRMValidationError("Search parametreleri SearchParams instance'ı olmalıdır")
                except ValueError as e:
                    raise EspoCRMValidationError(f"Geçersiz search parametreleri: {str(e)}")
            else:
                # Manuel parametreler
                if offset is not None:
                    params["offset"] = offset
                if max_size is not None:
                    params["maxSize"] = max_size
                if order_by:
                    params["orderBy"] = order_by
                if order:
                    params["order"] = order
                if select:
                    params["select"] = ",".join(select)
                if where:
                    params["where"] = where
            
            # API request
            response_data = self.client.get(entity_type, params=params, **kwargs)
            
            # Response parse et
            list_response = parse_list_response(response_data, entity_type)
            
            self.logger.info(
                "Entities listed successfully",
                entity_type=entity_type,
                total=list_response.total,
                count=len(list_response.list)
            )
            
            return list_response
            
        except Exception as e:
            self.logger.error(
                "Failed to list entities",
                entity_type=entity_type,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def search(
        self,
        entity_type: str,
        search_params: SearchParams,
        **kwargs
    ) -> ListResponse:
        """Gelişmiş arama yapar.
        
        Args:
            entity_type: Entity türü
            search_params: Arama parametreleri
            **kwargs: Ek request parametreleri
            
        Returns:
            Arama sonuçları
            
        Example:
            >>> from espocrm.models.search import SearchParams, equals, contains
            >>> search = SearchParams()
            >>> search.add_where_clause(equals("type", "Customer"))
            >>> search.add_where_clause(contains("name", "Tech"))
            >>> search.set_order("createdAt", "desc")
            >>> results = crud_client.search("Account", search)
        """
        return self.list(entity_type, search_params=search_params, **kwargs)
    
    @timing_decorator
    def bulk_create(
        self,
        entity_type: str,
        entities: List[Union[Dict[str, Any], EntityRecord]],
        **kwargs
    ) -> BulkOperationResult:
        """Bulk entity oluşturma.
        
        Args:
            entity_type: Entity türü
            entities: Oluşturulacak entity'ler listesi
            **kwargs: Ek request parametreleri
            
        Returns:
            Bulk operasyon sonucu
            
        Example:
            >>> entities = [
            ...     {"name": "Company 1", "website": "https://company1.com"},
            ...     {"name": "Company 2", "website": "https://company2.com"}
            ... ]
            >>> result = crud_client.bulk_create("Account", entities)
            >>> print(f"Created: {result.successful}/{result.total}")
        """
        self.logger.info(
            "Bulk creating entities",
            entity_type=entity_type,
            count=len(entities)
        )
        
        if not entities:
            raise EspoCRMValidationError("Entity listesi boş olamaz")
        
        results = []
        successful = 0
        failed = 0
        errors = []
        
        for i, entity_data in enumerate(entities):
            try:
                # Her entity'yi tek tek oluştur
                response = self.create(entity_type, entity_data, **kwargs)
                
                results.append({
                    "index": i,
                    "success": True,
                    "id": response.get_id(),
                    "data": response.data
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
                errors.append({
                    "index": i,
                    "message": str(e)
                })
        
        bulk_result = BulkOperationResult(
            success=failed == 0,
            total=len(entities),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors if errors else None
        )
        
        self.logger.info(
            "Bulk create completed",
            entity_type=entity_type,
            total=bulk_result.total,
            successful=bulk_result.successful,
            failed=bulk_result.failed
        )
        
        return bulk_result
    
    @timing_decorator
    def bulk_update(
        self,
        entity_type: str,
        updates: List[Dict[str, Any]],
        partial: bool = True,
        **kwargs
    ) -> BulkOperationResult:
        """Bulk entity güncelleme.
        
        Args:
            entity_type: Entity türü
            updates: Güncellenecek entity'ler (id ve data içermeli)
            partial: Partial update mi
            **kwargs: Ek request parametreleri
            
        Returns:
            Bulk operasyon sonucu
            
        Example:
            >>> updates = [
            ...     {"id": "507f1f77bcf86cd799439011", "website": "https://new1.com"},
            ...     {"id": "507f1f77bcf86cd799439012", "website": "https://new2.com"}
            ... ]
            >>> result = crud_client.bulk_update("Account", updates)
        """
        self.logger.info(
            "Bulk updating entities",
            entity_type=entity_type,
            count=len(updates)
        )
        
        if not updates:
            raise EspoCRMValidationError("Güncelleme listesi boş olamaz")
        
        results = []
        successful = 0
        failed = 0
        errors = []
        
        for i, update_data in enumerate(updates):
            try:
                entity_id = update_data.get("id")
                if not entity_id:
                    raise EspoCRMValidationError("Update verisi 'id' field'ı içermelidir")
                
                # ID'yi data'dan çıkar
                data = {k: v for k, v in update_data.items() if k != "id"}
                
                # Entity'yi güncelle
                response = self.update(entity_type, entity_id, data, partial, **kwargs)
                
                results.append({
                    "index": i,
                    "success": True,
                    "id": entity_id,
                    "data": response.data
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "id": update_data.get("id"),
                    "error": str(e)
                })
                failed += 1
                errors.append({
                    "index": i,
                    "message": str(e)
                })
        
        bulk_result = BulkOperationResult(
            success=failed == 0,
            total=len(updates),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors if errors else None
        )
        
        self.logger.info(
            "Bulk update completed",
            entity_type=entity_type,
            total=bulk_result.total,
            successful=bulk_result.successful,
            failed=bulk_result.failed
        )
        
        return bulk_result
    
    @timing_decorator
    def bulk_delete(
        self,
        entity_type: str,
        entity_ids: List[str],
        **kwargs
    ) -> BulkOperationResult:
        """Bulk entity silme.
        
        Args:
            entity_type: Entity türü
            entity_ids: Silinecek entity ID'leri
            **kwargs: Ek request parametreleri
            
        Returns:
            Bulk operasyon sonucu
            
        Example:
            >>> ids = ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
            >>> result = crud_client.bulk_delete("Account", ids)
        """
        self.logger.info(
            "Bulk deleting entities",
            entity_type=entity_type,
            count=len(entity_ids)
        )
        
        if not entity_ids:
            raise EspoCRMValidationError("Entity ID listesi boş olamaz")
        
        results = []
        successful = 0
        failed = 0
        errors = []
        
        for i, entity_id in enumerate(entity_ids):
            try:
                # Entity'yi sil
                success = self.delete(entity_type, entity_id, **kwargs)
                
                results.append({
                    "index": i,
                    "success": success,
                    "id": entity_id
                })
                
                if success:
                    successful += 1
                else:
                    failed += 1
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "id": entity_id,
                    "error": str(e)
                })
                failed += 1
                errors.append({
                    "index": i,
                    "message": str(e)
                })
        
        bulk_result = BulkOperationResult(
            success=failed == 0,
            total=len(entity_ids),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors if errors else None
        )
        
        self.logger.info(
            "Bulk delete completed",
            entity_type=entity_type,
            total=bulk_result.total,
            successful=bulk_result.successful,
            failed=bulk_result.failed
        )
        
        return bulk_result
    
    def count(
        self,
        entity_type: str,
        where: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> int:
        """Entity sayısını döndürür.
        
        Args:
            entity_type: Entity türü
            where: Where clause'ları
            **kwargs: Ek request parametreleri
            
        Returns:
            Entity sayısı
        """
        # Sadece count için minimal bir liste çek
        search_params = SearchParams(maxSize=1, offset=0)
        if where:
            search_params.where = where
        
        response = self.list(entity_type, search_params=search_params, **kwargs)
        return response.total
    
    def exists(
        self,
        entity_type: str,
        entity_id: str,
        **kwargs
    ) -> bool:
        """Entity'nin var olup olmadığını kontrol eder.
        
        Args:
            entity_type: Entity türü
            entity_id: Entity ID'si
            **kwargs: Ek request parametreleri
            
        Returns:
            Entity var ise True
        """
        try:
            self.read(entity_type, entity_id, select=["id"], **kwargs)
            return True
        except EspoCRMError:
            return False
    
    # Entity-specific convenience methods
    def get_account(self, account_id: str, **kwargs) -> EntityResponse:
        """Account entity'sini getirir."""
        return self.read("Account", account_id, **kwargs)
    
    def create_account(self, data: Union[Dict[str, Any], EntityRecord], **kwargs) -> EntityResponse:
        """Account entity'si oluşturur."""
        return self.create("Account", data, **kwargs)
    
    def list_accounts(self, search_params: Optional[SearchParams] = None, **kwargs) -> ListResponse:
        """Account listesini getirir."""
        return self.list("Account", search_params=search_params, **kwargs)
    
    def get_contact(self, contact_id: str, **kwargs) -> EntityResponse:
        """Contact entity'sini getirir."""
        return self.read("Contact", contact_id, **kwargs)
    
    def create_contact(self, data: Union[Dict[str, Any], EntityRecord], **kwargs) -> EntityResponse:
        """Contact entity'si oluşturur."""
        return self.create("Contact", data, **kwargs)
    
    def list_contacts(self, search_params: Optional[SearchParams] = None, **kwargs) -> ListResponse:
        """Contact listesini getirir."""
        return self.list("Contact", search_params=search_params, **kwargs)
    
    def get_lead(self, lead_id: str, **kwargs) -> EntityResponse:
        """Lead entity'sini getirir."""
        return self.read("Lead", lead_id, **kwargs)
    
    def create_lead(self, data: Union[Dict[str, Any], EntityRecord], **kwargs) -> EntityResponse:
        """Lead entity'si oluşturur."""
        return self.create("Lead", data, **kwargs)
    
    def list_leads(self, search_params: Optional[SearchParams] = None, **kwargs) -> ListResponse:
        """Lead listesini getirir."""
        return self.list("Lead", search_params=search_params, **kwargs)
    
    def get_opportunity(self, opportunity_id: str, **kwargs) -> EntityResponse:
        """Opportunity entity'sini getirir."""
        return self.read("Opportunity", opportunity_id, **kwargs)
    
    def create_opportunity(self, data: Union[Dict[str, Any], EntityRecord], **kwargs) -> EntityResponse:
        """Opportunity entity'si oluşturur."""
        return self.create("Opportunity", data, **kwargs)
    
    def list_opportunities(self, search_params: Optional[SearchParams] = None, **kwargs) -> ListResponse:
        """Opportunity listesini getirir."""
        return self.list("Opportunity", search_params=search_params, **kwargs)


# Export edilecek sınıflar
__all__ = [
    "CrudClient",
    "EntityT",
]