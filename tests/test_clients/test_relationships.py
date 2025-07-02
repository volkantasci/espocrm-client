"""
EspoCRM Relationships Client Test Module

Relationship operasyonları için kapsamlı testler.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import responses

from espocrm.clients.relationships import RelationshipsClient
from espocrm.models.entities import Entity
from espocrm.models.responses import ListResponse, RelationshipResponse
from espocrm.models.search import SearchParams, WhereClause
from espocrm.exceptions import (
    EspoCRMError,
    EntityNotFoundError,
    ValidationError,
    RelationshipError
)


@pytest.mark.unit
@pytest.mark.relationships
class TestRelationshipsClient:
    """Relationships Client temel testleri."""
    
    def test_relationships_client_initialization(self, mock_client):
        """Relationships client initialization testi."""
        rel_client = RelationshipsClient(mock_client)
        
        assert rel_client.client == mock_client
        assert rel_client.base_url == mock_client.base_url
        assert rel_client.api_version == mock_client.api_version
    
    def test_get_related_entities_success(self, mock_client, sample_entities):
        """Related entities alma başarı testi."""
        # Mock response setup
        mock_response = {
            "total": 2,
            "list": [
                sample_entities["Contact"].data,
                {
                    "id": "contact_456",
                    "firstName": "Jane",
                    "lastName": "Smith",
                    "accountId": "account_123"
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        rel_client = RelationshipsClient(mock_client)
        
        result = rel_client.get_related("Account", "account_123", "contacts")
        
        # Assertions
        assert isinstance(result, ListResponse)
        assert result.total == 2
        assert len(result.entities) == 2
        assert all(isinstance(entity, Entity) for entity in result.entities)
        assert result.entities[0].entity_type == "Contact"
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Account/account_123/contacts",
            params={}
        )
    
    def test_get_related_entities_with_params(self, mock_client):
        """Related entities parametreli alma testi."""
        # Mock response setup
        mock_response = {"total": 1, "list": [{"id": "contact_123", "firstName": "John"}]}
        mock_client.get.return_value = mock_response
        
        rel_client = RelationshipsClient(mock_client)
        
        # Search parameters
        search_params = SearchParams(
            select=["firstName", "lastName", "emailAddress"],
            where=[
                WhereClause(field="firstName", operator="equals", value="John")
            ],
            order_by="lastName",
            max_size=10
        )
        
        result = rel_client.get_related("Account", "account_123", "contacts", search_params)
        
        # Assertions
        assert isinstance(result, ListResponse)
        
        # API call verification
        expected_params = search_params.to_query_params()
        mock_client.get.assert_called_once_with(
            "Account/account_123/contacts",
            params=expected_params
        )
    
    def test_link_entities_success(self, mock_client):
        """Entity linking başarı testi."""
        # Mock response setup
        mock_client.post.return_value = {"linked": True}
        
        rel_client = RelationshipsClient(mock_client)
        
        result = rel_client.link("Account", "account_123", "contacts", "contact_456")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Account/account_123/contacts",
            data={"id": "contact_456"}
        )
    
    def test_link_entities_with_data(self, mock_client):
        """Entity linking with additional data testi."""
        # Mock response setup
        mock_client.post.return_value = {"linked": True}
        
        rel_client = RelationshipsClient(mock_client)
        
        link_data = {
            "id": "contact_456",
            "role": "Primary Contact",
            "isPrimary": True
        }
        
        result = rel_client.link("Account", "account_123", "contacts", "contact_456", link_data)
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Account/account_123/contacts",
            data=link_data
        )
    
    def test_unlink_entities_success(self, mock_client):
        """Entity unlinking başarı testi."""
        # Mock response setup
        mock_client.delete.return_value = {"unlinked": True}
        
        rel_client = RelationshipsClient(mock_client)
        
        result = rel_client.unlink("Account", "account_123", "contacts", "contact_456")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.delete.assert_called_once_with(
            "Account/account_123/contacts/contact_456"
        )
    
    def test_link_entities_validation_error(self, mock_client):
        """Entity linking validation error testi."""
        # Mock validation error response
        mock_client.post.side_effect = ValidationError("Invalid relationship")
        
        rel_client = RelationshipsClient(mock_client)
        
        with pytest.raises(ValidationError):
            rel_client.link("Account", "account_123", "invalid_relation", "contact_456")
    
    def test_unlink_entities_not_found(self, mock_client):
        """Entity unlinking not found testi."""
        # Mock not found response
        mock_client.delete.side_effect = EntityNotFoundError("Relationship not found")
        
        rel_client = RelationshipsClient(mock_client)
        
        with pytest.raises(EntityNotFoundError):
            rel_client.unlink("Account", "nonexistent_id", "contacts", "contact_456")
    
    def test_get_relationship_info(self, mock_client):
        """Relationship info alma testi."""
        # Mock response setup
        mock_response = {
            "relationshipType": "oneToMany",
            "entity": "Contact",
            "foreign": "account",
            "foreignKey": "accountId"
        }
        mock_client.get.return_value = mock_response
        
        rel_client = RelationshipsClient(mock_client)
        
        result = rel_client.get_relationship_info("Account", "contacts")
        
        # Assertions
        assert result["relationshipType"] == "oneToMany"
        assert result["entity"] == "Contact"
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Metadata/entityDefs/Account/links/contacts"
        )


@pytest.mark.unit
@pytest.mark.relationships
@pytest.mark.parametrize
class TestRelationshipsClientParametrized:
    """Relationships Client parametrized testleri."""
    
    @pytest.mark.parametrize("entity_type,relation_name", [
        ("Account", "contacts"),
        ("Account", "opportunities"),
        ("Contact", "opportunities"),
        ("Lead", "targetLists"),
        ("Opportunity", "contacts")
    ])
    def test_get_related_different_relationships(self, mock_client, entity_type, relation_name):
        """Farklı relationship türleri için get_related testi."""
        # Mock response
        mock_response = {"total": 1, "list": [{"id": "related_123"}]}
        mock_client.get.return_value = mock_response
        
        rel_client = RelationshipsClient(mock_client)
        
        result = rel_client.get_related(entity_type, "entity_123", relation_name)
        
        assert isinstance(result, ListResponse)
        mock_client.get.assert_called_once_with(
            f"{entity_type}/entity_123/{relation_name}",
            params={}
        )
    
    @pytest.mark.parametrize("relationship_type", [
        "oneToMany",
        "manyToOne", 
        "manyToMany",
        "oneToOne"
    ])
    def test_link_different_relationship_types(self, mock_client, relationship_type):
        """Farklı relationship türleri için link testi."""
        # Mock response
        mock_client.post.return_value = {"linked": True}
        
        rel_client = RelationshipsClient(mock_client)
        
        result = rel_client.link("Entity1", "id1", "relation", "id2")
        
        assert result is True
        mock_client.post.assert_called_once()
    
    @pytest.mark.parametrize("error_class,status_code", [
        (EntityNotFoundError, 404),
        (ValidationError, 400),
        (RelationshipError, 422),
        (EspoCRMError, 500)
    ])
    def test_relationship_error_handling(self, mock_client, error_class, status_code):
        """Relationship error handling testi."""
        mock_client.get.side_effect = error_class(f"Error {status_code}")
        
        rel_client = RelationshipsClient(mock_client)
        
        with pytest.raises(error_class):
            rel_client.get_related("Account", "test_id", "contacts")


@pytest.mark.unit
@pytest.mark.relationships
@pytest.mark.validation
class TestRelationshipsClientValidation:
    """Relationships Client validation testleri."""
    
    def test_entity_type_validation(self, mock_client):
        """Entity type validation testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Empty entity type
        with pytest.raises(ValidationError):
            rel_client.get_related("", "id", "relation")
        
        # None entity type
        with pytest.raises(ValidationError):
            rel_client.get_related(None, "id", "relation")
    
    def test_entity_id_validation(self, mock_client):
        """Entity ID validation testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Empty entity ID
        with pytest.raises(ValidationError):
            rel_client.get_related("Account", "", "contacts")
        
        # None entity ID
        with pytest.raises(ValidationError):
            rel_client.get_related("Account", None, "contacts")
        
        # Invalid entity ID format
        with pytest.raises(ValidationError):
            rel_client.get_related("Account", "invalid id", "contacts")
    
    def test_relationship_name_validation(self, mock_client):
        """Relationship name validation testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Empty relationship name
        with pytest.raises(ValidationError):
            rel_client.get_related("Account", "id", "")
        
        # None relationship name
        with pytest.raises(ValidationError):
            rel_client.get_related("Account", "id", None)
        
        # Invalid relationship name
        with pytest.raises(ValidationError):
            rel_client.get_related("Account", "id", "invalid relation")
    
    def test_related_entity_id_validation(self, mock_client):
        """Related entity ID validation testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Empty related entity ID
        with pytest.raises(ValidationError):
            rel_client.link("Account", "id", "contacts", "")
        
        # None related entity ID
        with pytest.raises(ValidationError):
            rel_client.link("Account", "id", "contacts", None)
        
        # Invalid related entity ID format
        with pytest.raises(ValidationError):
            rel_client.link("Account", "id", "contacts", "invalid id")
    
    def test_link_data_validation(self, mock_client):
        """Link data validation testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Invalid link data type
        with pytest.raises(ValidationError):
            rel_client.link("Account", "id", "contacts", "contact_id", "invalid_data")
        
        # Link data without ID
        invalid_data = {"role": "Primary"}  # Missing ID
        with pytest.raises(ValidationError):
            rel_client.link("Account", "id", "contacts", "contact_id", invalid_data)


