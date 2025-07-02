"""
EspoCRM CRUD Client Test Module

CRUD operasyonları için kapsamlı testler.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import responses

from espocrm.clients.crud import CrudClient
from espocrm.models.entities import EntityRecord
# from espocrm.models.requests import (
#     CreateRequest,
#     UpdateRequest,
#     DeleteRequest,
#     ListRequest
# )
from espocrm.models.responses import (
    EntityResponse,
    ListResponse
)
from espocrm.models.search import SearchParams, WhereClause, OrderDirection
from espocrm.exceptions import (
    EspoCRMError,
    EspoCRMNotFoundError,
    EspoCRMValidationError,
    EspoCRMRateLimitError
)


@pytest.mark.unit
@pytest.mark.crud
class TestCRUDClient:
    """CRUD Client temel testleri."""
    
    def test_crud_client_initialization(self, mock_client):
        """CRUD client initialization testi."""
        crud_client = CrudClient(mock_client)
        
        assert crud_client.client == mock_client
        # CrudClient doesn't have base_url and api_version attributes
        # assert crud_client.base_url == mock_client.base_url
        # assert crud_client.api_version == mock_client.api_version
    
    def test_create_entity_success(self, mock_client, sample_account):
        """Entity oluşturma başarı testi."""
        # Mock response setup
        mock_client.post.return_value = sample_account.data
        
        crud_client = CrudClient(mock_client)
        
        # Create request
        create_data = {
            "name": "New Company",
            "type": "Customer",
            "industry": "Technology"
        }
        
        result = crud_client.create("Account", create_data)
        
        # Assertions
        assert isinstance(result, EntityResponse)
        assert result.data.get("name") == sample_account.get("name")
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Account",
            data=create_data
        )
    
    def test_create_entity_validation_error(self, mock_client):
        """Entity oluşturma validation error testi."""
        # Mock validation error response
        mock_client.post.side_effect = EspoCRMValidationError("Required field missing")
        
        crud_client = CrudClient(mock_client)
        
        with pytest.raises(EspoCRMValidationError):
            crud_client.create("Account", {})
    
    def test_read_entity_success(self, mock_client, sample_account):
        """Entity okuma başarı testi."""
        # Mock response setup
        mock_client.get.return_value = sample_account.data
        
        crud_client = CrudClient(mock_client)
        
        result = crud_client.read("Account", "account_123")
        
        # Assertions
        assert isinstance(result, EntityResponse)
        assert result.data.get("id") == "account_123"
        assert result.data.get("name") == sample_account.get("name")
        
        # API call verification
        mock_client.get.assert_called_once_with("Account/account_123")
    
    def test_read_entity_not_found(self, mock_client):
        """Entity okuma not found testi."""
        # Mock not found response
        mock_client.get.side_effect = EspoCRMNotFoundError("Entity not found")
        
        crud_client = CrudClient(mock_client)
        
        with pytest.raises(EspoCRMNotFoundError):
            crud_client.read("Account", "nonexistent_id")
    
    def test_update_entity_success(self, mock_client, sample_account):
        """Entity güncelleme başarı testi."""
        # Mock response setup
        updated_data = sample_account.data.copy()
        updated_data["name"] = "Updated Company Name"
        mock_client.put.return_value = updated_data
        
        crud_client = CrudClient(mock_client)
        
        update_data = {"name": "Updated Company Name"}
        result = crud_client.update("Account", "account_123", update_data)
        
        # Assertions
        assert isinstance(result, EntityResponse)
        assert result.data.get("name") == "Updated Company Name"
        
        # API call verification
        mock_client.put.assert_called_once_with(
            "Account/account_123",
            data=update_data
        )
    
    def test_update_entity_partial(self, mock_client, sample_account):
        """Entity partial update testi."""
        # Mock response setup
        updated_data = sample_account.data.copy()
        updated_data["industry"] = "Healthcare"
        mock_client.patch.return_value = updated_data
        
        crud_client = CrudClient(mock_client)
        
        update_data = {"industry": "Healthcare"}
        result = crud_client.update("Account", "account_123", update_data, partial=True)
        
        # Assertions
        assert isinstance(result, EntityResponse)
        assert result.data.get("industry") == "Healthcare"
        
        # API call verification
        mock_client.patch.assert_called_once_with(
            "Account/account_123",
            data=update_data
        )
    
    def test_delete_entity_success(self, mock_client):
        """Entity silme başarı testi."""
        # Mock response setup
        mock_client.delete.return_value = {"deleted": True}
        
        crud_client = CrudClient(mock_client)
        
        result = crud_client.delete("Account", "account_123")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.delete.assert_called_once_with("Account/account_123")
    
    def test_delete_entity_not_found(self, mock_client):
        """Entity silme not found testi."""
        # Mock not found response
        mock_client.delete.side_effect = EspoCRMNotFoundError("Entity not found")
        
        crud_client = CrudClient(mock_client)
        
        with pytest.raises(EspoCRMNotFoundError):
            crud_client.delete("Account", "nonexistent_id")
    
    def test_list_entities_success(self, mock_client, sample_entities):
        """Entity listeleme başarı testi."""
        # Mock response setup
        mock_response = {
            "total": 2,
            "list": [
                sample_entities["Account"].data,
                {
                    "id": "account_456",
                    "name": "Another Company",
                    "type": "Partner"
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        crud_client = CrudClient(mock_client)
        
        result = crud_client.list("Account")
        
        # Assertions
        assert isinstance(result, ListResponse)
        assert result.total == 2
        assert len(result.list) == 2
        assert all(isinstance(entity, dict) for entity in result.list)
        
        # API call verification
        mock_client.get.assert_called_once_with("Account", params={})
    
    def test_list_entities_with_params(self, mock_client):
        """Entity listeleme parametreli testi."""
        # Mock response setup
        mock_response = {"total": 0, "list": []}
        mock_client.get.return_value = mock_response
        
        crud_client = CrudClient(mock_client)
        
        # Search parameters
        search_params = SearchParams(
            select=["name", "type", "industry"],
            where=[
                {"type": "equals", "attribute": "type", "value": "Customer"}
            ],
            orderBy="name",
            order=OrderDirection.ASC,
            offset=0,
            maxSize=50
        )
        
        result = crud_client.list("Account", search_params=search_params)
        
        # Assertions
        assert isinstance(result, ListResponse)
        
        # API call verification
        expected_params = search_params.to_query_params()
        mock_client.get.assert_called_once_with("Account", params=expected_params)


@pytest.mark.unit
@pytest.mark.crud
# @pytest.mark.parametrize
class TestCRUDClientParametrized:
    """CRUD Client parametrized testleri."""
    
    @pytest.mark.parametrize("entity_type", ["Account", "Contact", "Lead", "Opportunity"])
    def test_create_different_entity_types(self, mock_client, entity_type):
        """Farklı entity türleri için create testi."""
        # Mock response
        mock_data = {"id": f"{entity_type.lower()}_123", "name": f"Test {entity_type}"}
        mock_client.post.return_value = mock_data
        
        crud_client = CrudClient(mock_client)
        
        create_data = {"name": f"Test {entity_type}"}
        result = crud_client.create(entity_type, create_data)
        
        assert isinstance(result, EntityResponse)
        mock_client.post.assert_called_once_with(entity_type, data=create_data)
    
    @pytest.mark.parametrize("http_method,crud_method,partial", [
        ("put", "update", False),
        ("patch", "update", True)
    ])
    def test_update_methods(self, mock_client, http_method, crud_method, partial):
        """Update method'ları testi."""
        # Mock response
        mock_data = {"id": "account_123", "name": "Updated Name"}
        getattr(mock_client, http_method).return_value = mock_data
        
        crud_client = CrudClient(mock_client)
        
        update_data = {"name": "Updated Name"}
        result = getattr(crud_client, crud_method)("Account", "account_123", update_data, partial=partial)
        
        assert isinstance(result, EntityResponse)
        getattr(mock_client, http_method).assert_called_once()
    
    @pytest.mark.parametrize("error_class,status_code", [
        (EspoCRMNotFoundError, 404),
        (EspoCRMValidationError, 400),
        (EspoCRMRateLimitError, 429),
        (EspoCRMError, 500)
    ])
    def test_error_handling(self, mock_client, error_class, status_code):
        """Error handling testi."""
        mock_client.get.side_effect = error_class(f"Error {status_code}")
        
        crud_client = CrudClient(mock_client)
        
        with pytest.raises(error_class):
            crud_client.read("Account", "test_id")


