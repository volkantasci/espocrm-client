"""
EspoCRM End-to-End Integration Tests

Tam workflow testleri - gerçek API simülasyonu ile.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
import responses
from datetime import datetime, timedelta

from espocrm.client import EspoCRMClient
from espocrm.config import ClientConfig
from espocrm.auth import create_api_key_auth, create_hmac_auth, create_basic_auth
from espocrm.models.entities import EntityRecord
from espocrm.models.search import SearchParams, WhereClause
from espocrm.exceptions import EspoCRMError, EspoCRMNotFoundError


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndWorkflows:
    """End-to-end workflow testleri."""
    
    @responses.activate
    def test_complete_account_lifecycle(self, mock_http_responses):
        """Complete account lifecycle testi."""
        # Setup client
        config = ClientConfig(
            base_url="https://test.espocrm.com",
            api_version="v1"
        )
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        # 1. Create Account
        account_data = {
            "name": "Integration Test Company",
            "type": "Customer",
            "industry": "Technology",
            "website": "https://integration-test.com",
            "phoneNumber": "+1-555-0123",
            "emailAddress": "info@integration-test.com"
        }
        
        created_account = client.crud.create("Account", account_data)
        
        # Assertions for creation
        assert isinstance(created_account, EntityRecord)
        assert created_account.entity_type == "Account"
        assert created_account.get("name") == "Integration Test Company"
        assert created_account.id is not None
        
        account_id = created_account.id
        
        # 2. Read Account
        read_account = client.crud.read("Account", account_id)
        
        # Assertions for read
        assert read_account.id == account_id
        assert read_account.get("name") == "Integration Test Company"
        assert read_account.get("type") == "Customer"
        
        # 3. Update Account
        update_data = {
            "industry": "Healthcare",
            "description": "Updated during integration test"
        }
        
        updated_account = client.crud.update("Account", account_id, update_data)
        
        # Assertions for update
        assert updated_account.get("industry") == "Healthcare"
        assert updated_account.get("description") == "Updated during integration test"
        assert updated_account.get("name") == "Integration Test Company"  # Unchanged
        
        # 4. Create related Contact
        contact_data = {
            "firstName": "John",
            "lastName": "Doe",
            "emailAddress": "john.doe@integration-test.com",
            "title": "Integration Manager",
            "accountId": account_id
        }
        
        created_contact = client.crud.create("Contact", contact_data)
        
        # Assertions for contact creation
        assert isinstance(created_contact, EntityRecord)
        assert created_contact.get("firstName") == "John"
        assert created_contact.get("accountId") == account_id
        
        contact_id = created_contact.id
        
        # 5. Link Contact to Account (if not auto-linked)
        link_result = client.relationships.link("Account", account_id, "contacts", contact_id)
        assert link_result is True
        
        # 6. Get Account's contacts
        account_contacts = client.relationships.get_related("Account", account_id, "contacts")
        
        # Assertions for relationships
        assert account_contacts.total >= 1
        contact_found = any(c.id == contact_id for c in account_contacts.entities)
        assert contact_found
        
        # 7. Search for Accounts
        search_params = SearchParams(
            where=[
                WhereClause(field="type", operator="equals", value="Customer"),
                WhereClause(field="industry", operator="equals", value="Healthcare")
            ],
            order_by="name",
            max_size=10
        )
        
        search_results = client.crud.list("Account", search_params=search_params)
        
        # Assertions for search
        assert search_results.total >= 1
        found_account = any(a.id == account_id for a in search_results.entities)
        assert found_account
        
        # 8. Stream operations
        stream_post_data = {
            "post": "Integration test completed successfully!",
            "type": "Post"
        }
        
        posted_item = client.stream.post("Account", account_id, stream_post_data)
        
        # Assertions for stream
        assert posted_item.data["post"] == "Integration test completed successfully!"
        
        # 9. Get Account stream
        account_stream = client.stream.get_stream("Account", account_id)
        
        # Assertions for stream retrieval
        assert account_stream.total >= 1
        
        # 10. Follow Account
        follow_result = client.stream.follow("Account", account_id)
        assert follow_result is True
        
        # 11. Unfollow Account
        unfollow_result = client.stream.unfollow("Account", account_id)
        assert unfollow_result is True
        
        # 12. Cleanup - Delete Contact
        contact_delete_result = client.crud.delete("Contact", contact_id)
        assert contact_delete_result is True
        
        # 13. Cleanup - Delete Account
        account_delete_result = client.crud.delete("Account", account_id)
        assert account_delete_result is True
        
        # 14. Verify deletion
        with pytest.raises(EspoCRMNotFoundError):
            client.crud.read("Account", account_id)
    
    @responses.activate
    def test_bulk_operations_workflow(self, mock_http_responses):
        """Bulk operations workflow testi."""
        # Setup client
        config = ClientConfig(base_url="https://test.espocrm.com")
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        # 1. Bulk create Accounts
        accounts_data = [
            {"name": f"Bulk Company {i}", "type": "Customer", "industry": "Technology"}
            for i in range(5)
        ]
        
        created_accounts = []
        for account_data in accounts_data:
            account = client.crud.create("Account", account_data)
            created_accounts.append(account)
        
        # Assertions for bulk creation
        assert len(created_accounts) == 5
        assert all(isinstance(acc, EntityRecord) for acc in created_accounts)
        assert all(acc.get("type") == "Customer" for acc in created_accounts)
        
        # 2. Bulk create Contacts for each Account
        created_contacts = []
        for i, account in enumerate(created_accounts):
            contact_data = {
                "firstName": f"Contact{i}",
                "lastName": "BulkTest",
                "emailAddress": f"contact{i}@bulktest.com",
                "accountId": account.id
            }
            contact = client.crud.create("Contact", contact_data)
            created_contacts.append(contact)
        
        # Assertions for bulk contact creation
        assert len(created_contacts) == 5
        
        # 3. Bulk link Contacts to Accounts
        for account, contact in zip(created_accounts, created_contacts):
            link_result = client.relationships.link("Account", account.id, "contacts", contact.id)
            assert link_result is True
        
        # 4. Bulk search and verify
        search_params = SearchParams(
            where=[WhereClause(field="type", operator="equals", value="Customer")],
            max_size=20
        )
        
        search_results = client.crud.list("Account", search_params=search_params)
        
        # Should find at least our 5 accounts
        assert search_results.total >= 5
        
        # 5. Bulk update
        for account in created_accounts:
            update_data = {"industry": "Healthcare"}
            client.crud.update("Account", account.id, update_data)
        
        # 6. Verify bulk update
        for account in created_accounts:
            updated_account = client.crud.read("Account", account.id)
            assert updated_account.get("industry") == "Healthcare"
        
        # 7. Bulk cleanup
        for contact in created_contacts:
            client.crud.delete("Contact", contact.id)
        
        for account in created_accounts:
            client.crud.delete("Account", account.id)
    
    @responses.activate
    def test_complex_relationship_workflow(self, mock_http_responses):
        """Complex relationship workflow testi."""
        # Setup client
        config = ClientConfig(base_url="https://test.espocrm.com")
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        # 1. Create Account
        account = client.crud.create("Account", {
            "name": "Relationship Test Company",
            "type": "Customer"
        })
        
        # 2. Create multiple Contacts
        contacts = []
        for i in range(3):
            contact = client.crud.create("Contact", {
                "firstName": f"Contact{i}",
                "lastName": "RelTest",
                "emailAddress": f"contact{i}@reltest.com",
                "accountId": account.id
            })
            contacts.append(contact)
        
        # 3. Create Opportunities
        opportunities = []
        for i in range(2):
            opportunity = client.crud.create("Opportunity", {
                "name": f"Opportunity {i}",
                "stage": "Prospecting",
                "amount": 10000 * (i + 1),
                "accountId": account.id
            })
            opportunities.append(opportunity)
        
        # 4. Link Contacts to Opportunities (many-to-many)
        for opportunity in opportunities:
            for contact in contacts:
                client.relationships.link("Opportunity", opportunity.id, "contacts", contact.id)
        
        # 5. Verify Account relationships
        account_contacts = client.relationships.get_related("Account", account.id, "contacts")
        assert len(account_contacts.entities) == 3
        
        account_opportunities = client.relationships.get_related("Account", account.id, "opportunities")
        assert len(account_opportunities.entities) == 2
        
        # 6. Verify Opportunity relationships
        for opportunity in opportunities:
            opp_contacts = client.relationships.get_related("Opportunity", opportunity.id, "contacts")
            assert len(opp_contacts.entities) == 3
        
        # 7. Verify Contact relationships
        for contact in contacts:
            contact_opportunities = client.relationships.get_related("Contact", contact.id, "opportunities")
            assert len(contact_opportunities.entities) == 2
        
        # 8. Unlink some relationships
        client.relationships.unlink("Opportunity", opportunities[0].id, "contacts", contacts[0].id)
        
        # 9. Verify unlink
        opp_contacts = client.relationships.get_related("Opportunity", opportunities[0].id, "contacts")
        assert len(opp_contacts.entities) == 2  # One less
        
        # 10. Cleanup
        for opportunity in opportunities:
            client.crud.delete("Opportunity", opportunity.id)
        
        for contact in contacts:
            client.crud.delete("Contact", contact.id)
        
        client.crud.delete("Account", account.id)
    
    @responses.activate
    def test_metadata_driven_workflow(self, mock_http_responses):
        """Metadata-driven workflow testi."""
        # Setup client
        config = ClientConfig(base_url="https://test.espocrm.com")
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        # 1. Get application metadata
        app_metadata = client.metadata.get_application_metadata()
        
        # Assertions for metadata
        assert app_metadata.has_entity("Account")
        assert app_metadata.has_entity("Contact")
        
        # 2. Get Account metadata
        account_metadata = client.metadata.get_entity_metadata("Account")
        
        # Assertions for entity metadata
        assert account_metadata.has_field("name")
        assert account_metadata.has_link("contacts")
        
        # 3. Discover required fields
        required_fields = account_metadata.get_required_fields()
        assert "name" in required_fields
        
        # 4. Create entity with only required fields
        minimal_data = {field: f"Test {field}" for field in required_fields}
        
        created_entity = client.crud.create("Account", minimal_data)
        assert isinstance(created_entity, EntityRecord)
        
        # 5. Validate data against metadata
        test_data = {
            "name": "Valid Company",
            "type": "Customer",
            "industry": "Technology"
        }
        
        validation_errors = client.metadata.validate_entity_data("Account", test_data)
        assert len(validation_errors) == 0  # Should be valid
        
        # 6. Test invalid data
        invalid_data = {
            "name": "",  # Required field empty
            "type": "InvalidType"  # Invalid enum value
        }
        
        validation_errors = client.metadata.validate_entity_data("Account", invalid_data)
        assert len(validation_errors) > 0  # Should have errors
        
        # 7. Cleanup
        client.crud.delete("Account", created_entity.id)
    
    @responses.activate
    def test_error_handling_workflow(self, mock_http_responses):
        """Error handling workflow testi."""
        # Setup client
        config = ClientConfig(base_url="https://test.espocrm.com")
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        # 1. Test entity not found
        with pytest.raises(EspoCRMNotFoundError):
            client.crud.read("Account", "nonexistent_id")
        
        # 2. Test validation error
        with pytest.raises(EspoCRMError):
            client.crud.create("Account", {})  # Missing required fields
        
        # 3. Test relationship error
        with pytest.raises(EspoCRMError):
            client.relationships.link("Account", "nonexistent", "contacts", "also_nonexistent")
        
        # 4. Test recovery after error
        # Create valid entity after error
        valid_account = client.crud.create("Account", {"name": "Recovery Test"})
        assert isinstance(valid_account, EntityRecord)
        
        # 5. Cleanup
        client.crud.delete("Account", valid_account.id)


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceIntegration:
    """Performance integration testleri."""
    
    @responses.activate
    def test_high_volume_operations(self, mock_http_responses, performance_timer):
        """High volume operations testi."""
        # Setup client
        config = ClientConfig(base_url="https://test.espocrm.com")
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        performance_timer.start()
        
        # Create 100 entities
        created_entities = []
        for i in range(100):
            entity = client.crud.create("Account", {
                "name": f"Performance Test {i}",
                "type": "Customer"
            })
            created_entities.append(entity)
        
        # Read all entities
        for entity in created_entities:
            read_entity = client.crud.read("Account", entity.id)
            assert read_entity.id == entity.id
        
        # Update all entities
        for entity in created_entities:
            client.crud.update("Account", entity.id, {"industry": "Technology"})
        
        # Delete all entities
        for entity in created_entities:
            client.crud.delete("Account", entity.id)
        
        performance_timer.stop()
        
        # Performance assertions
        assert performance_timer.elapsed < 30.0  # 30 saniyeden az
        assert len(created_entities) == 100
    
    @responses.activate
    def test_concurrent_operations_simulation(self, mock_http_responses):
        """Concurrent operations simulation testi."""
        import threading
        import queue
        
        # Setup client
        config = ClientConfig(base_url="https://test.espocrm.com")
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def worker(worker_id):
            try:
                # Each worker creates, reads, updates, deletes
                entity = client.crud.create("Account", {
                    "name": f"Concurrent Test {worker_id}",
                    "type": "Customer"
                })
                
                read_entity = client.crud.read("Account", entity.id)
                
                updated_entity = client.crud.update("Account", entity.id, {
                    "industry": "Technology"
                })
                
                delete_result = client.crud.delete("Account", entity.id)
                
                results.put({
                    "worker_id": worker_id,
                    "created": entity.id,
                    "read": read_entity.id,
                    "updated": updated_entity.get("industry"),
                    "deleted": delete_result
                })
                
            except Exception as e:
                errors.put({"worker_id": worker_id, "error": str(e)})
        
        # Start 10 concurrent workers
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert errors.qsize() == 0  # No errors
        assert results.qsize() == 10  # All workers completed
        
        # Verify all operations succeeded
        while not results.empty():
            result = results.get()
            assert result["created"] is not None
            assert result["read"] is not None
            assert result["updated"] == "Technology"
            assert result["deleted"] is True


@pytest.mark.integration
@pytest.mark.security
class TestSecurityIntegration:
    """Security integration testleri."""
    
    @responses.activate
    def test_authentication_workflow(self, mock_http_responses):
        """Authentication workflow testi."""
        config = ClientConfig(base_url="https://test.espocrm.com")
        
        # Test different auth methods
        auth_methods = [
            create_api_key_auth("test_api_key"),
            create_hmac_auth("test_key", "test_secret_key_with_sufficient_length"),
            create_basic_auth("testuser", password="strong_password_123")
        ]
        
        for auth in auth_methods:
            client = EspoCRMClient(config=config, auth=auth)
            
            # Test authenticated request
            entity = client.crud.create("Account", {"name": "Auth Test"})
            assert isinstance(entity, EntityRecord)
            
            # Cleanup
            client.crud.delete("Account", entity.id)
    
    @responses.activate
    def test_data_sanitization_workflow(self, mock_http_responses, security_test_data):
        """Data sanitization workflow testi."""
        config = EspoCRMConfig(base_url="https://test.espocrm.com")
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        # Test XSS prevention
        for payload in security_test_data["xss_payloads"]:
            with pytest.raises((EspoCRMError, ValueError)):
                client.crud.create("Account", {"name": payload})
        
        # Test SQL injection prevention
        for payload in security_test_data["sql_injection"]:
            search_params = SearchParams(
                where=[WhereClause(field="name", operator="equals", value=payload)]
            )
            
            # Should handle safely without injection
            try:
                client.crud.list("Account", search_params=search_params)
            except (EspoCRMError, ValueError):
                pass  # Expected for malicious payloads
    
    @responses.activate
    def test_rate_limiting_workflow(self, mock_http_responses):
        """Rate limiting workflow testi."""
        config = ClientConfig(
            base_url="https://test.espocrm.com",
            rate_limit=5,  # 5 requests per window
            rate_limit_window=1  # 1 second window
        )
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        # Make requests up to limit
        for i in range(5):
            entity = client.crud.create("Account", {"name": f"Rate Test {i}"})
            assert isinstance(entity, EntityRecord)
        
        # Next request should be rate limited
        with pytest.raises(EspoCRMError):
            client.crud.create("Account", {"name": "Rate Limited"})


@pytest.mark.integration
@pytest.mark.slow
class TestLongRunningWorkflows:
    """Long-running workflow testleri."""
    
    @responses.activate
    def test_session_persistence(self, mock_http_responses):
        """Session persistence testi."""
        config = ClientConfig(base_url="https://test.espocrm.com")
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        # Simulate long-running session
        entities = []
        
        # Create entities over time
        for i in range(10):
            entity = client.crud.create("Account", {
                "name": f"Session Test {i}",
                "type": "Customer"
            })
            entities.append(entity)
            
            # Simulate time passing
            time.sleep(0.1)
        
        # Verify all entities still accessible
        for entity in entities:
            read_entity = client.crud.read("Account", entity.id)
            assert read_entity.id == entity.id
        
        # Cleanup
        for entity in entities:
            client.crud.delete("Account", entity.id)
    
    @responses.activate
    def test_cache_behavior_over_time(self, mock_http_responses):
        """Cache behavior over time testi."""
        config = ClientConfig(base_url="https://test.espocrm.com")
        auth = create_api_key_auth("test_api_key_123")
        client = EspoCRMClient(config=config, auth=auth)
        
        # Get metadata (should be cached)
        metadata1 = client.metadata.get_application_metadata()
        
        # Get metadata again (should use cache)
        metadata2 = client.metadata.get_application_metadata()
        
        # Should be same instance or equivalent
        assert metadata1.entity_defs.keys() == metadata2.entity_defs.keys()
        
        # Clear cache
        client.metadata.clear_cache()
        
        # Get metadata again (should fetch fresh)
        metadata3 = client.metadata.get_application_metadata()
        assert metadata3.entity_defs.keys() == metadata1.entity_defs.keys()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])