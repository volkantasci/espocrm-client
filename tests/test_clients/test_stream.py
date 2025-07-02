"""
EspoCRM Stream Client Test Module

Stream operasyonları için kapsamlı testler.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import responses

from espocrm.clients.stream import StreamClient
from espocrm.models.stream import StreamPost, StreamNote, StreamUpdate
from espocrm.models.entities import Entity
from espocrm.models.responses import ListResponse, StreamResponse
from espocrm.models.search import SearchParams, WhereClause
from espocrm.exceptions import (
    EspoCRMError,
    EntityNotFoundError,
    ValidationError,
    StreamError
)


@pytest.mark.unit
@pytest.mark.stream
class TestStreamClient:
    """Stream Client temel testleri."""
    
    def test_stream_client_initialization(self, mock_client):
        """Stream client initialization testi."""
        stream_client = StreamClient(mock_client)
        
        assert stream_client.client == mock_client
        assert stream_client.base_url == mock_client.base_url
        assert stream_client.api_version == mock_client.api_version
    
    def test_get_entity_stream_success(self, mock_client):
        """Entity stream alma başarı testi."""
        # Mock response setup
        mock_response = {
            "total": 3,
            "list": [
                {
                    "id": "stream_1",
                    "type": "Post",
                    "data": {"post": "This is a test post"},
                    "parentType": "Account",
                    "parentId": "account_123",
                    "createdAt": "2024-01-01T10:00:00+00:00",
                    "createdById": "user_123"
                },
                {
                    "id": "stream_2", 
                    "type": "Update",
                    "data": {"fields": ["name", "industry"]},
                    "parentType": "Account",
                    "parentId": "account_123",
                    "createdAt": "2024-01-01T09:00:00+00:00",
                    "createdById": "user_456"
                },
                {
                    "id": "stream_3",
                    "type": "Status",
                    "data": {"value": "Active"},
                    "parentType": "Account", 
                    "parentId": "account_123",
                    "createdAt": "2024-01-01T08:00:00+00:00",
                    "createdById": "user_789"
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.get_stream("Account", "account_123")
        
        # Assertions
        assert isinstance(result, StreamResponse)
        assert result.total == 3
        assert len(result.items) == 3
        assert all(hasattr(item, 'type') for item in result.items)
        assert result.items[0].type == "Post"
        assert result.items[1].type == "Update"
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Account/account_123/stream",
            params={}
        )
    
    def test_get_stream_with_params(self, mock_client):
        """Stream parametreli alma testi."""
        # Mock response setup
        mock_response = {"total": 1, "list": [{"id": "stream_1", "type": "Post"}]}
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        # Search parameters
        search_params = SearchParams(
            where=[
                WhereClause(field="type", operator="equals", value="Post")
            ],
            order_by="createdAt",
            order="desc",
            max_size=20
        )
        
        result = stream_client.get_stream("Account", "account_123", search_params)
        
        # Assertions
        assert isinstance(result, StreamResponse)
        
        # API call verification
        expected_params = search_params.to_query_params()
        mock_client.get.assert_called_once_with(
            "Account/account_123/stream",
            params=expected_params
        )
    
    def test_post_to_stream_success(self, mock_client):
        """Stream'e post gönderme başarı testi."""
        # Mock response setup
        mock_response = {
            "id": "stream_new",
            "type": "Post",
            "data": {"post": "New stream post"},
            "parentType": "Account",
            "parentId": "account_123",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "user_123"
        }
        mock_client.post.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        post_data = {
            "post": "New stream post",
            "type": "Post"
        }
        
        result = stream_client.post("Account", "account_123", post_data)
        
        # Assertions
        assert isinstance(result, StreamPost)
        assert result.id == "stream_new"
        assert result.data["post"] == "New stream post"
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Account/account_123/stream",
            data=post_data
        )
    
    def test_post_note_to_stream(self, mock_client):
        """Stream'e note gönderme testi."""
        # Mock response setup
        mock_response = {
            "id": "stream_note",
            "type": "Note",
            "data": {"post": "Important note about this account"},
            "parentType": "Account",
            "parentId": "account_123",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "user_123"
        }
        mock_client.post.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.post_note("Account", "account_123", "Important note about this account")
        
        # Assertions
        assert isinstance(result, StreamNote)
        assert result.data["post"] == "Important note about this account"
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Account/account_123/stream",
            data={
                "post": "Important note about this account",
                "type": "Note"
            }
        )
    
    def test_follow_entity_success(self, mock_client):
        """Entity follow başarı testi."""
        # Mock response setup
        mock_client.put.return_value = {"followed": True}
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.follow("Account", "account_123")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.put.assert_called_once_with(
            "Account/account_123/subscription"
        )
    
    def test_unfollow_entity_success(self, mock_client):
        """Entity unfollow başarı testi."""
        # Mock response setup
        mock_client.delete.return_value = {"unfollowed": True}
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.unfollow("Account", "account_123")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.delete.assert_called_once_with(
            "Account/account_123/subscription"
        )
    
    def test_get_followers_success(self, mock_client):
        """Entity followers alma başarı testi."""
        # Mock response setup
        mock_response = {
            "total": 2,
            "list": [
                {"id": "user_123", "name": "John Doe", "type": "User"},
                {"id": "user_456", "name": "Jane Smith", "type": "User"}
            ]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.get_followers("Account", "account_123")
        
        # Assertions
        assert isinstance(result, ListResponse)
        assert result.total == 2
        assert len(result.entities) == 2
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Account/account_123/followers"
        )
    
    def test_delete_stream_post_success(self, mock_client):
        """Stream post silme başarı testi."""
        # Mock response setup
        mock_client.delete.return_value = {"deleted": True}
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.delete_post("stream_123")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.delete.assert_called_once_with(
            "Stream/stream_123"
        )
    
    def test_get_global_stream_success(self, mock_client):
        """Global stream alma başarı testi."""
        # Mock response setup
        mock_response = {
            "total": 5,
            "list": [
                {"id": "stream_1", "type": "Post", "parentType": "Account"},
                {"id": "stream_2", "type": "Update", "parentType": "Contact"},
                {"id": "stream_3", "type": "Create", "parentType": "Lead"}
            ]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.get_global_stream()
        
        # Assertions
        assert isinstance(result, StreamResponse)
        assert result.total == 5
        assert len(result.items) == 3
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Stream",
            params={}
        )


