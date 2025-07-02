"""
EspoCRM Structured Logging modülü

Professional-grade structured logging ve monitoring sistemi:
- JSON formatında structured logging
- Context management ve sensitive data masking
- Performance metrics collection
- External monitoring system integration
- Thread-safe operations
- Async logging desteği

Temel Kullanım:
    ```python
    from espocrm.logging import get_logger, setup_logging
    
    # Setup logging
    setup_logging(level='INFO', enable_console=True)
    
    # Get logger
    logger = get_logger('espocrm.client')
    
    # Log with context
    logger.set_context(user_id='user123', request_id='req456')
    logger.info('User action performed', action='create_lead')
    
    # Log API calls
    logger.log_api_call('POST', '/api/v1/Lead', status_code=201, execution_time_ms=245)
    ```

Metrics Kullanımı:
    ```python
    from espocrm.logging import get_metrics_collector, time_operation
    
    # Get metrics collector
    metrics = get_metrics_collector()
    
    # Record API request
    metrics.record_request('POST', '/api/v1/Lead', status_code=201, response_time_ms=245)
    
    # Time operations
    with time_operation('database_query'):
        # Your operation here
        pass
    
    # Get statistics
    stats = metrics.get_stats()
    ```
"""

import logging
from typing import Optional, Union, Dict, Any, List
from pathlib import Path

# Core components
from .logger import (
    StructuredLogger,
    get_logger,
    setup_logging,
    context_manager,
    SensitiveDataMasker
)

from .formatters import (
    JSONFormatter,
    ConsoleFormatter,
    CompactJSONFormatter,
    DebugFormatter,
    create_json_formatter,
    create_console_formatter
)

from .handlers import (
    FileHandler,
    ConsoleHandler,
    RotatingFileHandler,
    TimedRotatingHandler,
    AsyncHandler,
    MonitoringHandler,
    create_file_handler,
    create_console_handler,
    create_async_handler
)

from .metrics import (
    MetricsCollector,
    RequestMetrics,
    PerformanceMetrics,
    CounterMetrics,
    Timer,
    MetricsAggregator,
    get_metrics_collector,
    set_metrics_collector,
    record_request,
    record_performance,
    increment_counter,
    time_operation,
    get_stats
)

# Version info
__version__ = "1.0.0"

# Public API
__all__ = [
    # Core logger
    "StructuredLogger",
    "get_logger",
    "setup_logging",
    
    # Context management
    "context_manager",
    "SensitiveDataMasker",
    
    # Formatters
    "JSONFormatter",
    "ConsoleFormatter",
    "CompactJSONFormatter",
    "DebugFormatter",
    "create_json_formatter",
    "create_console_formatter",
    
    # Handlers
    "FileHandler",
    "ConsoleHandler",
    "RotatingFileHandler",
    "TimedRotatingHandler",
    "AsyncHandler",
    "MonitoringHandler",
    "create_file_handler",
    "create_console_handler",
    "create_async_handler",
    
    # Metrics
    "MetricsCollector",
    "RequestMetrics",
    "PerformanceMetrics",
    "CounterMetrics",
    "Timer",
    "MetricsAggregator",
    "get_metrics_collector",
    "set_metrics_collector",
    "record_request",
    "record_performance",
    "increment_counter",
    "time_operation",
    "get_stats",
    
    # Factory functions
    "create_logger",
    "create_file_logger",
    "create_console_logger",
    "create_production_logger",
    "create_development_logger",
    "configure_espocrm_logging",
]


def create_logger(
    name: str,
    level: Union[str, int] = logging.INFO,
    enable_masking: bool = True,
    handlers: Optional[List[logging.Handler]] = None,
    formatters: Optional[Dict[str, logging.Formatter]] = None
) -> StructuredLogger:
    """
    Create a structured logger with custom configuration
    
    Args:
        name: Logger name
        level: Log level
        enable_masking: Enable sensitive data masking
        handlers: Custom handlers
        formatters: Custom formatters for handlers
        
    Returns:
        StructuredLogger instance
    """
    logger = get_logger(name, level, enable_masking)
    
    if handlers:
        # Clear default handlers
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.handlers.clear()
        
        # Add custom handlers
        for i, handler in enumerate(handlers):
            if formatters and i < len(formatters):
                formatter_key = list(formatters.keys())[i]
                handler.setFormatter(formatters[formatter_key])
            stdlib_logger.addHandler(handler)
    
    return logger


def create_file_logger(
    name: str,
    log_file: Union[str, Path],
    level: Union[str, int] = logging.INFO,
    max_size: Optional[int] = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_masking: bool = True,
    use_json: bool = True
) -> StructuredLogger:
    """
    Create a file-based structured logger
    
    Args:
        name: Logger name
        log_file: Log file path
        level: Log level
        max_size: Maximum file size for rotation (None=no rotation)
        backup_count: Number of backup files
        enable_masking: Enable sensitive data masking
        use_json: Use JSON formatting
        
    Returns:
        StructuredLogger instance
    """
    # Create handler
    handler = create_file_handler(
        filename=log_file,
        max_size=max_size,
        backup_count=backup_count
    )
    
    # Create formatter
    if use_json:
        formatter = create_json_formatter()
    else:
        formatter = create_console_formatter(use_colors=False)
    
    return create_logger(
        name=name,
        level=level,
        enable_masking=enable_masking,
        handlers=[handler],
        formatters={'file': formatter}
    )