@pytest.mark.unit
@pytest.mark.relationships
@pytest.mark.performance
class TestRelationshipsClientPerformance:
    """Relationships Client performance testleri."""
    
    def test_bulk_link_performance(self, mock_client, performance_timer):
        """Bulk link performance testi."""
        # Mock response
        mock_client.post.return_value = {"linked": True}
        
        rel_client = RelationshipsClient(mock_client)
        
        # 50 entity link et
        related_ids = [f"contact_{i}" for i in range(50)]
        
        performance_timer.start()
        results = []
        for related_id in related_ids:
            result = rel_client.link("Account", "account_123", "contacts", related_id)
            results.append(result)
        performance_timer.stop()
        
        # Performance assertions
        assert len(results) == 50
        assert all(result is True for result in results)
        assert performance_timer.elapsed < 3.0  # 3 saniyeden az
        assert mock_client.post.call_count == 50
    
    def test_bulk_unlink_performance(self, mock_client, performance_timer):
        """Bulk unlink performance testi."""
        # Mock response
        mock_client.delete.return_value = {"unlinked": True}
        
        rel_client = RelationshipsClient(mock_client)
        
        # 50 entity unlink et
        related_ids = [f"contact_{i}" for i in range(50)]
        
        performance_timer.start()
        results = []
        for related_id in related_ids:
            result = rel_client.unlink("Account", "account_123", "contacts", related_id)
            results.append(result)
        performance_timer.stop()
        
        # Performance assertions
        assert len(results) == 50
        assert all(result is True for result in results)
        assert performance_timer.elapsed < 3.0  # 3 saniyeden az
        assert mock_client.delete.call_count == 50
    
    def test_large_related_list_performance(self, mock_client, performance_timer):
        """Large related list performance testi."""
        # Mock large response
        large_list = [{"id": f"contact_{i}", "firstName": f"Contact {i}"} for i in range(500)]
        mock_client.get.return_value = {"total": 500, "list": large_list}
        
        rel_client = RelationshipsClient(mock_client)
        
        performance_timer.start()
        result = rel_client.get_related("Account", "account_123", "contacts")
        performance_timer.stop()
        
        # Performance assertions
        assert len(result.entities) == 500
        assert performance_timer.elapsed < 2.0  # 2 saniyeden az