@pytest.mark.unit
@pytest.mark.stream
@pytest.mark.parametrize
class TestStreamClientParametrized:
    """Stream Client parametrized testleri."""
    
    @pytest.mark.parametrize("entity_type", ["Account", "Contact", "Lead", "Opportunity"])
    def test_get_stream_different_entities(self, mock_client, entity_type):
        """Farklı entity türleri için stream alma testi."""
        # Mock response
        mock_response = {"total": 1, "list": [{"id": "stream_1", "type": "Post"}]}
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.get_stream(entity_type, "entity_123")
        
        assert isinstance(result, StreamResponse)
        mock_client.get.assert_called_once_with(
            f"{entity_type}/entity_123/stream",
            params={}
        )
    
    @pytest.mark.parametrize("post_type", ["Post", "Note", "Update", "Status"])
    def test_post_different_types(self, mock_client, post_type):
        """Farklı post türleri için stream post testi."""
        # Mock response
        mock_response = {
            "id": "stream_new",
            "type": post_type,
            "data": {"post": f"Test {post_type}"},
            "parentType": "Account",
            "parentId": "account_123"
        }
        mock_client.post.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        post_data = {
            "post": f"Test {post_type}",
            "type": post_type
        }
        
        result = stream_client.post("Account", "account_123", post_data)
        
        assert result.type == post_type
        mock_client.post.assert_called_once()
    
    @pytest.mark.parametrize("error_class,status_code", [
        (EntityNotFoundError, 404),
        (ValidationError, 400),
        (StreamError, 422),
        (EspoCRMError, 500)
    ])
    def test_stream_error_handling(self, mock_client, error_class, status_code):
        """Stream error handling testi."""
        mock_client.get.side_effect = error_class(f"Error {status_code}")
        
        stream_client = StreamClient(mock_client)
        
        with pytest.raises(error_class):
            stream_client.get_stream("Account", "test_id")


@pytest.mark.unit
@pytest.mark.stream
@pytest.mark.validation
class TestStreamClientValidation:
    """Stream Client validation testleri."""
    
    def test_entity_type_validation(self, mock_client):
        """Entity type validation testi."""
        stream_client = StreamClient(mock_client)
        
        # Empty entity type
        with pytest.raises(ValidationError):
            stream_client.get_stream("", "id")
        
        # None entity type
        with pytest.raises(ValidationError):
            stream_client.get_stream(None, "id")
    
    def test_entity_id_validation(self, mock_client):
        """Entity ID validation testi."""
        stream_client = StreamClient(mock_client)
        
        # Empty entity ID
        with pytest.raises(ValidationError):
            stream_client.get_stream("Account", "")
        
        # None entity ID
        with pytest.raises(ValidationError):
            stream_client.get_stream("Account", None)
    
    def test_post_data_validation(self, mock_client):
        """Post data validation testi."""
        stream_client = StreamClient(mock_client)
        
        # Empty post data
        with pytest.raises(ValidationError):
            stream_client.post("Account", "id", {})
        
        # None post data
        with pytest.raises(ValidationError):
            stream_client.post("Account", "id", None)
        
        # Invalid post data type
        with pytest.raises(ValidationError):
            stream_client.post("Account", "id", "invalid_data")
    
    def test_note_content_validation(self, mock_client):
        """Note content validation testi."""
        stream_client = StreamClient(mock_client)
        
        # Empty note content
        with pytest.raises(ValidationError):
            stream_client.post_note("Account", "id", "")
        
        # None note content
        with pytest.raises(ValidationError):
            stream_client.post_note("Account", "id", None)
        
        # Too long note content
        long_content = "A" * 10000
        with pytest.raises(ValidationError):
            stream_client.post_note("Account", "id", long_content)
    
    def test_stream_post_id_validation(self, mock_client):
        """Stream post ID validation testi."""
        stream_client = StreamClient(mock_client)
        
        # Empty post ID
        with pytest.raises(ValidationError):
            stream_client.delete_post("")
        
        # None post ID
        with pytest.raises(ValidationError):
            stream_client.delete_post(None)