@pytest.mark.unit
@pytest.mark.crud
@pytest.mark.performance
class TestCRUDClientPerformance:
    """CRUD Client performance testleri."""
    
    def test_bulk_create_performance(self, mock_client, performance_timer):
        """Bulk create performance testi."""
        # Mock response
        mock_client.post.return_value = {"id": "test_id", "name": "Test"}
        
        crud_client = CrudClient(mock_client)
        
        # 100 entity oluştur
        entities_data = [{"name": f"Entity {i}"} for i in range(100)]
        
        performance_timer.start()
        results = []
        for data in entities_data:
            result = crud_client.create("Account", data)
            results.append(result)
        performance_timer.stop()
        
        # Performance assertions
        assert len(results) == 100
        assert performance_timer.elapsed < 5.0  # 5 saniyeden az
        assert mock_client.post.call_count == 100
    
    def test_bulk_read_performance(self, mock_client, performance_timer):
        """Bulk read performance testi."""
        # Mock response
        mock_client.get.return_value = {"id": "test_id", "name": "Test"}
        
        crud_client = CrudClient(mock_client)
        
        # 100 entity oku
        entity_ids = [f"id_{i}" for i in range(100)]
        
        performance_timer.start()
        results = []
        for entity_id in entity_ids:
            result = crud_client.read("Account", entity_id)
            results.append(result)
        performance_timer.stop()
        
        # Performance assertions
        assert len(results) == 100
        assert performance_timer.elapsed < 3.0  # 3 saniyeden az
        assert mock_client.get.call_count == 100
    
    def test_large_list_performance(self, mock_client, performance_timer):
        """Large list performance testi."""
        # Mock large response
        large_list = [{"id": f"id_{i}", "name": f"Entity {i}"} for i in range(1000)]
        mock_client.get.return_value = {"total": 1000, "list": large_list}
        
        crud_client = CrudClient(mock_client)
        
        performance_timer.start()
        result = crud_client.list("Account")
        performance_timer.stop()
        
        # Performance assertions
        assert len(result.list) == 1000
        assert performance_timer.elapsed < 2.0  # 2 saniyeden az


