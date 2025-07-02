"""
EspoCRM Attachments Client Test Module

Attachment operasyonları için kapsamlı testler.
"""

import pytest
import json
import io
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
import responses

from espocrm.clients.attachments import AttachmentsClient
from espocrm.models.attachments import Attachment, AttachmentInfo
from espocrm.models.entities import Entity
from espocrm.models.responses import ListResponse, AttachmentResponse
from espocrm.exceptions import (
    EspoCRMError,
    EntityNotFoundError,
    ValidationError,
    AttachmentError
)


@pytest.mark.unit
@pytest.mark.attachments
class TestAttachmentsClient:
    """Attachments Client temel testleri."""
    
    def test_attachments_client_initialization(self, mock_client):
        """Attachments client initialization testi."""
        att_client = AttachmentsClient(mock_client)
        
        assert att_client.client == mock_client
        assert att_client.base_url == mock_client.base_url
        assert att_client.api_version == mock_client.api_version
    
    def test_upload_file_success(self, mock_client):
        """File upload başarı testi."""
        # Mock response setup
        mock_response = {
            "id": "attachment_123",
            "name": "test_document.pdf",
            "type": "application/pdf",
            "size": 1024,
            "createdAt": "2024-01-01T10:00:00+00:00",
            "createdById": "user_123"
        }
        mock_client.post.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        # Mock file data
        file_data = b"PDF file content"
        file_name = "test_document.pdf"
        content_type = "application/pdf"
        
        with patch("builtins.open", mock_open(read_data=file_data)):
            result = att_client.upload_file(file_name, content_type=content_type)
        
        # Assertions
        assert isinstance(result, Attachment)
        assert result.id == "attachment_123"
        assert result.name == "test_document.pdf"
        assert result.type == "application/pdf"
        assert result.size == 1024
        
        # API call verification
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "Attachment" in call_args[0][0]
        assert "files" in call_args[1]
    
    def test_upload_file_from_bytes(self, mock_client):
        """Bytes'tan file upload testi."""
        # Mock response setup
        mock_response = {
            "id": "attachment_456",
            "name": "data.txt",
            "type": "text/plain",
            "size": 11
        }
        mock_client.post.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        # File data as bytes
        file_data = b"Hello World"
        file_name = "data.txt"
        
        result = att_client.upload_from_bytes(file_data, file_name, content_type="text/plain")
        
        # Assertions
        assert isinstance(result, Attachment)
        assert result.id == "attachment_456"
        assert result.name == "data.txt"
        assert result.size == 11
    
    def test_upload_file_with_metadata(self, mock_client):
        """Metadata ile file upload testi."""
        # Mock response setup
        mock_response = {
            "id": "attachment_789",
            "name": "report.xlsx",
            "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "size": 2048,
            "description": "Monthly report"
        }
        mock_client.post.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        file_data = b"Excel file content"
        metadata = {
            "description": "Monthly report",
            "tags": ["report", "monthly"],
            "category": "Reports"
        }
        
        with patch("builtins.open", mock_open(read_data=file_data)):
            result = att_client.upload_file(
                "report.xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                metadata=metadata
            )
        
        # Assertions
        assert isinstance(result, Attachment)
        assert result.description == "Monthly report"
    
    def test_download_file_success(self, mock_client):
        """File download başarı testi."""
        # Mock response setup
        file_content = b"Downloaded file content"
        mock_response = Mock()
        mock_response.content = file_content
        mock_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Disposition": "attachment; filename=document.pdf"
        }
        mock_client.get.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        result = att_client.download_file("attachment_123")
        
        # Assertions
        assert result == file_content
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Attachment/attachment_123/download",
            stream=True
        )
    
    def test_download_file_to_path(self, mock_client):
        """File download to path testi."""
        # Mock response setup
        file_content = b"Downloaded file content"
        mock_response = Mock()
        mock_response.content = file_content
        mock_response.iter_content.return_value = [file_content]
        mock_client.get.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch("builtins.open", mock_open()) as mock_file:
                result = att_client.download_file_to_path("attachment_123", temp_path)
            
            # Assertions
            assert result == temp_path
            mock_file.assert_called_once_with(temp_path, "wb")
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_attachment_info_success(self, mock_client):
        """Attachment info alma başarı testi."""
        # Mock response setup
        mock_response = {
            "id": "attachment_123",
            "name": "document.pdf",
            "type": "application/pdf",
            "size": 1024,
            "createdAt": "2024-01-01T10:00:00+00:00",
            "createdById": "user_123",
            "parentType": "Account",
            "parentId": "account_123"
        }
        mock_client.get.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        result = att_client.get_attachment_info("attachment_123")
        
        # Assertions
        assert isinstance(result, AttachmentInfo)
        assert result.id == "attachment_123"
        assert result.name == "document.pdf"
        assert result.parent_type == "Account"
        assert result.parent_id == "account_123"
        
        # API call verification
        mock_client.get.assert_called_once_with("Attachment/attachment_123")
    
    def test_delete_attachment_success(self, mock_client):
        """Attachment silme başarı testi."""
        # Mock response setup
        mock_client.delete.return_value = {"deleted": True}
        
        att_client = AttachmentsClient(mock_client)
        
        result = att_client.delete_attachment("attachment_123")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.delete.assert_called_once_with("Attachment/attachment_123")
    
    def test_get_entity_attachments_success(self, mock_client):
        """Entity attachments alma başarı testi."""
        # Mock response setup
        mock_response = {
            "total": 2,
            "list": [
                {
                    "id": "attachment_1",
                    "name": "document1.pdf",
                    "type": "application/pdf",
                    "size": 1024
                },
                {
                    "id": "attachment_2",
                    "name": "image.jpg",
                    "type": "image/jpeg",
                    "size": 2048
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        result = att_client.get_entity_attachments("Account", "account_123")
        
        # Assertions
        assert isinstance(result, ListResponse)
        assert result.total == 2
        assert len(result.entities) == 2
        assert all(isinstance(att, Attachment) for att in result.entities)
        
        # API call verification
        mock_client.get.assert_called_once_with(
            "Account/account_123/attachments"
        )
    
    def test_attach_to_entity_success(self, mock_client):
        """Entity'ye attachment bağlama başarı testi."""
        # Mock response setup
        mock_client.post.return_value = {"attached": True}
        
        att_client = AttachmentsClient(mock_client)
        
        result = att_client.attach_to_entity("attachment_123", "Account", "account_123")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.post.assert_called_once_with(
            "Account/account_123/attachments",
            data={"attachmentId": "attachment_123"}
        )
    
    def test_detach_from_entity_success(self, mock_client):
        """Entity'den attachment ayırma başarı testi."""
        # Mock response setup
        mock_client.delete.return_value = {"detached": True}
        
        att_client = AttachmentsClient(mock_client)
        
        result = att_client.detach_from_entity("attachment_123", "Account", "account_123")
        
        # Assertions
        assert result is True
        
        # API call verification
        mock_client.delete.assert_called_once_with(
            "Account/account_123/attachments/attachment_123"
        )


@pytest.mark.unit
@pytest.mark.attachments
@pytest.mark.parametrize
class TestAttachmentsClientParametrized:
    """Attachments Client parametrized testleri."""
    
    @pytest.mark.parametrize("file_type,content_type", [
        ("pdf", "application/pdf"),
        ("jpg", "image/jpeg"),
        ("png", "image/png"),
        ("txt", "text/plain"),
        ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    ])
    def test_upload_different_file_types(self, mock_client, file_type, content_type):
        """Farklı file türleri için upload testi."""
        # Mock response
        mock_response = {
            "id": f"attachment_{file_type}",
            "name": f"test.{file_type}",
            "type": content_type,
            "size": 1024
        }
        mock_client.post.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        file_data = b"File content"
        with patch("builtins.open", mock_open(read_data=file_data)):
            result = att_client.upload_file(f"test.{file_type}", content_type=content_type)
        
        assert isinstance(result, Attachment)
        assert result.type == content_type
        mock_client.post.assert_called_once()
    
    @pytest.mark.parametrize("entity_type", ["Account", "Contact", "Lead", "Opportunity"])
    def test_get_attachments_different_entities(self, mock_client, entity_type):
        """Farklı entity türleri için attachments alma testi."""
        # Mock response
        mock_response = {"total": 1, "list": [{"id": "att_1", "name": "file.pdf"}]}
        mock_client.get.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        result = att_client.get_entity_attachments(entity_type, "entity_123")
        
        assert isinstance(result, ListResponse)
        mock_client.get.assert_called_once_with(f"{entity_type}/entity_123/attachments")
    
    @pytest.mark.parametrize("error_class,status_code", [
        (EntityNotFoundError, 404),
        (ValidationError, 400),
        (AttachmentError, 422),
        (EspoCRMError, 500)
    ])
    def test_attachment_error_handling(self, mock_client, error_class, status_code):
        """Attachment error handling testi."""
        mock_client.get.side_effect = error_class(f"Error {status_code}")
        
        att_client = AttachmentsClient(mock_client)
        
        with pytest.raises(error_class):
            att_client.get_attachment_info("test_id")


@pytest.mark.unit
@pytest.mark.attachments
@pytest.mark.validation
class TestAttachmentsClientValidation:
    """Attachments Client validation testleri."""
    
    def test_file_path_validation(self, mock_client):
        """File path validation testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Empty file path
        with pytest.raises(ValidationError):
            att_client.upload_file("")
        
        # None file path
        with pytest.raises(ValidationError):
            att_client.upload_file(None)
        
        # Non-existent file
        with pytest.raises(ValidationError):
            att_client.upload_file("/nonexistent/file.pdf")
    
    def test_file_size_validation(self, mock_client):
        """File size validation testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Too large file (simulate)
        large_data = b"A" * (100 * 1024 * 1024)  # 100MB
        
        with pytest.raises(ValidationError):
            att_client.upload_from_bytes(large_data, "large_file.bin")
    
    def test_content_type_validation(self, mock_client):
        """Content type validation testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Invalid content type
        with pytest.raises(ValidationError):
            att_client.upload_from_bytes(b"data", "file.txt", content_type="invalid/type")
        
        # Dangerous content type
        with pytest.raises(ValidationError):
            att_client.upload_from_bytes(b"data", "script.exe", content_type="application/x-executable")
    
    def test_attachment_id_validation(self, mock_client):
        """Attachment ID validation testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Empty attachment ID
        with pytest.raises(ValidationError):
            att_client.get_attachment_info("")
        
        # None attachment ID
        with pytest.raises(ValidationError):
            att_client.get_attachment_info(None)
        
        # Invalid attachment ID format
        with pytest.raises(ValidationError):
            att_client.get_attachment_info("invalid id")
    
    def test_entity_validation(self, mock_client):
        """Entity validation testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Empty entity type
        with pytest.raises(ValidationError):
            att_client.get_entity_attachments("", "id")
        
        # Empty entity ID
        with pytest.raises(ValidationError):
            att_client.get_entity_attachments("Account", "")
    
    def test_file_name_validation(self, mock_client):
        """File name validation testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Invalid file names
        invalid_names = [
            "",
            None,
            "file with spaces.txt",  # Spaces might be problematic
            "file\nwith\nnewlines.txt",
            "file<with>html.txt",
            "../../../etc/passwd",  # Path traversal
            "CON.txt",  # Windows reserved name
            "file" + "A" * 300 + ".txt"  # Too long
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError):
                att_client.upload_from_bytes(b"data", invalid_name)


@pytest.mark.unit
@pytest.mark.attachments
@pytest.mark.performance
class TestAttachmentsClientPerformance:
    """Attachments Client performance testleri."""
    
    def test_bulk_upload_performance(self, mock_client, performance_timer):
        """Bulk upload performance testi."""
        # Mock response
        mock_client.post.return_value = {
            "id": "attachment_new",
            "name": "test.txt",
            "type": "text/plain",
            "size": 10
        }
        
        att_client = AttachmentsClient(mock_client)
        
        # 20 file upload et
        files_data = [(b"File content", f"file_{i}.txt") for i in range(20)]
        
        performance_timer.start()
        results = []
        for file_data, file_name in files_data:
            result = att_client.upload_from_bytes(file_data, file_name)
            results.append(result)
        performance_timer.stop()
        
        # Performance assertions
        assert len(results) == 20
        assert performance_timer.elapsed < 5.0  # 5 saniyeden az
        assert mock_client.post.call_count == 20
    
    def test_large_file_upload_performance(self, mock_client, performance_timer):
        """Large file upload performance testi."""
        # Mock response
        mock_client.post.return_value = {
            "id": "attachment_large",
            "name": "large_file.bin",
            "type": "application/octet-stream",
            "size": 10 * 1024 * 1024  # 10MB
        }
        
        att_client = AttachmentsClient(mock_client)
        
        # 10MB file
        large_data = b"A" * (10 * 1024 * 1024)
        
        performance_timer.start()
        result = att_client.upload_from_bytes(large_data, "large_file.bin")
        performance_timer.stop()
        
        # Performance assertions
        assert isinstance(result, Attachment)
        assert performance_timer.elapsed < 10.0  # 10 saniyeden az
    
    def test_bulk_download_performance(self, mock_client, performance_timer):
        """Bulk download performance testi."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b"Downloaded content"
        mock_client.get.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        # 20 file download et
        attachment_ids = [f"attachment_{i}" for i in range(20)]
        
        performance_timer.start()
        results = []
        for att_id in attachment_ids:
            result = att_client.download_file(att_id)
            results.append(result)
        performance_timer.stop()
        
        # Performance assertions
        assert len(results) == 20
        assert performance_timer.elapsed < 3.0  # 3 saniyeden az
        assert mock_client.get.call_count == 20


@pytest.mark.integration
@pytest.mark.attachments
class TestAttachmentsClientIntegration:
    """Attachments Client integration testleri."""
    
    @responses.activate
    def test_full_attachment_workflow(self, real_client, mock_http_responses):
        """Full attachment workflow integration testi."""
        att_client = AttachmentsClient(real_client)
        
        # 1. Upload file
        file_data = b"Test file content for integration"
        uploaded_attachment = att_client.upload_from_bytes(
            file_data, 
            "integration_test.txt",
            content_type="text/plain"
        )
        assert isinstance(uploaded_attachment, Attachment)
        
        # 2. Get attachment info
        att_info = att_client.get_attachment_info(uploaded_attachment.id)
        assert isinstance(att_info, AttachmentInfo)
        assert att_info.name == "integration_test.txt"
        
        # 3. Attach to entity
        attach_result = att_client.attach_to_entity(
            uploaded_attachment.id, 
            "Account", 
            "account_123"
        )
        assert attach_result is True
        
        # 4. Get entity attachments
        entity_attachments = att_client.get_entity_attachments("Account", "account_123")
        assert isinstance(entity_attachments, ListResponse)
        
        # 5. Download file
        downloaded_content = att_client.download_file(uploaded_attachment.id)
        assert downloaded_content == file_data
        
        # 6. Detach from entity
        detach_result = att_client.detach_from_entity(
            uploaded_attachment.id,
            "Account", 
            "account_123"
        )
        assert detach_result is True
        
        # 7. Delete attachment
        delete_result = att_client.delete_attachment(uploaded_attachment.id)
        assert delete_result is True
    
    def test_attachment_error_recovery(self, real_client):
        """Attachment error recovery testi."""
        att_client = AttachmentsClient(real_client)
        
        # Network error simulation
        with patch.object(real_client, 'post', side_effect=ConnectionError("Network error")):
            with pytest.raises(EspoCRMError):
                att_client.upload_from_bytes(b"data", "test.txt")
        
        # Recovery after network error
        mock_response = {"id": "att_123", "name": "test.txt", "type": "text/plain", "size": 4}
        with patch.object(real_client, 'post', return_value=mock_response):
            result = att_client.upload_from_bytes(b"data", "test.txt")
            assert isinstance(result, Attachment)


@pytest.mark.unit
@pytest.mark.attachments
@pytest.mark.security
class TestAttachmentsClientSecurity:
    """Attachments Client security testleri."""
    
    def test_file_type_security(self, mock_client):
        """File type security testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Dangerous file types
        dangerous_files = [
            ("virus.exe", "application/x-executable"),
            ("script.bat", "application/x-bat"),
            ("malware.scr", "application/x-screensaver"),
            ("trojan.com", "application/x-msdos-program"),
            ("backdoor.pif", "application/x-pif")
        ]
        
        for file_name, content_type in dangerous_files:
            with pytest.raises((ValidationError, AttachmentError)):
                att_client.upload_from_bytes(b"malicious content", file_name, content_type)
    
    def test_path_traversal_prevention(self, mock_client, security_test_data):
        """Path traversal prevention testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Path traversal in file names
        for payload in security_test_data["path_traversal"]:
            with pytest.raises((ValidationError, AttachmentError)):
                att_client.upload_from_bytes(b"data", payload)
    
    def test_attachment_access_control(self, mock_client):
        """Attachment access control testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Unauthorized access simulation
        mock_client.get.side_effect = EspoCRMError("Unauthorized", status_code=401)
        
        with pytest.raises(EspoCRMError):
            att_client.get_attachment_info("attachment_123")
        
        # Forbidden download
        mock_client.get.side_effect = EspoCRMError("Forbidden", status_code=403)
        
        with pytest.raises(EspoCRMError):
            att_client.download_file("attachment_123")
    
    def test_file_content_scanning(self, mock_client, security_test_data):
        """File content scanning testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Malicious content patterns
        malicious_contents = [
            b"<script>alert('xss')</script>",  # XSS in file
            b"<?php system($_GET['cmd']); ?>",  # PHP backdoor
            b"eval(base64_decode('malicious_code'))",  # Encoded malicious code
        ]
        
        for content in malicious_contents:
            with pytest.raises((ValidationError, AttachmentError)):
                att_client.upload_from_bytes(content, "suspicious.txt")
    
    def test_attachment_metadata_sanitization(self, mock_client, security_test_data):
        """Attachment metadata sanitization testi."""
        att_client = AttachmentsClient(mock_client)
        
        # XSS in metadata
        for payload in security_test_data["xss_payloads"]:
            metadata = {
                "description": payload,  # Malicious payload
                "tags": [payload]
            }
            
            with pytest.raises((ValidationError, AttachmentError)):
                att_client.upload_from_bytes(b"data", "file.txt", metadata=metadata)


@pytest.mark.unit
@pytest.mark.attachments
@pytest.mark.edge_cases
class TestAttachmentsClientEdgeCases:
    """Attachments Client edge cases testleri."""
    
    def test_empty_file_upload(self, mock_client):
        """Empty file upload testi."""
        att_client = AttachmentsClient(mock_client)
        
        # Empty file content
        with pytest.raises(ValidationError):
            att_client.upload_from_bytes(b"", "empty.txt")
    
    def test_zero_byte_file(self, mock_client):
        """Zero byte file testi."""
        # Mock response for zero byte file
        mock_response = {
            "id": "attachment_zero",
            "name": "zero.txt",
            "type": "text/plain",
            "size": 0
        }
        mock_client.post.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        # Should handle zero byte files
        result = att_client.upload_from_bytes(b"", "zero.txt", allow_empty=True)
        assert isinstance(result, Attachment)
        assert result.size == 0
    
    def test_unicode_filename_handling(self, mock_client):
        """Unicode filename handling testi."""
        # Mock response
        mock_response = {
            "id": "attachment_unicode",
            "name": "файл.txt",  # Cyrillic filename
            "type": "text/plain",
            "size": 10
        }
        mock_client.post.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        # Unicode filename should be handled properly
        result = att_client.upload_from_bytes(b"unicode test", "файл.txt")
        assert isinstance(result, Attachment)
        assert result.name == "файл.txt"
    
    def test_attachment_without_extension(self, mock_client):
        """Extension olmayan attachment testi."""
        # Mock response
        mock_response = {
            "id": "attachment_no_ext",
            "name": "README",
            "type": "text/plain",
            "size": 20
        }
        mock_client.post.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        result = att_client.upload_from_bytes(b"README file content", "README")
        assert isinstance(result, Attachment)
        assert result.name == "README"
    
    def test_corrupted_download_handling(self, mock_client):
        """Corrupted download handling testi."""
        # Mock corrupted response
        mock_response = Mock()
        mock_response.content = b"corrupted data"
        mock_response.headers = {"Content-Length": "1000"}  # Wrong size
        mock_client.get.return_value = mock_response
        
        att_client = AttachmentsClient(mock_client)
        
        # Should detect size mismatch
        with pytest.raises(AttachmentError):
            att_client.download_file("attachment_123", verify_size=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])