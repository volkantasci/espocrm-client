"""
EspoCRM Structured Logger

Professional-grade structured logging sistemi:
- JSON formatında log çıktısı
- Context management (request_id, user_id, vb.)
- Sensitive data masking
- Thread-safe logging
- Performance optimized
"""

import logging
import threading
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional, Union, List, Set
from datetime import datetime, timezone

import structlog
from structlog.types import FilteringBoundLogger


# Context variables for request tracking
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


class SensitiveDataMasker:
    """Sensitive data masking utility"""
    
    # Sensitive field patterns
    SENSITIVE_FIELDS: Set[str] = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'api_key',
        'apikey', 'auth', 'authorization', 'credential', 'credentials',
        'private_key', 'privatekey', 'access_token', 'refresh_token',
        'session_id', 'sessionid', 'cookie', 'cookies'
    }
    
    # PII field patterns
    PII_FIELDS: Set[str] = {
        'email', 'phone', 'mobile', 'ssn', 'social_security_number',
        'credit_card', 'creditcard', 'card_number', 'cardnumber',
        'account_number', 'accountnumber', 'iban', 'swift'
    }
    
    @classmethod
    def mask_sensitive_data(cls, data: Any) -> Any:
        """
        Mask sensitive data in logs
        
        Args:
            data: Data to mask
            
        Returns:
            Masked data
        """
        if isinstance(data, dict):
            return cls._mask_dict(data)
        elif isinstance(data, list):
            return [cls.mask_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            return cls._mask_string_if_sensitive(data)
        else:
            return data
    
    @classmethod
    def _mask_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in dictionary"""
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            if any(sensitive in key_lower for sensitive in cls.SENSITIVE_FIELDS):
                masked[key] = "***MASKED***"
            elif any(pii in key_lower for pii in cls.PII_FIELDS):
                masked[key] = cls._mask_pii_value(value)
            else:
                masked[key] = cls.mask_sensitive_data(value)
                
        return masked
    
    @classmethod
    def _mask_pii_value(cls, value: Any) -> str:
        """Mask PII values partially"""
        if not isinstance(value, str):
            return "***PII***"
            
        if len(value) <= 4:
            return "***"
        elif '@' in value:  # Email
            parts = value.split('@')
            if len(parts) == 2:
                return f"{parts[0][:2]}***@{parts[1]}"
        else:  # Other PII
            return f"{value[:2]}***{value[-2:]}"
            
        return "***PII***"
    
    @classmethod
    def _mask_string_if_sensitive(cls, value: str) -> str:
        """Check if string contains sensitive patterns"""
        # Simple heuristic for potential tokens/keys
        if len(value) > 20 and any(char.isalnum() for char in value):
            # Looks like a token
            return f"{value[:4]}***{value[-4:]}"
        return value


class ContextManager:
    """Thread-safe context management for logging"""
    
    def __init__(self):
        self._local = threading.local()
    
    def set_context(self, **kwargs: Any) -> None:
        """Set context variables"""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        self._local.context.update(kwargs)
        
        # Also set in contextvars for async compatibility
        current = request_context.get({})
        current.update(kwargs)
        request_context.set(current)
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context"""
        # Try contextvars first (async-friendly)
        ctx = request_context.get({})
        if ctx:
            return ctx.copy()
            
        # Fallback to thread-local
        if hasattr(self._local, 'context'):
            return self._local.context.copy()
        return {}
    
    def clear_context(self) -> None:
        """Clear current context"""
        if hasattr(self._local, 'context'):
            self._local.context.clear()
        request_context.set({})
    
    def generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{uuid.uuid4().hex[:12]}"


# Global context manager instance
context_manager = ContextManager()


def add_timestamp(logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add ISO timestamp to log events"""
    event_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_context(logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add context information to log events"""
    context = context_manager.get_context()
    if context:
        event_dict['context'] = context
    return event_dict


def mask_sensitive_processor(logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Process and mask sensitive data in log events"""
    # Mask sensitive data in the event dict
    for key, value in list(event_dict.items()):
        if key in ['data', 'request_data', 'response_data', 'payload']:
            event_dict[key] = SensitiveDataMasker.mask_sensitive_data(value)
    
    return event_dict


def add_logger_name(logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add logger name to log events"""
    if hasattr(logger, '_logger') and hasattr(logger._logger, 'name'):
        event_dict['logger'] = logger._logger.name
    return event_dict


class StructuredLogger:
    """
    Professional structured logger for EspoCRM client
    
    Features:
    - JSON structured logging
    - Context management
    - Sensitive data masking
    - Thread-safe operations
    - Performance optimized
    """
    
    def __init__(
        self,
        name: str,
        level: Union[str, int] = logging.INFO,
        enable_masking: bool = True,
        extra_processors: Optional[List] = None
    ):
        """
        Initialize structured logger
        
        Args:
            name: Logger name
            level: Log level
            enable_masking: Enable sensitive data masking
            extra_processors: Additional structlog processors
        """
        self.name = name
        self.enable_masking = enable_masking
        
        # Configure structlog processors
        processors = [
            add_timestamp,
            add_context,
            add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
        ]
        
        if enable_masking:
            processors.append(mask_sensitive_processor)
            
        if extra_processors:
            processors.extend(extra_processors)
            
        processors.extend([
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ])
        
        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Create logger
        self._logger = structlog.get_logger(name)
        
        # Set log level
        stdlib_logger = logging.getLogger(name)
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        stdlib_logger.setLevel(level)
    
    def set_context(self, **kwargs: Any) -> None:
        """Set logging context"""
        context_manager.set_context(**kwargs)
    
    def clear_context(self) -> None:
        """Clear logging context"""
        context_manager.clear_context()
    
    def generate_request_id(self) -> str:
        """Generate and set request ID"""
        request_id = context_manager.generate_request_id()
        self.set_context(request_id=request_id)
        return request_id
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message"""
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message"""
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message"""
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message"""
        self._logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message"""
        self._logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback"""
        self._logger.exception(message, **kwargs)
    
    def log_api_call(
        self,
        method: str,
        endpoint: str,
        status_code: Optional[int] = None,
        execution_time_ms: Optional[float] = None,
        **kwargs: Any
    ) -> None:
        """
        Log API call with structured data
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: Response status code
            execution_time_ms: Execution time in milliseconds
            **kwargs: Additional context
        """
        log_data = {
            'method': method,
            'endpoint': endpoint,
        }
        
        if status_code is not None:
            log_data['status_code'] = status_code
            
        if execution_time_ms is not None:
            log_data['execution_time_ms'] = round(execution_time_ms, 2)
            
        log_data.update(kwargs)
        
        # Determine log level based on status code
        if status_code is None:
            level = 'info'
        elif status_code < 400:
            level = 'info'
        elif status_code < 500:
            level = 'warning'
        else:
            level = 'error'
            
        getattr(self, level)(f"API call: {method} {endpoint}", **log_data)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        **kwargs: Any
    ) -> None:
        """
        Log performance metrics
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            **kwargs: Additional context
        """
        self.info(
            f"Performance: {operation}",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            **kwargs
        )
    
    def bind(self, **kwargs: Any) -> 'StructuredLogger':
        """
        Create a new logger with bound context
        
        Args:
            **kwargs: Context to bind
            
        Returns:
            New logger instance with bound context
        """
        bound_logger = StructuredLogger(
            name=self.name,
            enable_masking=self.enable_masking
        )
        bound_logger._logger = self._logger.bind(**kwargs)
        return bound_logger


def get_logger(
    name: str,
    level: Union[str, int] = logging.INFO,
    enable_masking: bool = True
) -> StructuredLogger:
    """
    Get or create a structured logger
    
    Args:
        name: Logger name
        level: Log level
        enable_masking: Enable sensitive data masking
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(
        name=name,
        level=level,
        enable_masking=enable_masking
    )


def setup_logging(
    level: Union[str, int] = logging.INFO,
    enable_console: bool = True,
    enable_file: bool = False,
    log_file: Optional[str] = None,
    enable_masking: bool = True
) -> None:
    """
    Setup global logging configuration
    
    Args:
        level: Global log level
        enable_console: Enable console logging
        enable_file: Enable file logging
        log_file: Log file path
        enable_masking: Enable sensitive data masking
    """
    # Configure root logger
    root_logger = logging.getLogger()
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Import handlers here to avoid circular imports
    from .handlers import ConsoleHandler, FileHandler
    from .formatters import JSONFormatter, ConsoleFormatter
    
    if enable_console:
        console_handler = ConsoleHandler()
        console_handler.setFormatter(ConsoleFormatter())
        root_logger.addHandler(console_handler)
    
    if enable_file and log_file:
        file_handler = FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)