@pytest.mark.unit
@pytest.mark.crud
@pytest.mark.validation
class TestCRUDClientValidation:
    """CRUD Client validation testleri."""
    
    def test_create_data_validation(self, mock_client):
        """Create data validation testi."""
        crud_client = CrudClient(mock_client)
        
        # Empty data
        with pytest.raises(EspoCRMValidationError):
            crud_client.create("Account", {})
        
        # None data
        with pytest.raises(EspoCRMValidationError):
            crud_client.create("Account", None)
        
        # Invalid data type
        with pytest.raises(EspoCRMValidationError):
            crud_client.create("Account", "invalid_data")
    
    def test_entity_type_validation(self, mock_client):
        """Entity type validation testi."""
        crud_client = CrudClient(mock_client)
        
        # Empty entity type
        with pytest.raises(EspoCRMValidationError):
            crud_client.create("", {"name": "Test"})
        
        # None entity type
        with pytest.raises(EspoCRMValidationError):
            crud_client.create(None, {"name": "Test"})
        
        # Invalid entity type
        with pytest.raises(EspoCRMValidationError):
            crud_client.create("InvalidEntity", {"name": "Test"})
    
    def test_entity_id_validation(self, mock_client):
        """Entity ID validation testi."""
        crud_client = CrudClient(mock_client)
        
        # Empty entity ID
        with pytest.raises(EspoCRMValidationError):
            crud_client.read("Account", "")
        
        # None entity ID
        with pytest.raises(EspoCRMValidationError):
            crud_client.read("Account", None)
        
        # Invalid entity ID format
        with pytest.raises(EspoCRMValidationError):
            crud_client.read("Account", "invalid id with spaces")
    
    def test_update_data_validation(self, mock_client):
        """Update data validation testi."""
        crud_client = CrudClient(mock_client)
        
        # Empty update data
        with pytest.raises(EspoCRMValidationError):
            crud_client.update("Account", "test_id", {})
        
        # None update data
        with pytest.raises(EspoCRMValidationError):
            crud_client.update("Account", "test_id", None)
    
    def test_search_params_validation(self, mock_client):
        """Search parameters validation testi."""
        crud_client = CrudClient(mock_client)
        
        # Invalid search params type
        with pytest.raises(EspoCRMValidationError):
            crud_client.list("Account", search_params="invalid")
        
        # Invalid where clause
        invalid_search = SearchParams(
            where=[{"invalid": "clause"}]  # Should be WhereClause objects
        )
        
        with pytest.raises(EspoCRMValidationError):
            crud_client.list("Account", search_params=invalid_search)