def create_console_logger(
    name: str,
    level: Union[str, int] = logging.INFO,
    enable_masking: bool = True,
    use_colors: bool = True,
    debug_mode: bool = False
) -> StructuredLogger:
    """
    Create a console-based structured logger
    
    Args:
        name: Logger name
        level: Log level
        enable_masking: Enable sensitive data masking
        use_colors: Enable colored output
        debug_mode: Enable debug formatting
        
    Returns:
        StructuredLogger instance
    """
    # Create handler
    handler = create_console_handler()
    
    # Create formatter
    formatter = create_console_formatter(
        debug=debug_mode,
        use_colors=use_colors
    )
    
    return create_logger(
        name=name,
        level=level,
        enable_masking=enable_masking,
        handlers=[handler],
        formatters={'console': formatter}
    )


def create_production_logger(
    name: str,
    log_file: Union[str, Path],
    level: Union[str, int] = logging.INFO,
    enable_console: bool = False,
    enable_monitoring: bool = True,
    max_size: int = 50 * 1024 * 1024,  # 50MB
    backup_count: int = 10
) -> StructuredLogger:
    """
    Create a production-ready structured logger
    
    Args:
        name: Logger name
        log_file: Log file path
        level: Log level
        enable_console: Enable console output
        enable_monitoring: Enable monitoring handler
        max_size: Maximum file size for rotation
        backup_count: Number of backup files
        
    Returns:
        StructuredLogger instance
    """
    handlers = []
    formatters = {}
    
    # File handler with rotation
    file_handler = create_file_handler(
        filename=log_file,
        max_size=max_size,
        backup_count=backup_count,
        compress_rotated=True
    )
    handlers.append(file_handler)
    formatters['file'] = create_json_formatter(compact=True)
    
    # Console handler (optional)
    if enable_console:
        console_handler = create_console_handler()
        handlers.append(console_handler)
        formatters['console'] = create_console_formatter(use_colors=False)
    
    # Monitoring handler (optional)
    if enable_monitoring:
        monitoring_handler = MonitoringHandler()
        handlers.append(monitoring_handler)
    
    return create_logger(
        name=name,
        level=level,
        enable_masking=True,
        handlers=handlers,
        formatters=formatters
    )


def create_development_logger(
    name: str,
    level: Union[str, int] = logging.DEBUG,
    log_file: Optional[Union[str, Path]] = None,
    enable_async: bool = False
) -> StructuredLogger:
    """
    Create a development-friendly structured logger
    
    Args:
        name: Logger name
        level: Log level
        log_file: Optional log file path
        enable_async: Enable async logging
        
    Returns:
        StructuredLogger instance
    """
    handlers = []
    formatters = {}
    
    # Console handler with debug formatting
    console_handler = create_console_handler()
    if enable_async:
        console_handler = create_async_handler(console_handler)
    
    handlers.append(console_handler)
    formatters['console'] = create_console_formatter(debug=True, use_colors=True)
    
    # Optional file handler
    if log_file:
        file_handler = create_file_handler(filename=log_file)
        if enable_async:
            file_handler = create_async_handler(file_handler)
        
        handlers.append(file_handler)
        formatters['file'] = create_json_formatter()
    
    return create_logger(
        name=name,
        level=level,
        enable_masking=True,
        handlers=handlers,
        formatters=formatters
    )


def configure_espocrm_logging(
    level: Union[str, int] = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    enable_console: bool = True,
    enable_metrics: bool = True,
    enable_masking: bool = True,
    production_mode: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Configure EspoCRM logging system with sensible defaults
    
    Args:
        level: Global log level
        log_file: Log file path
        enable_console: Enable console logging
        enable_metrics: Enable metrics collection
        enable_masking: Enable sensitive data masking
        production_mode: Use production-optimized settings
        **kwargs: Additional configuration options
        
    Returns:
        Configuration summary
    """
    config = {
        'level': level,
        'log_file': str(log_file) if log_file else None,
        'enable_console': enable_console,
        'enable_metrics': enable_metrics,
        'enable_masking': enable_masking,
        'production_mode': production_mode,
        'loggers_created': []
    }
    
    # Setup global logging
    setup_logging(
        level=level,
        enable_console=enable_console,
        enable_file=bool(log_file),
        log_file=str(log_file) if log_file else None,
        enable_masking=enable_masking
    )
    
    # Create main EspoCRM loggers
    logger_configs = [
        ('espocrm', level),
        ('espocrm.client', level),
        ('espocrm.auth', level),
        ('espocrm.models', level),
        ('espocrm.utils', level),
    ]
    
    for logger_name, logger_level in logger_configs:
        if production_mode and log_file:
            logger = create_production_logger(
                name=logger_name,
                log_file=Path(log_file).parent / f"{logger_name.replace('.', '_')}.log",
                level=logger_level,
                enable_console=enable_console,
                **kwargs
            )
        else:
            logger = create_development_logger(
                name=logger_name,
                level=logger_level,
                log_file=log_file,
                **kwargs
            )
        
        config['loggers_created'].append(logger_name)
    
    # Setup metrics collector
    if enable_metrics:
        metrics_collector = MetricsCollector(
            enable_aggregation=True,
            logger=logging.getLogger('espocrm.metrics')
        )
        set_metrics_collector(metrics_collector)
        config['metrics_enabled'] = True
    
    # Log configuration
    main_logger = get_logger('espocrm')
    main_logger.info(
        "EspoCRM logging system configured",
        config=config
    )
    
    return config


# Default logger for the module
_module_logger = get_logger(__name__)


def get_module_logger() -> StructuredLogger:
    """Get logger for this module"""
    return _module_logger