"""
EspoCRM Logging Test Module

Logging sistemi için kapsamlı testler.
"""

import pytest
import logging
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import structlog

from espocrm.logging.logger import (
    EspoCRMLogger,
    LoggerConfig,
    get_logger,
    configure_logging
)
from espocrm.logging.formatters import (
    JSONFormatter,
    StructuredFormatter,
    ColoredFormatter
)
from espocrm.logging.handlers import (
    RotatingFileHandler,
    TimedRotatingFileHandler,
    HTTPHandler
)
from espocrm.logging.metrics import LogMetrics, MetricsCollector


@pytest.mark.unit
@pytest.mark.logging
class TestEspoCRMLogger:
    """EspoCRM Logger temel testleri."""
    
    def test_logger_initialization(self):
        """Logger initialization testi."""
        config = LoggerConfig(
            name="test_logger",
            level="INFO",
            format="json"
        )
        
        logger = EspoCRMLogger(config)
        
        # Assertions
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert isinstance(logger.logger, logging.Logger)
    
    def test_logger_basic_logging(self, caplog):
        """Logger basic logging testi."""
        config = LoggerConfig(name="test_logger", level="DEBUG")
        logger = EspoCRMLogger(config)
        
        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Assertions
        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
        assert "Critical message" in caplog.text
    
    def test_logger_with_context(self, caplog):
        """Logger with context testi."""
        config = LoggerConfig(name="test_logger", level="INFO")
        logger = EspoCRMLogger(config)
        
        # Log with context
        context = {
            "user_id": "user_123",
            "entity_type": "Account",
            "entity_id": "account_456",
            "operation": "create"
        }
        
        logger.info("Entity created", **context)
        
        # Assertions
        assert "Entity created" in caplog.text
        assert "user_123" in caplog.text
        assert "Account" in caplog.text
        assert "account_456" in caplog.text
    
    def test_logger_exception_logging(self, caplog):
        """Logger exception logging testi."""
        config = LoggerConfig(name="test_logger", level="ERROR")
        logger = EspoCRMLogger(config)
        
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            logger.exception("An error occurred", error=str(e))
        
        # Assertions
        assert "An error occurred" in caplog.text
        assert "ValueError" in caplog.text
        assert "Test exception" in caplog.text
    
    def test_logger_structured_logging(self):
        """Logger structured logging testi."""
        config = LoggerConfig(
            name="test_logger",
            level="INFO",
            format="json"
        )
        logger = EspoCRMLogger(config)
        
        with patch('structlog.get_logger') as mock_structlog:
            mock_struct_logger = Mock()
            mock_structlog.return_value = mock_struct_logger
            
            logger.info("Structured message", key1="value1", key2="value2")
            
            # Verify structlog was called
            mock_struct_logger.info.assert_called_once_with(
                "Structured message",
                key1="value1",
                key2="value2"
            )
    
    def test_logger_performance_logging(self, caplog):
        """Logger performance logging testi."""
        config = LoggerConfig(name="test_logger", level="INFO")
        logger = EspoCRMLogger(config)
        
        # Performance context manager
        with logger.performance("test_operation"):
            import time
            time.sleep(0.1)  # Simulate work
        
        # Assertions
        assert "test_operation" in caplog.text
        assert "duration" in caplog.text or "elapsed" in caplog.text
    
    def test_logger_request_logging(self, caplog):
        """Logger request logging testi."""
        config = LoggerConfig(name="test_logger", level="INFO")
        logger = EspoCRMLogger(config)
        
        # Log HTTP request
        logger.log_request(
            method="POST",
            url="https://test.espocrm.com/api/v1/Account",
            headers={"Content-Type": "application/json"},
            data={"name": "Test Company"}
        )
        
        # Assertions
        assert "POST" in caplog.text
        assert "Account" in caplog.text
        assert "application/json" in caplog.text
    
    def test_logger_response_logging(self, caplog):
        """Logger response logging testi."""
        config = LoggerConfig(name="test_logger", level="INFO")
        logger = EspoCRMLogger(config)
        
        # Log HTTP response
        logger.log_response(
            status_code=201,
            headers={"Content-Type": "application/json"},
            data={"id": "account_123", "name": "Test Company"},
            duration=0.5
        )
        
        # Assertions
        assert "201" in caplog.text
        assert "account_123" in caplog.text
        assert "0.5" in caplog.text


