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
from espocrm.models.stream import StreamNote, StreamNoteType
from espocrm.exceptions import (
    EspoCRMError,
    EspoCRMValidationError
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
        assert stream_client.logger == mock_client.logger
    
    def test_list_user_stream_success(self, mock_client):
        """User stream listeleme başarı testi."""
        # Mock response setup
        mock_response = {
            "total": 3,
            "list": [
                {
                    "id": "675a1b2c3d4e5f6a7",
                    "type": "Post",
                    "data": {"post": "This is a test post"},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T10:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6a9"
                },
                {
                    "id": "675a1b2c3d4e5f6b0",
                    "type": "Update",
                    "data": {"fields": {"name": "New Name", "industry": "Technology"}},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T09:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6b1"
                },
                {
                    "id": "675a1b2c3d4e5f6b2",
                    "type": "Status",
                    "data": {"value": "Active"},
                    "parentType": "Account", 
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T08:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6b3"
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.list_user_stream(offset=0, max_size=20)
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, StreamNote) for item in result)
        assert result[0].type == StreamNoteType.POST
        assert result[1].type == StreamNoteType.UPDATE
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Stream",
            params={'offset': 0, 'maxSize': 20}
        )
    
    def test_list_entity_stream_success(self, mock_client):
        """Entity stream listeleme başarı testi."""
        # Mock response setup
        mock_response = {
            "total": 2,
            "list": [
                {
                    "id": "675a1b2c3d4e5f6a7",
                    "type": "Post",
                    "data": {"post": "Entity specific post"},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T10:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6a9"
                },
                {
                    "id": "675a1b2c3d4e5f6b0",
                    "type": "Update",
                    "data": {"fields": {"name": "Updated Name"}},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T09:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6b1"
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.list_entity_stream("Account", "675a1b2c3d4e5f6a8")
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, StreamNote) for item in result)
        assert result[0].parent_type == "Account"
        assert result[0].parent_id == "675a1b2c3d4e5f6a8"
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Account/675a1b2c3d4e5f6a8/stream",
            params={'offset': 0, 'maxSize': 20}
        )
    
    def test_post_to_stream_success(self, mock_client):
        """Stream'e post gönderme başarı testi."""
        # Mock response setup
        mock_response = {
            "id": "675a1b2c3d4e5f6c0",
            "type": "Post",
            "post": "New stream post",
            "data": {"post": "New stream post"},
            "parentType": "Account",
            "parentId": "675a1b2c3d4e5f6a8",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        }
        mock_client.post.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.post_to_stream(
            parent_type="Account",
            parent_id="675a1b2c3d4e5f6a8", 
            post="New stream post"
        )
        
        # Assertions
        assert isinstance(result, StreamNote)
        assert result.id == "675a1b2c3d4e5f6c0"
        assert result.post == "New stream post"
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Note",
            data={
                'type': 'Post',
                'post': 'New stream post',
                'parentType': 'Account',
                'parentId': '675a1b2c3d4e5f6a8'
            }
        )
    
    def test_follow_entity_success(self, mock_client):
        """Entity follow başarı testi."""
        # Mock response setup
        mock_client.put.return_value = {"success": True}
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.follow_entity("Account", "675a1b2c3d4e5f6a8")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.put.assert_called_once_with(
            "Account/675a1b2c3d4e5f6a8/subscription"
        )
    
    def test_unfollow_entity_success(self, mock_client):
        """Entity unfollow başarı testi."""
        # Mock response setup
        mock_client.delete.return_value = {"success": True}
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.unfollow_entity("Account", "675a1b2c3d4e5f6a8")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.delete.assert_called_once_with(
            "Account/675a1b2c3d4e5f6a8/subscription"
        )
    
    def test_is_following_entity_success(self, mock_client):
        """Entity takip durumu kontrol testi."""
        # Mock response setup
        mock_client.get.return_value = {"isFollowing": True}
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.is_following_entity("Account", "675a1b2c3d4e5f6a8")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Account/675a1b2c3d4e5f6a8/subscription"
        )
    
    def test_get_stream_note_success(self, mock_client):
        """Stream note getirme başarı testi."""
        # Mock response setup
        mock_response = {
            "id": "675a1b2c3d4e5f6c0",
            "type": "Post",
            "post": "Retrieved note",
            "data": {"post": "Retrieved note"},
            "parentType": "Account",
            "parentId": "675a1b2c3d4e5f6a8",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.get_stream_note("675a1b2c3d4e5f6c0")
        
        # Assertions
        assert isinstance(result, StreamNote)
        assert result.id == "675a1b2c3d4e5f6c0"
        assert result.post == "Retrieved note"
        
        # API call verification
        mock_client.get.assert_called_once_with("Note/675a1b2c3d4e5f6c0")
    
    def test_delete_stream_note_success(self, mock_client):
        """Stream note silme başarı testi."""
        # Mock response setup
        mock_client.delete.return_value = {"success": True}
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.delete_stream_note("675a1b2c3d4e5f6c0")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.delete.assert_called_once_with("Note/675a1b2c3d4e5f6c0")


@pytest.mark.unit
@pytest.mark.stream
class TestStreamClientParametrized:
    """Stream Client parametrized testleri."""
    
    @pytest.mark.parametrize("entity_type", ["Account", "Contact", "Lead", "Opportunity"])
    def test_list_entity_stream_different_entities(self, mock_client, entity_type):
        """Farklı entity türleri için stream alma testi."""
        # Mock response
        mock_response = {
            "total": 1, 
            "list": [{
                "id": "675a1b2c3d4e5f6a7",
                "type": "Post",
                "data": {"post": "Test post"},
                "parentType": entity_type,
                "parentId": "675a1b2c3d4e5f6a8",
                "createdAt": "2024-01-01T10:00:00+00:00",
                "createdById": "675a1b2c3d4e5f6a9"
            }]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.list_entity_stream(entity_type, "675a1b2c3d4e5f6a8")
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].parent_type == entity_type
        mock_client.get.assert_called_once_with(
            f"{entity_type}/675a1b2c3d4e5f6a8/stream",
            params={'offset': 0, 'maxSize': 20}
        )
    
    @pytest.mark.parametrize("error_class,status_code", [
        (EspoCRMError, 404),
        (EspoCRMValidationError, 400),
        (EspoCRMError, 422),
        (EspoCRMError, 500)
    ])
    def test_stream_error_handling(self, mock_client, error_class, status_code):
        """Stream error handling testi."""
        mock_client.get.side_effect = error_class(f"Error {status_code}")
        
        stream_client = StreamClient(mock_client)
        
        with pytest.raises(error_class):
            stream_client.list_entity_stream("Account", "675a1b2c3d4e5f6a8")


@pytest.mark.unit
@pytest.mark.stream
@pytest.mark.validation
class TestStreamClientValidation:
    """Stream Client validation testleri."""
    
    def test_post_to_stream_with_attachments(self, mock_client):
        """Attachment'lı stream post testi."""
        # Mock response setup
        mock_response = {
            "id": "675a1b2c3d4e5f6c0",
            "type": "Post",
            "data": {
                "post": "Post with attachments",
                "attachmentsIds": ["675a1b2c3d4e5f6d0"]
            },
            "parentType": "Account",
            "parentId": "675a1b2c3d4e5f6a8",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        }
        mock_client.post.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.post_to_stream(
            parent_type="Account",
            parent_id="675a1b2c3d4e5f6a8",
            post="Post with attachments",
            attachments_ids=["675a1b2c3d4e5f6d0"]
        )
        
        # Assertions
        assert isinstance(result, StreamNote)
        assert result.id == "675a1b2c3d4e5f6c0"
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Note",
            data={
                'type': 'Post',
                'post': 'Post with attachments',
                'parentType': 'Account',
                'parentId': '675a1b2c3d4e5f6a8',
                'attachmentsIds': ['675a1b2c3d4e5f6d0']
            }
        )
    
    def test_post_to_stream_internal_note(self, mock_client):
        """Internal note post testi."""
        # Mock response setup
        mock_response = {
            "id": "675a1b2c3d4e5f6c0",
            "type": "Post",
            "data": {
                "post": "Internal note",
                "isInternal": True
            },
            "parentType": "Account",
            "parentId": "675a1b2c3d4e5f6a8",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        }
        mock_client.post.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.post_to_stream(
            parent_type="Account",
            parent_id="675a1b2c3d4e5f6a8",
            post="Internal note",
            is_internal=True
        )
        
        # Assertions
        assert isinstance(result, StreamNote)
        assert result.id == "675a1b2c3d4e5f6c0"
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Note",
            data={
                'type': 'Post',
                'post': 'Internal note',
                'parentType': 'Account',
                'parentId': '675a1b2c3d4e5f6a8',
                'isInternal': True
            }
        )