@pytest.mark.unit
@pytest.mark.stream
@pytest.mark.performance
class TestStreamClientPerformance:
    """Stream Client performance testleri."""
    
    def test_bulk_post_performance(self, mock_client, performance_timer):
        """Bulk post performance testi."""
        # Mock response
        mock_client.post.return_value = {
            "id": "stream_new",
            "type": "Post",
            "data": {"post": "Test post"}
        }
        
        stream_client = StreamClient(mock_client)
        
        # 50 post gönder
        posts_data = [{"post": f"Post {i}", "type": "Post"} for i in range(50)]
        
        performance_timer.start()
        results = []
        for post_data in posts_data:
            result = stream_client.post("Account", "account_123", post_data)
            results.append(result)
        performance_timer.stop()
        
        # Performance assertions
        assert len(results) == 50
        assert performance_timer.elapsed < 3.0  # 3 saniyeden az
        assert mock_client.post.call_count == 50
    
    def test_large_stream_fetch_performance(self, mock_client, performance_timer):
        """Large stream fetch performance testi."""
        # Mock large response
        large_stream = [
            {"id": f"stream_{i}", "type": "Post", "data": {"post": f"Post {i}"}}
            for i in range(1000)
        ]
        mock_client.get.return_value = {"total": 1000, "list": large_stream}
        
        stream_client = StreamClient(mock_client)
        
        performance_timer.start()
        result = stream_client.get_stream("Account", "account_123")
        performance_timer.stop()
        
        # Performance assertions
        assert len(result.items) == 1000
        assert performance_timer.elapsed < 2.0  # 2 saniyeden az
    
    def test_follow_unfollow_performance(self, mock_client, performance_timer):
        """Follow/unfollow performance testi."""
        # Mock responses
        mock_client.put.return_value = {"followed": True}
        mock_client.delete.return_value = {"unfollowed": True}
        
        stream_client = StreamClient(mock_client)
        
        # 100 follow/unfollow operation
        entity_ids = [f"account_{i}" for i in range(50)]
        
        performance_timer.start()
        for entity_id in entity_ids:
            stream_client.follow("Account", entity_id)
            stream_client.unfollow("Account", entity_id)
        performance_timer.stop()
        
        # Performance assertions
        assert performance_timer.elapsed < 5.0  # 5 saniyeden az
        assert mock_client.put.call_count == 50
        assert mock_client.delete.call_count == 50


@pytest.mark.integration
@pytest.mark.stream
class TestStreamClientIntegration:
    """Stream Client integration testleri."""
    
    @responses.activate
    def test_full_stream_workflow(self, real_client, mock_http_responses):
        """Full stream workflow integration testi."""
        stream_client = StreamClient(real_client)
        
        # 1. Get initial stream
        initial_stream = stream_client.get_stream("Account", "account_123")
        initial_count = len(initial_stream.items)
        
        # 2. Post to stream
        post_data = {"post": "Integration test post", "type": "Post"}
        posted_item = stream_client.post("Account", "account_123", post_data)
        assert isinstance(posted_item, StreamPost)
        
        # 3. Follow entity
        follow_result = stream_client.follow("Account", "account_123")
        assert follow_result is True
        
        # 4. Get updated stream
        updated_stream = stream_client.get_stream("Account", "account_123")
        assert len(updated_stream.items) >= initial_count
        
        # 5. Unfollow entity
        unfollow_result = stream_client.unfollow("Account", "account_123")
        assert unfollow_result is True
    
    @responses.activate
    def test_stream_filtering_workflow(self, real_client, mock_http_responses):
        """Stream filtering workflow testi."""
        stream_client = StreamClient(real_client)
        
        # Filter by post type
        search_params = SearchParams(
            where=[
                WhereClause(field="type", operator="equals", value="Post")
            ],
            order_by="createdAt",
            order="desc",
            max_size=10
        )
        
        result = stream_client.get_stream("Account", "account_123", search_params)
        
        assert isinstance(result, StreamResponse)
        # Verify filtering worked (all items should be Posts)
        for item in result.items:
            assert item.type == "Post"
    
    def test_stream_error_recovery(self, real_client):
        """Stream error recovery testi."""
        stream_client = StreamClient(real_client)
        
        # Network error simulation
        with patch.object(real_client, 'get', side_effect=ConnectionError("Network error")):
            with pytest.raises(EspoCRMError):
                stream_client.get_stream("Account", "account_123")
        
        # Recovery after network error
        mock_response = {"total": 1, "list": [{"id": "stream_1", "type": "Post"}]}
        with patch.object(real_client, 'get', return_value=mock_response):
            result = stream_client.get_stream("Account", "account_123")
            assert isinstance(result, StreamResponse)