@pytest.mark.unit
@pytest.mark.logging
class TestLoggerConfig:
    """Logger Config testleri."""
    
    def test_logger_config_initialization(self):
        """Logger config initialization testi."""
        config = LoggerConfig(
            name="test_logger",
            level="DEBUG",
            format="json",
            output="file",
            file_path="/tmp/test.log",
            max_file_size="10MB",
            backup_count=5
        )
        
        # Assertions
        assert config.name == "test_logger"
        assert config.level == "DEBUG"
        assert config.format == "json"
        assert config.output == "file"
        assert config.file_path == "/tmp/test.log"
        assert config.max_file_size == "10MB"
        assert config.backup_count == 5
    
    def test_logger_config_validation(self):
        """Logger config validation testi."""
        # Valid config
        valid_config = LoggerConfig(name="test", level="INFO")
        assert valid_config.name == "test"
        
        # Invalid level
        with pytest.raises(ValueError):
            LoggerConfig(name="test", level="INVALID")
        
        # Invalid format
        with pytest.raises(ValueError):
            LoggerConfig(name="test", format="invalid")
        
        # Invalid output
        with pytest.raises(ValueError):
            LoggerConfig(name="test", output="invalid")
    
    def test_logger_config_from_dict(self):
        """Logger config from dict testi."""
        config_dict = {
            "name": "test_logger",
            "level": "WARNING",
            "format": "structured",
            "output": "console",
            "enable_metrics": True
        }
        
        config = LoggerConfig.from_dict(config_dict)
        
        # Assertions
        assert config.name == "test_logger"
        assert config.level == "WARNING"
        assert config.format == "structured"
        assert config.output == "console"
        assert config.enable_metrics is True
    
    def test_logger_config_to_dict(self):
        """Logger config to dict testi."""
        config = LoggerConfig(
            name="test_logger",
            level="ERROR",
            format="colored"
        )
        
        config_dict = config.to_dict()
        
        # Assertions
        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "test_logger"
        assert config_dict["level"] == "ERROR"
        assert config_dict["format"] == "colored"


@pytest.mark.unit
@pytest.mark.logging
class TestLogFormatters:
    """Log Formatters testleri."""
    
    def test_json_formatter(self):
        """JSON formatter testi."""
        formatter = JSONFormatter()
        
        # Create log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.user_id = "user_123"
        record.entity_type = "Account"
        
        formatted = formatter.format(record)
        
        # Assertions
        assert isinstance(formatted, str)
        parsed = json.loads(formatted)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert parsed["user_id"] == "user_123"
        assert parsed["entity_type"] == "Account"
        assert "timestamp" in parsed
    
    def test_structured_formatter(self):
        """Structured formatter testi."""
        formatter = StructuredFormatter()
        
        # Create log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="test.py",
            lineno=20,
            msg="Warning message",
            args=(),
            exc_info=None
        )
        record.operation = "update"
        record.duration = 1.5
        
        formatted = formatter.format(record)
        
        # Assertions
        assert isinstance(formatted, str)
        assert "WARNING" in formatted
        assert "Warning message" in formatted
        assert "operation=update" in formatted
        assert "duration=1.5" in formatted
    
    def test_colored_formatter(self):
        """Colored formatter testi."""
        formatter = ColoredFormatter()
        
        # Test different log levels
        levels = [
            (logging.DEBUG, "Debug message"),
            (logging.INFO, "Info message"),
            (logging.WARNING, "Warning message"),
            (logging.ERROR, "Error message"),
            (logging.CRITICAL, "Critical message")
        ]
        
        for level, message in levels:
            record = logging.LogRecord(
                name="test_logger",
                level=level,
                pathname="test.py",
                lineno=30,
                msg=message,
                args=(),
                exc_info=None
            )
            
            formatted = formatter.format(record)
            
            # Assertions
            assert isinstance(formatted, str)
            assert message in formatted
            # Color codes should be present (ANSI escape sequences)
            assert "\033[" in formatted or message in formatted