@pytest.mark.unit
@pytest.mark.stream
@pytest.mark.performance
class TestStreamClientPerformance:
    """Stream Client performance testleri."""
    
    def test_bulk_stream_fetch_performance(self, mock_client, performance_timer):
        """Bulk stream fetch performance testi."""
        # Mock large response
        large_stream = []
        for i in range(100):
            large_stream.append({
                "id": f"675a1b2c3d4e5f{i:03d}",
                "type": "Post",
                "data": {"post": f"Post {i}"},
                "parentType": "Account",
                "parentId": "675a1b2c3d4e5f6a8",
                "createdAt": "2024-01-01T10:00:00+00:00",
                "createdById": "675a1b2c3d4e5f6a9"
            })
        
        mock_client.get.return_value = {"total": 100, "list": large_stream}
        
        stream_client = StreamClient(mock_client)
        
        performance_timer.start()
        result = stream_client.list_entity_stream("Account", "675a1b2c3d4e5f6a8", max_size=100)
        performance_timer.stop()
        
        # Performance assertions
        assert len(result) == 100
        assert performance_timer.elapsed < 2.0  # 2 saniyeden az
    
    def test_follow_unfollow_performance(self, mock_client, performance_timer):
        """Follow/unfollow performance testi."""
        # Mock responses
        mock_client.put.return_value = {"success": True}
        mock_client.delete.return_value = {"success": True}
        
        stream_client = StreamClient(mock_client)
        
        # 25 follow/unfollow operation
        entity_ids = [f"675a1b2c3d4e5f{i:03d}" for i in range(25)]
        
        performance_timer.start()
        for entity_id in entity_ids:
            stream_client.follow_entity("Account", entity_id)
            stream_client.unfollow_entity("Account", entity_id)
        performance_timer.stop()
        
        # Performance assertions
        assert performance_timer.elapsed < 3.0  # 3 saniyeden az
        assert mock_client.put.call_count == 25
        assert mock_client.delete.call_count == 25