@pytest.mark.integration
@pytest.mark.relationships
class TestRelationshipsClientIntegration:
    """Relationships Client integration testleri."""
    
    @responses.activate
    def test_full_relationship_workflow(self, real_client, mock_http_responses):
        """Full relationship workflow integration testi."""
        rel_client = RelationshipsClient(real_client)
        
        # 1. Get initial related entities
        initial_contacts = rel_client.get_related("Account", "account_123", "contacts")
        initial_count = len(initial_contacts.entities)
        
        # 2. Link new entity
        link_result = rel_client.link("Account", "account_123", "contacts", "contact_456")
        assert link_result is True
        
        # 3. Verify link
        updated_contacts = rel_client.get_related("Account", "account_123", "contacts")
        assert len(updated_contacts.entities) == initial_count + 1
        
        # 4. Unlink entity
        unlink_result = rel_client.unlink("Account", "account_123", "contacts", "contact_456")
        assert unlink_result is True
        
        # 5. Verify unlink
        final_contacts = rel_client.get_related("Account", "account_123", "contacts")
        assert len(final_contacts.entities) == initial_count
    
    @responses.activate
    def test_complex_relationship_queries(self, real_client, mock_http_responses):
        """Complex relationship queries testi."""
        rel_client = RelationshipsClient(real_client)
        
        # Complex search with multiple conditions
        search_params = SearchParams(
            select=["firstName", "lastName", "emailAddress", "title"],
            where=[
                WhereClause(field="title", operator="contains", value="Manager"),
                WhereClause(field="emailAddress", operator="isNotNull")
            ],
            order_by="lastName",
            order="asc",
            max_size=20
        )
        
        result = rel_client.get_related("Account", "account_123", "contacts", search_params)
        
        assert isinstance(result, ListResponse)
        # Verify that search parameters were applied
        for entity in result.entities:
            assert entity.get("firstName") is not None
            assert entity.get("lastName") is not None
    
    def test_relationship_error_recovery(self, real_client):
        """Relationship error recovery testi."""
        rel_client = RelationshipsClient(real_client)
        
        # Network error simulation
        with patch.object(real_client, 'post', side_effect=ConnectionError("Network error")):
            with pytest.raises(EspoCRMError):
                rel_client.link("Account", "account_123", "contacts", "contact_456")
        
        # Recovery after network error
        with patch.object(real_client, 'post', return_value={"linked": True}):
            result = rel_client.link("Account", "account_123", "contacts", "contact_456")
            assert result is True
    
    def test_concurrent_relationship_operations(self, real_client):
        """Concurrent relationship operations testi."""
        import threading
        
        rel_client = RelationshipsClient(real_client)
        results = []
        errors = []
        
        def link_entity(index):
            try:
                with patch.object(real_client, 'post', return_value={"linked": True}):
                    result = rel_client.link("Account", "account_123", "contacts", f"contact_{index}")
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 10 concurrent link operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=link_entity, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Assertions
        assert len(errors) == 0  # No errors
        assert len(results) == 10  # All operations successful
        assert all(result is True for result in results)