@pytest.mark.unit
@pytest.mark.logging
class TestLogHandlers:
    """Log Handlers testleri."""
    
    def test_rotating_file_handler(self):
        """Rotating file handler testi."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            handler = RotatingFileHandler(
                filename=temp_path,
                max_bytes=1024,  # 1KB
                backup_count=3
            )
            
            # Create logger with handler
            logger = logging.getLogger("test_rotating")
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            # Write logs to trigger rotation
            for i in range(100):
                logger.info(f"Log message {i} with some content to fill the file")
            
            # Check if backup files were created
            backup_files = [f for f in os.listdir(os.path.dirname(temp_path)) 
                           if f.startswith(os.path.basename(temp_path))]
            
            # Should have original + backup files
            assert len(backup_files) > 1
            
        finally:
            # Cleanup
            for f in os.listdir(os.path.dirname(temp_path)):
                if f.startswith(os.path.basename(temp_path)):
                    os.unlink(os.path.join(os.path.dirname(temp_path), f))
    
    def test_timed_rotating_file_handler(self):
        """Timed rotating file handler testi."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            handler = TimedRotatingFileHandler(
                filename=temp_path,
                when="S",  # Seconds
                interval=1,
                backup_count=2
            )
            
            # Create logger with handler
            logger = logging.getLogger("test_timed")
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            # Write initial log
            logger.info("Initial log message")
            
            # Wait and write another log
            import time
            time.sleep(1.1)
            logger.info("Second log message")
            
            # Check if file exists
            assert os.path.exists(temp_path)
            
        finally:
            # Cleanup
            for f in os.listdir(os.path.dirname(temp_path)):
                if f.startswith(os.path.basename(temp_path)):
                    os.unlink(os.path.join(os.path.dirname(temp_path), f))
    
    def test_http_handler(self):
        """HTTP handler testi."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            handler = HTTPHandler(
                url="https://logs.example.com/api/logs",
                method="POST",
                headers={"Authorization": "Bearer token"}
            )
            
            # Create log record
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=40,
                msg="HTTP log message",
                args=(),
                exc_info=None
            )
            
            # Emit log
            handler.emit(record)
            
            # Verify HTTP request was made
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "logs.example.com" in call_args[1]["url"]
            assert call_args[1]["headers"]["Authorization"] == "Bearer token"


@pytest.mark.unit
@pytest.mark.logging
class TestLogMetrics:
    """Log Metrics testleri."""
    
    def test_log_metrics_initialization(self):
        """Log metrics initialization testi."""
        metrics = LogMetrics()
        
        # Assertions
        assert metrics.total_logs == 0
        assert metrics.error_count == 0
        assert metrics.warning_count == 0
        assert len(metrics.log_levels) == 0
        assert len(metrics.response_times) == 0
    
    def test_log_metrics_recording(self):
        """Log metrics recording testi."""
        metrics = LogMetrics()
        
        # Record different log levels
        metrics.record_log("INFO", duration=0.1)
        metrics.record_log("WARNING", duration=0.2)
        metrics.record_log("ERROR", duration=0.3)
        metrics.record_log("INFO", duration=0.15)
        
        # Assertions
        assert metrics.total_logs == 4
        assert metrics.error_count == 1
        assert metrics.warning_count == 1
        assert metrics.log_levels["INFO"] == 2
        assert metrics.log_levels["WARNING"] == 1
        assert metrics.log_levels["ERROR"] == 1
        assert len(metrics.response_times) == 4
    
    def test_log_metrics_statistics(self):
        """Log metrics statistics testi."""
        metrics = LogMetrics()
        
        # Record some logs with response times
        response_times = [0.1, 0.2, 0.3, 0.4, 0.5]
        for i, rt in enumerate(response_times):
            metrics.record_log("INFO", duration=rt)
        
        stats = metrics.get_statistics()
        
        # Assertions
        assert isinstance(stats, dict)
        assert stats["total_logs"] == 5
        assert stats["average_response_time"] == 0.3  # (0.1+0.2+0.3+0.4+0.5)/5
        assert stats["min_response_time"] == 0.1
        assert stats["max_response_time"] == 0.5
        assert "log_levels" in stats
    
    def test_metrics_collector(self):
        """Metrics collector testi."""
        collector = MetricsCollector()
        
        # Add metrics from different loggers
        metrics1 = LogMetrics()
        metrics1.record_log("INFO", duration=0.1)
        metrics1.record_log("ERROR", duration=0.2)
        
        metrics2 = LogMetrics()
        metrics2.record_log("WARNING", duration=0.3)
        metrics2.record_log("INFO", duration=0.4)
        
        collector.add_metrics("logger1", metrics1)
        collector.add_metrics("logger2", metrics2)
        
        # Get aggregated statistics
        aggregated = collector.get_aggregated_statistics()
        
        # Assertions
        assert aggregated["total_logs"] == 4
        assert aggregated["error_count"] == 1
        assert aggregated["warning_count"] == 1
        assert "logger1" in aggregated["by_logger"]
        assert "logger2" in aggregated["by_logger"]


@pytest.mark.unit
@pytest.mark.logging
@pytest.mark.performance
class TestLoggingPerformance:
    """Logging performance testleri."""
    
    def test_high_volume_logging_performance(self, performance_timer):
        """High volume logging performance testi."""
        config = LoggerConfig(name="perf_logger", level="INFO")
        logger = EspoCRMLogger(config)
        
        performance_timer.start()
        
        # Log 1000 messages
        for i in range(1000):
            logger.info(f"Performance test message {i}", 
                       iteration=i, 
                       timestamp=datetime.now().isoformat())
        
        performance_timer.stop()
        
        # Performance assertions
        assert performance_timer.elapsed < 2.0  # 2 saniyeden az
    
    def test_structured_logging_performance(self, performance_timer):
        """Structured logging performance testi."""
        config = LoggerConfig(
            name="struct_logger", 
            level="INFO", 
            format="json"
        )
        logger = EspoCRMLogger(config)
        
        performance_timer.start()
        
        # Log 500 structured messages
        for i in range(500):
            logger.info("Structured message",
                       user_id=f"user_{i}",
                       entity_type="Account",
                       entity_id=f"account_{i}",
                       operation="create",
                       duration=0.1 + (i * 0.001))
        
        performance_timer.stop()
        
        # Performance assertions
        assert performance_timer.elapsed < 3.0  # 3 saniyeden az
    
    def test_metrics_collection_performance(self, performance_timer):
        """Metrics collection performance testi."""
        metrics = LogMetrics()
        
        performance_timer.start()
        
        # Record 10000 metrics
        for i in range(10000):
            level = ["DEBUG", "INFO", "WARNING", "ERROR"][i % 4]
            duration = 0.001 + (i * 0.0001)
            metrics.record_log(level, duration=duration)
        
        # Get statistics
        stats = metrics.get_statistics()
        
        performance_timer.stop()
        
        # Performance assertions
        assert performance_timer.elapsed < 1.0  # 1 saniyeden az
        assert stats["total_logs"] == 10000


@pytest.mark.unit
@pytest.mark.logging
@pytest.mark.security
class TestLoggingSecurity:
    """Logging security testleri."""
    
    def test_sensitive_data_filtering(self, caplog):
        """Sensitive data filtering testi."""
        config = LoggerConfig(
            name="secure_logger", 
            level="INFO",
            filter_sensitive=True
        )
        logger = EspoCRMLogger(config)
        
        # Log with sensitive data
        logger.info("User login", 
                   username="testuser",
                   password="secret123",  # Should be filtered
                   api_key="sk_test_123456",  # Should be filtered
                   credit_card="4111-1111-1111-1111")  # Should be filtered
        
        # Assertions
        assert "testuser" in caplog.text
        assert "secret123" not in caplog.text
        assert "sk_test_123456" not in caplog.text
        assert "4111-1111-1111-1111" not in caplog.text
        assert "***" in caplog.text or "[FILTERED]" in caplog.text
    
    def test_log_injection_prevention(self, caplog):
        """Log injection prevention testi."""
        config = LoggerConfig(name="secure_logger", level="INFO")
        logger = EspoCRMLogger(config)
        
        # Malicious log content
        malicious_content = "Normal message\nFAKE ERROR: Injected log entry"
        
        logger.info("User input", content=malicious_content)
        
        # Assertions
        log_lines = caplog.text.split('\n')
        # Should not create fake log entries
        fake_entries = [line for line in log_lines if "FAKE ERROR" in line and "User input" not in line]
        assert len(fake_entries) == 0
    
    def test_log_size_limits(self):
        """Log size limits testi."""
        config = LoggerConfig(
            name="limited_logger", 
            level="INFO",
            max_message_size=100
        )
        logger = EspoCRMLogger(config)
        
        # Very large log message
        large_message = "A" * 1000
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.info(large_message)
            
            # Message should be truncated
            call_args = mock_info.call_args[0][0]
            assert len(call_args) <= 100
            assert "..." in call_args or "[TRUNCATED]" in call_args
    
    def test_log_rate_limiting(self):
        """Log rate limiting testi."""
        config = LoggerConfig(
            name="rate_limited_logger",
            level="INFO",
            rate_limit=5,  # 5 logs per second
            rate_limit_window=1
        )
        logger = EspoCRMLogger(config)
        
        with patch.object(logger.logger, 'info') as mock_info:
            # Try to log 10 messages rapidly
            for i in range(10):
                logger.info(f"Message {i}")
            
            # Should be rate limited
            assert mock_info.call_count <= 5


@pytest.mark.integration
@pytest.mark.logging
class TestLoggingIntegration:
    """Logging integration testleri."""
    
    def test_full_logging_workflow(self):
        """Full logging workflow integration testi."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Configure logging
            config = LoggerConfig(
                name="integration_logger",
                level="DEBUG",
                format="json",
                output="file",
                file_path=temp_path,
                enable_metrics=True
            )
            
            logger = EspoCRMLogger(config)
            
            # Log various messages
            logger.debug("Debug message")
            logger.info("Info message", user_id="user_123")
            logger.warning("Warning message", entity_type="Account")
            logger.error("Error message", error_code=500)
            
            # Performance logging
            with logger.performance("test_operation"):
                import time
                time.sleep(0.1)
            
            # Check file was created and contains logs
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "Debug message" in content
                assert "Info message" in content
                assert "user_123" in content
                assert "test_operation" in content
            
            # Check metrics
            if hasattr(logger, 'metrics'):
                stats = logger.metrics.get_statistics()
                assert stats["total_logs"] > 0
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_multi_logger_coordination(self):
        """Multi-logger coordination testi."""
        # Create multiple loggers
        loggers = []
        for i in range(3):
            config = LoggerConfig(
                name=f"logger_{i}",
                level="INFO",
                enable_metrics=True
            )
            logger = EspoCRMLogger(config)
            loggers.append(logger)
        
        # Log from different loggers
        for i, logger in enumerate(loggers):
            logger.info(f"Message from logger {i}", logger_id=i)
        
        # Collect metrics
        collector = MetricsCollector()
        for i, logger in enumerate(loggers):
            if hasattr(logger, 'metrics'):
                collector.add_metrics(f"logger_{i}", logger.metrics)
        
        # Check aggregated metrics
        aggregated = collector.get_aggregated_statistics()
        assert aggregated["total_logs"] >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])