@pytest.mark.integration
@pytest.mark.stream
class TestStreamClientIntegration:
    """Stream Client integration testleri."""
    
    def test_full_stream_workflow(self, mock_client):
        """Full stream workflow integration testi."""
        stream_client = StreamClient(mock_client)
        
        # Mock responses for workflow
        mock_client.get.side_effect = [
            # Initial stream
            {
                "total": 1,
                "list": [{
                    "id": "675a1b2c3d4e5f6a7",
                    "type": "Post",
                    "data": {"post": "Initial post"},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T10:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6a9"
                }]
            },
            # Updated stream
            {
                "total": 2,
                "list": [{
                    "id": "675a1b2c3d4e5f6a7",
                    "type": "Post",
                    "data": {"post": "Initial post"},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T10:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6a9"
                }, {
                    "id": "675a1b2c3d4e5f6c0",
                    "type": "Post",
                    "data": {"post": "Integration test post"},
                    "parentType": "Account",
                    "parentId": "675a1b2c3d4e5f6a8",
                    "createdAt": "2024-01-01T12:00:00+00:00",
                    "createdById": "675a1b2c3d4e5f6a9"
                }]
            }
        ]
        
        mock_client.post.return_value = {
            "id": "675a1b2c3d4e5f6c0",
            "type": "Post",
            "post": "Integration test post",
            "data": {"post": "Integration test post"},
            "parentType": "Account",
            "parentId": "675a1b2c3d4e5f6a8",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        }
        
        mock_client.put.return_value = {"success": True}
        mock_client.delete.return_value = {"success": True}
        
        # 1. Get initial stream
        initial_stream = stream_client.list_entity_stream("Account", "675a1b2c3d4e5f6a8")
        initial_count = len(initial_stream)
        assert initial_count == 1
        
        # 2. Post to stream
        posted_item = stream_client.post_to_stream(
            parent_type="Account",
            parent_id="675a1b2c3d4e5f6a8",
            post="Integration test post"
        )
        assert isinstance(posted_item, StreamNote)
        
        # 3. Follow entity
        follow_result = stream_client.follow_entity("Account", "675a1b2c3d4e5f6a8")
        assert follow_result is True
        
        # 4. Get updated stream
        updated_stream = stream_client.list_entity_stream("Account", "675a1b2c3d4e5f6a8")
        assert len(updated_stream) >= initial_count
        
        # 5. Unfollow entity
        unfollow_result = stream_client.unfollow_entity("Account", "675a1b2c3d4e5f6a8")
        assert unfollow_result is True
    
    def test_stream_error_recovery(self, real_client):
        """Stream error recovery testi."""
        stream_client = StreamClient(real_client)
        
        # Network error simulation
        with patch.object(real_client, 'get', side_effect=ConnectionError("Network error")):
            with pytest.raises(EspoCRMError):
                stream_client.list_entity_stream("Account", "675a1b2c3d4e5f6a8")
        
        # Recovery after network error
        mock_response = {
            "total": 1, 
            "list": [{
                "id": "675a1b2c3d4e5f6a7",
                "type": "Post",
                "data": {"post": "Recovery test"},
                "parentType": "Account",
                "parentId": "675a1b2c3d4e5f6a8",
                "createdAt": "2024-01-01T10:00:00+00:00",
                "createdById": "675a1b2c3d4e5f6a9"
            }]
        }
        with patch.object(real_client, 'get', return_value=mock_response):
            result = stream_client.list_entity_stream("Account", "675a1b2c3d4e5f6a8")
            assert isinstance(result, list)
            assert len(result) == 1


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
            stream_client.list_entity_stream("Account", "675a1b2c3d4e5f6a8")
        
        # Forbidden stream post
        mock_client.post.side_effect = EspoCRMError("Forbidden", status_code=403)
        
        with pytest.raises(EspoCRMError):
            stream_client.post_to_stream("Account", "675a1b2c3d4e5f6a8", "Test post")
    
    def test_stream_rate_limiting(self, mock_client):
        """Stream rate limiting testi."""
        stream_client = StreamClient(mock_client)
        
        # Rate limit simulation
        mock_client.post.side_effect = EspoCRMError("Rate limit exceeded", status_code=429)
        
        with pytest.raises(EspoCRMError):
            stream_client.post_to_stream("Account", "675a1b2c3d4e5f6a8", "Test post")


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
        
        result = stream_client.list_entity_stream("Account", "675a1b2c3d4e5f6a8")
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_convenience_methods(self, mock_client):
        """Convenience methods testi."""
        # Mock response setup
        mock_response = {
            "id": "675a1b2c3d4e5f6c0",
            "type": "Post",
            "data": {"post": "Account post"},
            "parentType": "Account",
            "parentId": "675a1b2c3d4e5f6a8",
            "createdAt": "2024-01-01T12:00:00+00:00",
            "createdById": "675a1b2c3d4e5f6a9"
        }
        mock_client.post.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        # Test convenience method
        result = stream_client.post_to_account("675a1b2c3d4e5f6a8", "Account post")
        
        assert isinstance(result, StreamNote)
        assert result.parent_type == "Account"
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Note",
            data={
                'type': 'Post',
                'post': 'Account post',
                'parentType': 'Account',
                'parentId': '675a1b2c3d4e5f6a8'
            }
        )
    
    def test_stream_with_filtering(self, mock_client):
        """Stream filtering testi."""
        # Mock response
        mock_response = {
            "total": 1,
            "list": [{
                "id": "675a1b2c3d4e5f6a7",
                "type": "Post",
                "data": {"post": "Filtered post"},
                "parentType": "Account",
                "parentId": "675a1b2c3d4e5f6a8",
                "createdAt": "2024-01-01T10:00:00+00:00",
                "createdById": "675a1b2c3d4e5f6a9"
            }]
        }
        mock_client.get.return_value = mock_response
        
        stream_client = StreamClient(mock_client)
        
        result = stream_client.list_entity_stream(
            "Account", 
            "675a1b2c3d4e5f6a8",
            offset=10,
            max_size=5,
            after="2024-01-01T00:00:00+00:00",
            filter="posts"
        )
        
        assert isinstance(result, list)
        assert len(result) == 1
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Account/675a1b2c3d4e5f6a8/stream",
            params={
                'offset': 10,
                'maxSize': 5,
                'after': '2024-01-01T00:00:00+00:00',
                'filter': 'posts'
            }
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])