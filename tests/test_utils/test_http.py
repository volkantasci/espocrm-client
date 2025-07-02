"""
EspoCRM HTTP Utilities Test Module

HTTP utilities için kapsamlı testler.
"""

import pytest
import requests
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import responses
import time

from espocrm.utils.http import (
    HTTPClient,
    RequestBuilder,
    ResponseHandler,
    RetryHandler,
    RateLimiter,
    HTTPError,
    TimeoutError,
    ConnectionError
)
from espocrm.exceptions import (
    EspoCRMError,
    RateLimitError,
    ValidationError
)


@pytest.mark.unit
@pytest.mark.utils
class TestHTTPClient:
    """HTTP Client temel testleri."""
    
    def test_http_client_initialization(self):
        """HTTP client initialization testi."""
        base_url = "https://test.espocrm.com"
        timeout = 30
        max_retries = 3
        
        client = HTTPClient(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Assertions
        assert client.base_url == base_url
        assert client.timeout == timeout
        assert client.max_retries == max_retries
        assert isinstance(client.session, requests.Session)
    
    @responses.activate
    def test_get_request_success(self):
        """GET request başarı testi."""
        # Mock response
        responses.add(
            responses.GET,
            "https://test.espocrm.com/api/v1/Account/123",
            json={"id": "123", "name": "Test Company"},
            status=200
        )
        
        client = HTTPClient("https://test.espocrm.com")
        
        result = client.get("api/v1/Account/123")
        
        # Assertions
        assert isinstance(result, dict)
        assert result["id"] == "123"
        assert result["name"] == "Test Company"
    
    @responses.activate
    def test_post_request_success(self):
        """POST request başarı testi."""
        # Mock response
        responses.add(
            responses.POST,
            "https://test.espocrm.com/api/v1/Account",
            json={"id": "new_123", "name": "New Company"},
            status=201
        )
        
        client = HTTPClient("https://test.espocrm.com")
        
        data = {"name": "New Company", "type": "Customer"}
        result = client.post("api/v1/Account", data=data)
        
        # Assertions
        assert isinstance(result, dict)
        assert result["id"] == "new_123"
        assert result["name"] == "New Company"
    
    @responses.activate
    def test_put_request_success(self):
        """PUT request başarı testi."""
        # Mock response
        responses.add(
            responses.PUT,
            "https://test.espocrm.com/api/v1/Account/123",
            json={"id": "123", "name": "Updated Company"},
            status=200
        )
        
        client = HTTPClient("https://test.espocrm.com")
        
        data = {"name": "Updated Company"}
        result = client.put("api/v1/Account/123", data=data)
        
        # Assertions
        assert result["name"] == "Updated Company"
    
    @responses.activate
    def test_delete_request_success(self):
        """DELETE request başarı testi."""
        # Mock response
        responses.add(
            responses.DELETE,
            "https://test.espocrm.com/api/v1/Account/123",
            json={"deleted": True},
            status=200
        )
        
        client = HTTPClient("https://test.espocrm.com")
        
        result = client.delete("api/v1/Account/123")
        
        # Assertions
        assert result["deleted"] is True
    
    @responses.activate
    def test_request_with_headers(self):
        """Headers ile request testi."""
        # Mock response
        responses.add(
            responses.GET,
            "https://test.espocrm.com/api/v1/Account",
            json={"total": 0, "list": []},
            status=200
        )
        
        client = HTTPClient("https://test.espocrm.com")
        
        headers = {
            "X-Api-Key": "test_api_key",
            "Content-Type": "application/json"
        }
        
        result = client.get("api/v1/Account", headers=headers)
        
        # Assertions
        assert isinstance(result, dict)
        
        # Verify headers were sent
        request = responses.calls[0].request
        assert request.headers["X-Api-Key"] == "test_api_key"
        assert request.headers["Content-Type"] == "application/json"
    
    @responses.activate
    def test_request_with_params(self):
        """Query parameters ile request testi."""
        # Mock response
        responses.add(
            responses.GET,
            "https://test.espocrm.com/api/v1/Account",
            json={"total": 1, "list": [{"id": "123"}]},
            status=200
        )
        
        client = HTTPClient("https://test.espocrm.com")
        
        params = {
            "where": [{"type": "equals", "attribute": "type", "value": "Customer"}],
            "maxSize": 20,
            "offset": 0
        }
        
        result = client.get("api/v1/Account", params=params)
        
        # Assertions
        assert isinstance(result, dict)
        assert result["total"] == 1
    
    @responses.activate
    def test_error_response_handling(self):
        """Error response handling testi."""
        # Mock error response
        responses.add(
            responses.GET,
            "https://test.espocrm.com/api/v1/Account/nonexistent",
            json={"error": "Not Found"},
            status=404
        )
        
        client = HTTPClient("https://test.espocrm.com")
        
        with pytest.raises(EspoCRMError) as exc_info:
            client.get("api/v1/Account/nonexistent")
        
        assert exc_info.value.status_code == 404
        assert "Not Found" in str(exc_info.value)
    
    def test_timeout_handling(self):
        """Timeout handling testi."""
        client = HTTPClient("https://test.espocrm.com", timeout=0.001)  # Very short timeout
        
        with patch('requests.Session.request') as mock_request:
            mock_request.side_effect = requests.exceptions.Timeout("Request timeout")
            
            with pytest.raises(TimeoutError):
                client.get("api/v1/Account")
    
    def test_connection_error_handling(self):
        """Connection error handling testi."""
        client = HTTPClient("https://nonexistent.espocrm.com")
        
        with patch('requests.Session.request') as mock_request:
            mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            with pytest.raises(ConnectionError):
                client.get("api/v1/Account")


@pytest.mark.unit
@pytest.mark.utils
class TestRequestBuilder:
    """Request Builder testleri."""
    
    def test_request_builder_initialization(self):
        """Request builder initialization testi."""
        base_url = "https://test.espocrm.com"
        builder = RequestBuilder(base_url)
        
        assert builder.base_url == base_url
        assert builder.method is None
        assert builder.path is None
        assert builder.headers == {}
        assert builder.params == {}
        assert builder.data is None
    
    def test_request_builder_method_chaining(self):
        """Request builder method chaining testi."""
        builder = RequestBuilder("https://test.espocrm.com")
        
        request = (builder
                  .method("GET")
                  .path("api/v1/Account")
                  .header("X-Api-Key", "test_key")
                  .param("maxSize", 20)
                  .build())
        
        # Assertions
        assert request.method == "GET"
        assert request.url == "https://test.espocrm.com/api/v1/Account"
        assert request.headers["X-Api-Key"] == "test_key"
        assert request.params["maxSize"] == 20
    
    def test_request_builder_with_data(self):
        """Request builder with data testi."""
        builder = RequestBuilder("https://test.espocrm.com")
        
        data = {"name": "Test Company", "type": "Customer"}
        
        request = (builder
                  .method("POST")
                  .path("api/v1/Account")
                  .data(data)
                  .build())
        
        # Assertions
        assert request.method == "POST"
        assert request.data == data
    
    def test_request_builder_url_construction(self):
        """Request builder URL construction testi."""
        builder = RequestBuilder("https://test.espocrm.com")
        
        # Test various path formats
        test_cases = [
            ("api/v1/Account", "https://test.espocrm.com/api/v1/Account"),
            ("/api/v1/Account", "https://test.espocrm.com/api/v1/Account"),
            ("api/v1/Account/123", "https://test.espocrm.com/api/v1/Account/123"),
            ("", "https://test.espocrm.com/")
        ]
        
        for path, expected_url in test_cases:
            request = builder.path(path).build()
            assert request.url == expected_url
    
    def test_request_builder_headers_merging(self):
        """Request builder headers merging testi."""
        builder = RequestBuilder("https://test.espocrm.com")
        
        request = (builder
                  .header("Content-Type", "application/json")
                  .header("X-Api-Key", "test_key")
                  .headers({"Authorization": "Bearer token", "Accept": "application/json"})
                  .build())
        
        # Assertions
        assert request.headers["Content-Type"] == "application/json"
        assert request.headers["X-Api-Key"] == "test_key"
        assert request.headers["Authorization"] == "Bearer token"
        assert request.headers["Accept"] == "application/json"
    
    def test_request_builder_params_merging(self):
        """Request builder params merging testi."""
        builder = RequestBuilder("https://test.espocrm.com")
        
        request = (builder
                  .param("maxSize", 20)
                  .param("offset", 0)
                  .params({"orderBy": "name", "order": "asc"})
                  .build())
        
        # Assertions
        assert request.params["maxSize"] == 20
        assert request.params["offset"] == 0
        assert request.params["orderBy"] == "name"
        assert request.params["order"] == "asc"


@pytest.mark.unit
@pytest.mark.utils
class TestResponseHandler:
    """Response Handler testleri."""
    
    def test_successful_json_response_handling(self):
        """Successful JSON response handling testi."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"id": "123", "name": "Test"}
        mock_response.text = '{"id": "123", "name": "Test"}'
        
        handler = ResponseHandler()
        result = handler.handle(mock_response)
        
        # Assertions
        assert isinstance(result, dict)
        assert result["id"] == "123"
        assert result["name"] == "Test"
    
    def test_successful_text_response_handling(self):
        """Successful text response handling testi."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "Plain text response"
        mock_response.json.side_effect = ValueError("No JSON")
        
        handler = ResponseHandler()
        result = handler.handle(mock_response)
        
        # Assertions
        assert result == "Plain text response"
    
    def test_error_response_handling(self):
        """Error response handling testi."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"error": "Bad Request", "message": "Invalid data"}
        mock_response.text = '{"error": "Bad Request", "message": "Invalid data"}'
        
        handler = ResponseHandler()
        
        with pytest.raises(EspoCRMError) as exc_info:
            handler.handle(mock_response)
        
        assert exc_info.value.status_code == 400
        assert "Bad Request" in str(exc_info.value)
    
    def test_malformed_json_response_handling(self):
        """Malformed JSON response handling testi."""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid JSON content"
        
        handler = ResponseHandler()
        
        # Should fallback to text
        result = handler.handle(mock_response)
        assert result == "Invalid JSON content"
    
    def test_empty_response_handling(self):
        """Empty response handling testi."""
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 204  # No Content
        mock_response.headers = {}
        mock_response.text = ""
        mock_response.json.side_effect = ValueError("No JSON")
        
        handler = ResponseHandler()
        result = handler.handle(mock_response)
        
        # Assertions
        assert result == ""


@pytest.mark.unit
@pytest.mark.utils
class TestRetryHandler:
    """Retry Handler testleri."""
    
    def test_retry_handler_initialization(self):
        """Retry handler initialization testi."""
        max_retries = 3
        backoff_factor = 2.0
        
        handler = RetryHandler(max_retries=max_retries, backoff_factor=backoff_factor)
        
        assert handler.max_retries == max_retries
        assert handler.backoff_factor == backoff_factor
        assert handler.retry_count == 0
    
    def test_should_retry_logic(self):
        """Should retry logic testi."""
        handler = RetryHandler(max_retries=3)
        
        # Test retryable errors
        retryable_errors = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.Timeout("Request timeout"),
            requests.exceptions.HTTPError("500 Server Error")
        ]
        
        for error in retryable_errors:
            assert handler.should_retry(error) is True
        
        # Test non-retryable errors
        non_retryable_errors = [
            requests.exceptions.HTTPError("400 Bad Request"),
            requests.exceptions.HTTPError("401 Unauthorized"),
            requests.exceptions.HTTPError("403 Forbidden"),
            requests.exceptions.HTTPError("404 Not Found")
        ]
        
        for error in non_retryable_errors:
            assert handler.should_retry(error) is False
    
    def test_retry_count_limit(self):
        """Retry count limit testi."""
        handler = RetryHandler(max_retries=2)
        
        # First retry
        handler.retry_count = 1
        assert handler.should_retry(requests.exceptions.ConnectionError()) is True
        
        # Second retry
        handler.retry_count = 2
        assert handler.should_retry(requests.exceptions.ConnectionError()) is False
    
    def test_backoff_calculation(self):
        """Backoff calculation testi."""
        handler = RetryHandler(max_retries=3, backoff_factor=2.0)
        
        # Test backoff times
        assert handler.get_backoff_time(1) == 2.0  # 2^1 * 1
        assert handler.get_backoff_time(2) == 4.0  # 2^2 * 1
        assert handler.get_backoff_time(3) == 8.0  # 2^3 * 1
    
    def test_retry_execution(self):
        """Retry execution testi."""
        handler = RetryHandler(max_retries=2, backoff_factor=0.1)  # Fast backoff for testing
        
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.ConnectionError("Connection failed")
            return "Success"
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = handler.execute_with_retry(failing_function)
        
        # Assertions
        assert result == "Success"
        assert call_count == 3  # Initial call + 2 retries


@pytest.mark.unit
@pytest.mark.utils
class TestRateLimiter:
    """Rate Limiter testleri."""
    
    def test_rate_limiter_initialization(self):
        """Rate limiter initialization testi."""
        max_requests = 100
        time_window = 60
        
        limiter = RateLimiter(max_requests=max_requests, time_window=time_window)
        
        assert limiter.max_requests == max_requests
        assert limiter.time_window == time_window
        assert len(limiter.requests) == 0
    
    def test_rate_limiting_within_limit(self):
        """Rate limiting within limit testi."""
        limiter = RateLimiter(max_requests=5, time_window=60)
        
        # Make requests within limit
        for i in range(5):
            assert limiter.is_allowed() is True
            limiter.record_request()
        
        # Should still be allowed (exactly at limit)
        assert limiter.is_allowed() is True
    
    def test_rate_limiting_exceeds_limit(self):
        """Rate limiting exceeds limit testi."""
        limiter = RateLimiter(max_requests=3, time_window=60)
        
        # Make requests up to limit
        for i in range(3):
            limiter.record_request()
        
        # Next request should be denied
        assert limiter.is_allowed() is False
    
    def test_rate_limiting_time_window_reset(self):
        """Rate limiting time window reset testi."""
        limiter = RateLimiter(max_requests=2, time_window=1)  # 1 second window
        
        # Make requests up to limit
        limiter.record_request()
        limiter.record_request()
        
        # Should be at limit
        assert limiter.is_allowed() is False
        
        # Wait for time window to pass
        time.sleep(1.1)
        
        # Should be allowed again
        assert limiter.is_allowed() is True
    
    def test_rate_limiter_cleanup(self):
        """Rate limiter cleanup testi."""
        limiter = RateLimiter(max_requests=5, time_window=1)
        
        # Add old requests
        old_time = time.time() - 2  # 2 seconds ago
        limiter.requests = [old_time, old_time, old_time]
        
        # Cleanup should remove old requests
        limiter.cleanup_old_requests()
        
        assert len(limiter.requests) == 0
    
    def test_rate_limiter_wait_time(self):
        """Rate limiter wait time testi."""
        limiter = RateLimiter(max_requests=2, time_window=60)
        
        # Make requests up to limit
        limiter.record_request()
        limiter.record_request()
        
        # Get wait time
        wait_time = limiter.get_wait_time()
        
        # Should be close to time window (within a few seconds)
        assert 55 <= wait_time <= 60


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.performance
class TestHTTPUtilsPerformance:
    """HTTP Utils performance testleri."""
    
    @responses.activate
    def test_bulk_requests_performance(self, performance_timer):
        """Bulk requests performance testi."""
        # Mock responses for 100 requests
        for i in range(100):
            responses.add(
                responses.GET,
                f"https://test.espocrm.com/api/v1/Account/{i}",
                json={"id": str(i), "name": f"Company {i}"},
                status=200
            )
        
        client = HTTPClient("https://test.espocrm.com")
        
        performance_timer.start()
        results = []
        for i in range(100):
            result = client.get(f"api/v1/Account/{i}")
            results.append(result)
        performance_timer.stop()
        
        # Performance assertions
        assert len(results) == 100
        assert performance_timer.elapsed < 5.0  # 5 saniyeden az
    
    def test_request_builder_performance(self, performance_timer):
        """Request builder performance testi."""
        builder = RequestBuilder("https://test.espocrm.com")
        
        performance_timer.start()
        
        # Build 1000 requests
        requests_built = []
        for i in range(1000):
            request = (builder
                      .method("GET")
                      .path(f"api/v1/Account/{i}")
                      .header("X-Request-ID", str(i))
                      .param("include", "contacts")
                      .build())
            requests_built.append(request)
        
        performance_timer.stop()
        
        # Performance assertions
        assert len(requests_built) == 1000
        assert performance_timer.elapsed < 1.0  # 1 saniyeden az
    
    def test_response_handling_performance(self, performance_timer):
        """Response handling performance testi."""
        handler = ResponseHandler()
        
        # Create mock responses
        mock_responses = []
        for i in range(1000):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.json.return_value = {"id": str(i), "name": f"Entity {i}"}
            mock_responses.append(mock_response)
        
        performance_timer.start()
        
        # Handle all responses
        results = []
        for response in mock_responses:
            result = handler.handle(response)
            results.append(result)
        
        performance_timer.stop()
        
        # Performance assertions
        assert len(results) == 1000
        assert performance_timer.elapsed < 0.5  # 500ms'den az


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.security
class TestHTTPUtilsSecurity:
    """HTTP Utils security testleri."""
    
    def test_url_validation(self):
        """URL validation testi."""
        builder = RequestBuilder("https://test.espocrm.com")
        
        # Valid URLs
        valid_paths = [
            "api/v1/Account",
            "api/v1/Account/123",
            "api/v1/Account/123/contacts"
        ]
        
        for path in valid_paths:
            request = builder.path(path).build()
            assert request.url.startswith("https://test.espocrm.com")
        
        # Invalid URLs (should be sanitized or rejected)
        invalid_paths = [
            "../../../etc/passwd",
            "javascript:alert('xss')",
            "http://malicious.com/api",
            "//malicious.com/api"
        ]
        
        for path in invalid_paths:
            with pytest.raises((ValidationError, ValueError)):
                builder.path(path).build()
    
    def test_header_sanitization(self):
        """Header sanitization testi."""
        builder = RequestBuilder("https://test.espocrm.com")
        
        # Malicious headers should be rejected
        malicious_headers = [
            ("X-Forwarded-For", "127.0.0.1"),  # Header injection
            ("Host", "malicious.com"),  # Host header injection
            ("Content-Length", "999999"),  # Content length manipulation
        ]
        
        for header_name, header_value in malicious_headers:
            with pytest.raises((ValidationError, ValueError)):
                builder.header(header_name, header_value).build()
    
    def test_data_sanitization(self):
        """Data sanitization testi."""
        client = HTTPClient("https://test.espocrm.com")
        
        # Large payload should be rejected
        large_data = {"field": "A" * (10 * 1024 * 1024)}  # 10MB
        
        with pytest.raises(ValidationError):
            client.post("api/v1/Account", data=large_data)
    
    def test_response_size_limits(self):
        """Response size limits testi."""
        handler = ResponseHandler(max_response_size=1024)  # 1KB limit
        
        # Mock large response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json", "Content-Length": "2048"}
        mock_response.text = "A" * 2048  # 2KB response
        
        with pytest.raises(ValidationError):
            handler.handle(mock_response)


@pytest.mark.integration
@pytest.mark.utils
class TestHTTPUtilsIntegration:
    """HTTP Utils integration testleri."""
    
    @responses.activate
    def test_full_http_workflow(self):
        """Full HTTP workflow integration testi."""
        # Mock responses
        responses.add(
            responses.POST,
            "https://test.espocrm.com/api/v1/Account",
            json={"id": "new_123", "name": "New Company"},
            status=201
        )
        
        responses.add(
            responses.GET,
            "https://test.espocrm.com/api/v1/Account/new_123",
            json={"id": "new_123", "name": "New Company", "type": "Customer"},
            status=200
        )
        
        responses.add(
            responses.PUT,
            "https://test.espocrm.com/api/v1/Account/new_123",
            json={"id": "new_123", "name": "Updated Company", "type": "Customer"},
            status=200
        )
        
        responses.add(
            responses.DELETE,
            "https://test.espocrm.com/api/v1/Account/new_123",
            json={"deleted": True},
            status=200
        )
        
        client = HTTPClient("https://test.espocrm.com")
        
        # 1. Create
        create_result = client.post("api/v1/Account", data={"name": "New Company"})
        assert create_result["id"] == "new_123"
        
        # 2. Read
        read_result = client.get("api/v1/Account/new_123")
        assert read_result["name"] == "New Company"
        
        # 3. Update
        update_result = client.put("api/v1/Account/new_123", data={"name": "Updated Company"})
        assert update_result["name"] == "Updated Company"
        
        # 4. Delete
        delete_result = client.delete("api/v1/Account/new_123")
        assert delete_result["deleted"] is True
    
    def test_error_recovery_workflow(self):
        """Error recovery workflow testi."""
        client = HTTPClient("https://test.espocrm.com", max_retries=2)
        
        call_count = 0
        
        def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.ConnectionError("Connection failed")
            
            # Success response
            response = Mock()
            response.status_code = 200
            response.headers = {"Content-Type": "application/json"}
            response.json.return_value = {"success": True}
            return response
        
        with patch('requests.Session.request', side_effect=mock_request):
            with patch('time.sleep'):  # Speed up test
                result = client.get("api/v1/Account")
        
        # Should succeed after retries
        assert result["success"] is True
        assert call_count == 3  # Initial + 2 retries


if __name__ == "__main__":
    pytest.main([__file__, "-v"])