@pytest.mark.integration
@pytest.mark.crud
class TestCRUDClientIntegration:
    """CRUD Client integration testleri."""
    
    def test_full_crud_workflow(self, real_client, mock_http_responses):
        """Full CRUD workflow integration testi."""
        crud_client = CrudClient(real_client)
        
        # 1. Create
        create_data = {
            "name": "Integration Test Company",
            "type": "Customer",
            "industry": "Technology"
        }
        
        created_entity = crud_client.create("Account", create_data)
        assert isinstance(created_entity, EntityResponse)
        assert created_entity.data.get("name") == create_data["name"]
        
        # 2. Read
        entity_id = created_entity.data.get("id")
        read_entity = crud_client.read("Account", entity_id)
        assert read_entity.data.get("id") == entity_id
        assert read_entity.data.get("name") == create_data["name"]
        
        # 3. Update
        update_data = {"industry": "Healthcare"}
        updated_entity = crud_client.update("Account", entity_id, update_data)
        assert updated_entity.data.get("industry") == "Healthcare"
        
        # 4. List
        list_result = crud_client.list("Account")
        assert isinstance(list_result, ListResponse)
        assert list_result.total >= 1
        
        # 5. Delete
        delete_result = crud_client.delete("Account", entity_id)
        assert delete_result is True
    
    @responses.activate
    def test_error_recovery_workflow(self, real_client, mock_http_responses):
        """Error recovery workflow testi."""
        crud_client = CrudClient(real_client)
        
        # Network error simulation
        with patch.object(real_client, 'get', side_effect=ConnectionError("Network error")):
            with pytest.raises(EspoCRMError):
                crud_client.read("Account", "test_id")
        
        # Recovery after network error
        mock_data = {"id": "test_id", "name": "Test Entity"}
        with patch.object(real_client, 'get', return_value=mock_data):
            result = crud_client.read("Account", "test_id")
            assert isinstance(result, EntityResponse)
    
    def test_concurrent_operations(self, real_client):
        """Concurrent operations testi."""
        import threading
        import time
        
        crud_client = CrudClient(real_client)
        results = []
        errors = []
        
        def create_entity(index):
            try:
                data = {"name": f"Concurrent Entity {index}"}
                with patch.object(real_client, 'post', return_value={"id": f"id_{index}", **data}):
                    result = crud_client.create("Account", data)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 10 concurrent create operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_entity, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Assertions
        assert len(errors) == 0  # No errors
        assert len(results) == 10  # All operations successful


@pytest.mark.unit
@pytest.mark.crud
@pytest.mark.security
class TestCRUDClientSecurity:
    """CRUD Client security testleri."""
    
    def test_sql_injection_prevention(self, mock_client, security_test_data):
        """SQL injection prevention testi."""
        crud_client = CrudClient(mock_client)
        
        # SQL injection payloads
        for payload in security_test_data["sql_injection"]:
            # Create ile injection denemesi
            with pytest.raises((EspoCRMValidationError, EspoCRMError)):
                crud_client.create("Account", {"name": payload})
            
            # Search ile injection denemesi
            search_params = SearchParams(
                where=[{"type": "equals", "attribute": "name", "value": payload}]
            )
            
            # Bu güvenli olmalı - validation geçmeli
            try:
                crud_client.list("Account", search_params=search_params)
            except (EspoCRMValidationError, EspoCRMError):
                pass  # Expected for malicious payloads
    
    def test_xss_prevention(self, mock_client, security_test_data):
        """XSS prevention testi."""
        crud_client = CrudClient(mock_client)
        
        # XSS payloads
        for payload in security_test_data["xss_payloads"]:
            # Data sanitization kontrolü
            with pytest.raises((EspoCRMValidationError, EspoCRMError)):
                crud_client.create("Account", {"description": payload})
    
    def test_path_traversal_prevention(self, mock_client, security_test_data):
        """Path traversal prevention testi."""
        crud_client = CrudClient(mock_client)
        
        # Path traversal payloads
        for payload in security_test_data["path_traversal"]:
            # Entity ID olarak path traversal denemesi
            with pytest.raises((EspoCRMValidationError, EspoCRMError)):
                crud_client.read("Account", payload)
    
    def test_large_payload_handling(self, mock_client, security_test_data):
        """Large payload handling testi."""
        crud_client = CrudClient(mock_client)
        
        # Large payloads
        for payload in security_test_data["large_payloads"]:
            # DoS attack prevention
            with pytest.raises((EspoCRMValidationError, EspoCRMError)):
                if isinstance(payload, str):
                    crud_client.create("Account", {"description": payload})
                elif isinstance(payload, dict):
                    crud_client.create("Account", payload)
                elif isinstance(payload, list):
                    crud_client.create("Account", {"tags": payload})
    
    def test_authorization_enforcement(self, mock_client):
        """Authorization enforcement testi."""
        crud_client = CrudClient(mock_client)
        
        # Unauthorized access simulation
        mock_client.get.side_effect = EspoCRMError("Unauthorized", status_code=401)
        
        with pytest.raises(EspoCRMError):
            crud_client.read("Account", "test_id")
        
        # Forbidden access simulation
        mock_client.post.side_effect = EspoCRMError("Forbidden", status_code=403)
        
        with pytest.raises(EspoCRMError):
            crud_client.create("Account", {"name": "Test"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])