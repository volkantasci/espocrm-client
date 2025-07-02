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
import time
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
        log_data: Dict[str, Any] = {
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


class LoggerConfig:
    """
    Logger configuration sınıfı.
    
    Logger ayarlarını yönetir ve doğrular.
    """
    
    VALID_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    VALID_FORMATS = ['json', 'structured', 'colored', 'simple']
    VALID_OUTPUTS = ['console', 'file', 'both']
    
    def __init__(
        self,
        name: str,
        level: str = 'INFO',
        format: str = 'structured',
        output: str = 'console',
        file_path: Optional[str] = None,
        max_file_size: str = '10MB',
        backup_count: int = 5,
        enable_metrics: bool = False,
        filter_sensitive: bool = True,
        max_message_size: Optional[int] = None,
        rate_limit: Optional[int] = None,
        rate_limit_window: int = 1
    ):
        """
        Logger config'ini başlatır.
        
        Args:
            name: Logger adı
            level: Log seviyesi
            format: Log formatı
            output: Çıktı türü
            file_path: Log dosya yolu
            max_file_size: Maksimum dosya boyutu
            backup_count: Backup dosya sayısı
            enable_metrics: Metrics toplama
            filter_sensitive: Sensitive data filtreleme
            max_message_size: Maksimum mesaj boyutu
            rate_limit: Rate limit (saniye başına)
            rate_limit_window: Rate limit penceresi
        """
        # Validation
        if level.upper() not in self.VALID_LEVELS:
            raise ValueError(f"Invalid level: {level}. Valid levels: {self.VALID_LEVELS}")
        
        if format not in self.VALID_FORMATS:
            raise ValueError(f"Invalid format: {format}. Valid formats: {self.VALID_FORMATS}")
        
        if output not in self.VALID_OUTPUTS:
            raise ValueError(f"Invalid output: {output}. Valid outputs: {self.VALID_OUTPUTS}")
        
        self.name = name
        self.level = level.upper()
        self.format = format
        self.output = output
        self.file_path = file_path
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_metrics = enable_metrics
        self.filter_sensitive = filter_sensitive
        self.max_message_size = max_message_size
        self.rate_limit = rate_limit
        self.rate_limit_window = rate_limit_window
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LoggerConfig':
        """Dict'ten LoggerConfig oluşturur."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """LoggerConfig'i dict'e çevirir."""
        return {
            'name': self.name,
            'level': self.level,
            'format': self.format,
            'output': self.output,
            'file_path': self.file_path,
            'max_file_size': self.max_file_size,
            'backup_count': self.backup_count,
            'enable_metrics': self.enable_metrics,
            'filter_sensitive': self.filter_sensitive,
            'max_message_size': self.max_message_size,
            'rate_limit': self.rate_limit,
            'rate_limit_window': self.rate_limit_window
        }


class EspoCRMLogger:
    """
    EspoCRM için özelleştirilmiş logger sınıfı.
    
    Features:
    - Structured logging
    - Performance monitoring
    - Request/response logging
    - Context management
    - Metrics collection
    """
    
    def __init__(self, config: LoggerConfig):
        """
        EspoCRM logger'ı başlatır.
        
        Args:
            config: Logger konfigürasyonu
        """
        self.config = config
        self.name = config.name
        
        # Convert level string to logging level
        self.level = getattr(logging, config.level)
        
        # Create logger
        self.logger = logging.getLogger(config.name)
        self.logger.setLevel(self.level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers based on config
        self._setup_handlers()
        
        # Setup structured logger if needed
        if config.format == 'json':
            self._setup_structured_logger()
        
        # Setup metrics if enabled
        if config.enable_metrics:
            try:
                from .metrics import LogMetrics
                self.metrics = LogMetrics()
            except ImportError:
                # Fallback metrics implementation
                class SimpleMetrics:
                    def record_log(self, level, duration=None):
                        pass
                self.metrics = SimpleMetrics()
        
        # Rate limiting
        self._rate_limit_times = []
        self._rate_limit_lock = threading.Lock()
    
    def _setup_handlers(self):
        """Handler'ları setup eder."""
        if self.config.output in ['console', 'both']:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.level)
            
            if self.config.format == 'colored':
                try:
                    from .formatters import ColoredFormatter
                    console_handler.setFormatter(ColoredFormatter())
                except ImportError:
                    console_handler.setFormatter(logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    ))
            else:
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            
            self.logger.addHandler(console_handler)
        
        if self.config.output in ['file', 'both'] and self.config.file_path:
            try:
                from .handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    filename=self.config.file_path,
                    maxBytes=self._parse_file_size(self.config.max_file_size),
                    backupCount=self.config.backup_count
                )
            except ImportError:
                # Use standard library RotatingFileHandler
                from logging.handlers import RotatingFileHandler as StdRotatingFileHandler
                file_handler = StdRotatingFileHandler(
                    filename=self.config.file_path,
                    maxBytes=self._parse_file_size(self.config.max_file_size),
                    backupCount=self.config.backup_count
                )
            
            file_handler.setLevel(self.level)
            
            if self.config.format == 'json':
                try:
                    from .formatters import JSONFormatter
                    file_handler.setFormatter(JSONFormatter())
                except ImportError:
                    file_handler.setFormatter(logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    ))
            else:
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            
            self.logger.addHandler(file_handler)
    
    def _setup_structured_logger(self):
        """Structured logger'ı setup eder."""
        try:
            self._structured_logger = get_logger(
                self.name,
                level=self.level,
                enable_masking=self.config.filter_sensitive
            )
        except:
            # Fallback to regular logger
            self._structured_logger = None
    
    def _parse_file_size(self, size_str: str) -> int:
        """Dosya boyutu string'ini byte'a çevirir."""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def _check_rate_limit(self) -> bool:
        """Rate limit kontrolü yapar."""
        if not self.config.rate_limit:
            return True
        
        with self._rate_limit_lock:
            now = time.time()
            # Eski kayıtları temizle
            self._rate_limit_times = [
                t for t in self._rate_limit_times
                if now - t < self.config.rate_limit_window
            ]
            
            if len(self._rate_limit_times) >= self.config.rate_limit:
                return False
            
            self._rate_limit_times.append(now)
            return True
    
    def _filter_message(self, message: str, **kwargs) -> tuple:
        """Mesajı filtreler ve truncate eder."""
        # Sensitive data filtering
        if self.config.filter_sensitive:
            kwargs = SensitiveDataMasker.mask_sensitive_data(kwargs)
        
        # Message size limiting
        if self.config.max_message_size and len(message) > self.config.max_message_size:
            message = message[:self.config.max_message_size - 3] + "..."
        
        # Log injection prevention
        message = message.replace('\n', '\\n').replace('\r', '\\r')
        
        return message, kwargs
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal log method."""
        # Rate limit check
        if not self._check_rate_limit():
            return
        
        # Filter message
        message, kwargs = self._filter_message(message, **kwargs)
        
        # Record metrics
        if hasattr(self, 'metrics'):
            self.metrics.record_log(level)
        
        # Log with structured logger if available
        if hasattr(self, '_structured_logger') and self._structured_logger:
            getattr(self._structured_logger, level.lower())(message, **kwargs)
        else:
            # Fallback to regular logger
            log_method = getattr(self.logger, level.lower())
            if kwargs:
                extra_info = ' '.join([f"{k}={v}" for k, v in kwargs.items()])
                log_method(f"{message} | {extra_info}")
            else:
                log_method(message)
    
    def debug(self, message: str, **kwargs):
        """Debug log."""
        self._log('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Info log."""
        self._log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning log."""
        self._log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Error log."""
        self._log('ERROR', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Critical log."""
        self._log('CRITICAL', message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Exception log with traceback."""
        self._log('ERROR', message, **kwargs)
        if hasattr(self, '_structured_logger') and self._structured_logger:
            self._structured_logger.exception(message, **kwargs)
        else:
            self.logger.exception(message)
    
    def log_request(self, method: str, url: str, headers: Optional[Dict] = None, data: Optional[Any] = None, **kwargs):
        """HTTP request log."""
        log_data: Dict[str, Any] = {
            'method': method,
            'url': url,
            'type': 'request'
        }
        
        if headers:
            log_data['headers'] = headers
        if data:
            log_data['data'] = data
        
        log_data.update(kwargs)
        self.info(f"HTTP Request: {method} {url}", **log_data)
    
    def log_response(self, status_code: int, headers: Optional[Dict] = None, data: Optional[Any] = None, duration: Optional[float] = None, **kwargs):
        """HTTP response log."""
        log_data: Dict[str, Any] = {
            'status_code': status_code,
            'type': 'response'
        }
        
        if headers:
            log_data['headers'] = headers
        if data:
            log_data['data'] = data
        if duration:
            log_data['duration'] = duration
        
        log_data.update(kwargs)
        
        # Log level based on status code
        if status_code < 400:
            self.info(f"HTTP Response: {status_code}", **log_data)
        elif status_code < 500:
            self.warning(f"HTTP Response: {status_code}", **log_data)
        else:
            self.error(f"HTTP Response: {status_code}", **log_data)
    
    def performance(self, operation: str):
        """Performance context manager."""
        return PerformanceContext(self, operation)


class PerformanceContext:
    """Performance monitoring context manager."""
    
    def __init__(self, logger: EspoCRMLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.debug(f"Performance: {self.operation} started")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        if self.start_time:
            duration = time.time() - self.start_time
            self.logger.info(
                f"Performance: {self.operation} completed",
                operation=self.operation,
                duration=duration,
                duration_ms=duration * 1000
            )


def configure_logging(
    level: Union[str, int] = 'INFO',
    format: str = 'structured',
    output: str = 'console',
    file_path: Optional[str] = None,
    enable_metrics: bool = False
) -> LoggerConfig:
    """
    Global logging konfigürasyonu.
    
    Args:
        level: Log seviyesi
        format: Log formatı
        output: Çıktı türü
        file_path: Log dosya yolu
        enable_metrics: Metrics toplama
        
    Returns:
        LoggerConfig instance
    """
    # Convert level to string if it's an int
    if isinstance(level, int):
        level_name = logging.getLevelName(level)
    else:
        level_name = level
    
    config = LoggerConfig(
        name='espocrm',
        level=level_name,
        format=format,
        output=output,
        file_path=file_path,
        enable_metrics=enable_metrics
    )
    
    # Setup global logging
    setup_logging(
        level=getattr(logging, config.level) if isinstance(config.level, str) else config.level,
        enable_console=(output in ['console', 'both']),
        enable_file=(output in ['file', 'both']),
        log_file=file_path
    )
    
    return config


# Backward compatibility
EspoCRMLogger = EspoCRMLogger
LoggerConfig = LoggerConfig