@pytest.mark.unit
@pytest.mark.relationships
@pytest.mark.security
class TestRelationshipsClientSecurity:
    """Relationships Client security testleri."""
    
    def test_relationship_access_control(self, mock_client):
        """Relationship access control testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Unauthorized access simulation
        mock_client.get.side_effect = EspoCRMError("Unauthorized", status_code=401)
        
        with pytest.raises(EspoCRMError):
            rel_client.get_related("Account", "account_123", "contacts")
        
        # Forbidden relationship access
        mock_client.post.side_effect = EspoCRMError("Forbidden", status_code=403)
        
        with pytest.raises(EspoCRMError):
            rel_client.link("Account", "account_123", "contacts", "contact_456")
    
    def test_relationship_injection_prevention(self, mock_client, security_test_data):
        """Relationship injection prevention testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # SQL injection in relationship queries
        for payload in security_test_data["sql_injection"]:
            search_params = SearchParams(
                where=[WhereClause(field="name", operator="equals", value=payload)]
            )
            
            with pytest.raises((ValidationError, EspoCRMError)):
                rel_client.get_related("Account", "account_123", "contacts", search_params)
    
    def test_path_traversal_in_relationships(self, mock_client, security_test_data):
        """Path traversal in relationships prevention testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Path traversal in entity IDs
        for payload in security_test_data["path_traversal"]:
            with pytest.raises((ValidationError, EspoCRMError)):
                rel_client.get_related("Account", payload, "contacts")
            
            with pytest.raises((ValidationError, EspoCRMError)):
                rel_client.link("Account", "account_123", "contacts", payload)
    
    def test_relationship_data_sanitization(self, mock_client, security_test_data):
        """Relationship data sanitization testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # XSS in link data
        for payload in security_test_data["xss_payloads"]:
            link_data = {
                "id": "contact_456",
                "role": payload  # Malicious payload
            }
            
            with pytest.raises((ValidationError, EspoCRMError)):
                rel_client.link("Account", "account_123", "contacts", "contact_456", link_data)
    
    def test_relationship_rate_limiting(self, mock_client):
        """Relationship rate limiting testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Rate limit simulation
        mock_client.post.side_effect = EspoCRMError("Rate limit exceeded", status_code=429)
        
        with pytest.raises(EspoCRMError):
            rel_client.link("Account", "account_123", "contacts", "contact_456")


@pytest.mark.unit
@pytest.mark.relationships
@pytest.mark.edge_cases
class TestRelationshipsClientEdgeCases:
    """Relationships Client edge cases testleri."""
    
    def test_empty_relationship_list(self, mock_client):
        """Empty relationship list testi."""
        # Mock empty response
        mock_client.get.return_value = {"total": 0, "list": []}
        
        rel_client = RelationshipsClient(mock_client)
        
        result = rel_client.get_related("Account", "account_123", "contacts")
        
        assert isinstance(result, ListResponse)
        assert result.total == 0
        assert len(result.entities) == 0
    
    def test_self_referencing_relationships(self, mock_client):
        """Self-referencing relationships testi."""
        # Mock response for parent-child relationship
        mock_response = {
            "total": 1,
            "list": [{"id": "account_456", "name": "Child Account", "parentId": "account_123"}]
        }
        mock_client.get.return_value = mock_response
        
        rel_client = RelationshipsClient(mock_client)
        
        result = rel_client.get_related("Account", "account_123", "children")
        
        assert isinstance(result, ListResponse)
        assert len(result.entities) == 1
        assert result.entities[0].get("parentId") == "account_123"
    
    def test_circular_relationship_detection(self, mock_client):
        """Circular relationship detection testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Mock circular relationship attempt
        mock_client.post.side_effect = RelationshipError("Circular relationship detected")
        
        with pytest.raises(RelationshipError):
            rel_client.link("Account", "account_123", "parent", "account_123")  # Self-parent
    
    def test_invalid_relationship_types(self, mock_client):
        """Invalid relationship types testi."""
        rel_client = RelationshipsClient(mock_client)
        
        # Mock invalid relationship error
        mock_client.get.side_effect = ValidationError("Invalid relationship type")
        
        with pytest.raises(ValidationError):
            rel_client.get_related("Account", "account_123", "nonexistent_relation")
    
    def test_relationship_with_deleted_entities(self, mock_client):
        """Relationship with deleted entities testi."""
        # Mock response with deleted entity reference
        mock_response = {
            "total": 1,
            "list": [{"id": "contact_123", "deleted": True, "firstName": "Deleted Contact"}]
        }
        mock_client.get.return_value = mock_response
        
        rel_client = RelationshipsClient(mock_client)
        
        result = rel_client.get_related("Account", "account_123", "contacts")
        
        # Should handle deleted entities gracefully
        assert isinstance(result, ListResponse)
        assert len(result.entities) == 1
        assert result.entities[0].get("deleted") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])