@pytest.mark.unit
@pytest.mark.stream
@pytest.mark.security
class TestStreamClientSecurity:
    """Stream Client security testleri."""
    
    def test_stream_access_control(self, mock_client):
        """Stream access control testi."""
        stream_client = StreamClient(mock_client)
        
        # Unauthorized access simulation
        mock_client.get.side_effect = EspoCRMError("Unauthorized", status_code=401)
        
        with pytest.raises(EspoCRMError):
            stream_client.get_stream("Account", "account_123")
        
        # Forbidden stream post
        mock_client.post.side_effect = EspoCRMError("Forbidden", status_code=403)
        
        with pytest.raises(EspoCRMError):
            stream_client.post("Account", "account_123", {"post": "Test", "type": "Post"})
    
    def test_stream_content_sanitization(self, mock_client, security_test_data):
        """Stream content sanitization testi."""
        stream_client = StreamClient(mock_client)
        
        # XSS in stream posts
        for payload in security_test_data["xss_payloads"]:
            post_data = {
                "post": payload,  # Malicious payload
                "type": "Post"
            }
            
            with pytest.raises((ValidationError, EspoCRMError)):
                stream_client.post("Account", "account_123", post_data)
    
    def test_stream_injection_prevention(self, mock_client, security_test_data):
        """Stream injection prevention testi."""
        stream_client = StreamClient(mock_client)
        
        # SQL injection in stream queries
        for payload in security_test_data["sql_injection"]:
            search_params = SearchParams(
                where=[WhereClause(field="data", operator="contains", value=payload)]
            )
            
            with pytest.raises((ValidationError, EspoCRMError)):
                stream_client.get_stream("Account", "account_123", search_params)
    
    def test_stream_rate_limiting(self, mock_client):
        """Stream rate limiting testi."""
        stream_client = StreamClient(mock_client)
        
        # Rate limit simulation
        mock_client.post.side_effect = EspoCRMError("Rate limit exceeded", status_code=429)
        
        with pytest.raises(EspoCRMError):
            stream_client.post("Account", "account_123", {"post": "Test", "type": "Post"})


@pytest.mark.unit
@pytest.mark.stream
@pytest.mark.edge_cases
class TestStreamClientEdgeCases:
    """Stream Client edge cases testleri."""
    
    def test_empty_stream(self, mock_client):
        """Empty stream testi."""
        # Mock empty response
        mock_client.get.return_value = {"total": 0, "list": []}
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.get_stream("Account", "account_123")
        
        assert isinstance(result, StreamResponse)
        assert result.total == 0
        assert len(result.items) == 0
    
    def test_malformed_stream_data(self, mock_client):
        """Malformed stream data testi."""
        # Mock malformed response
        mock_response = {
            "total": 1,
            "list": [
                {"id": "stream_1"}  # Missing required fields
            ]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        # Should handle malformed data gracefully
        result = stream_client.get_stream("Account", "account_123")
        assert isinstance(result, StreamResponse)
    
    def test_very_old_stream_posts(self, mock_client):
        """Very old stream posts testi."""
        # Mock response with very old posts
        old_date = "2020-01-01T00:00:00+00:00"
        mock_response = {
            "total": 1,
            "list": [
                {
                    "id": "stream_old",
                    "type": "Post",
                    "data": {"post": "Very old post"},
                    "createdAt": old_date
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.get_stream("Account", "account_123")
        
        assert isinstance(result, StreamResponse)
        assert len(result.items) == 1
        assert result.items[0].created_at == old_date
    
    def test_stream_with_attachments(self, mock_client):
        """Stream with attachments testi."""
        # Mock response with attachment data
        mock_response = {
            "total": 1,
            "list": [
                {
                    "id": "stream_attachment",
                    "type": "Post",
                    "data": {
                        "post": "Post with attachment",
                        "attachments": [
                            {"id": "attachment_1", "name": "document.pdf", "type": "application/pdf"}
                        ]
                    }
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.get_stream("Account", "account_123")
        
        assert isinstance(result, StreamResponse)
        assert len(result.items) == 1
        assert "attachments" in result.items[0].data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])