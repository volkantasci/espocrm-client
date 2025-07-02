"""
EspoCRM Log Formatters

Professional log formatters:
- JSON formatter for structured logging
- Console formatter for development
- Timestamp formatting utilities
- Field filtering and masking
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set, Union
from logging import LogRecord

import structlog


class BaseFormatter(logging.Formatter):
    """Base formatter with common functionality"""
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        validate: bool = True,
        exclude_fields: Optional[Set[str]] = None,
        include_fields: Optional[Set[str]] = None
    ):
        """
        Initialize base formatter
        
        Args:
            fmt: Format string
            datefmt: Date format string
            style: Format style
            validate: Validate format string
            exclude_fields: Fields to exclude from output
            include_fields: Fields to include in output (if set, only these fields)
        """
        super().__init__(fmt, datefmt, style, validate)
        self.exclude_fields = exclude_fields or set()
        self.include_fields = include_fields
    
    def filter_fields(self, record_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter fields based on include/exclude rules
        
        Args:
            record_dict: Record dictionary
            
        Returns:
            Filtered dictionary
        """
        if self.include_fields:
            # Only include specified fields
            filtered = {
                key: value for key, value in record_dict.items()
                if key in self.include_fields
            }
        else:
            # Exclude specified fields
            filtered = {
                key: value for key, value in record_dict.items()
                if key not in self.exclude_fields
            }
        
        return filtered
    
    def format_timestamp(self, timestamp: Union[float, datetime, str]) -> str:
        """
        Format timestamp consistently
        
        Args:
            timestamp: Timestamp to format
            
        Returns:
            Formatted timestamp string
        """
        if isinstance(timestamp, str):
            return timestamp
        elif isinstance(timestamp, datetime):
            return timestamp.isoformat()
        elif isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.isoformat()
        else:
            return datetime.now(timezone.utc).isoformat()


class JSONFormatter(BaseFormatter):
    """
    JSON formatter for structured logging
    
    Produces clean, parseable JSON logs suitable for:
    - Log aggregation systems (ELK, Splunk)
    - Monitoring tools (Prometheus, Grafana)
    - Cloud logging services
    """
    
    def __init__(
        self,
        exclude_fields: Optional[Set[str]] = None,
        include_fields: Optional[Set[str]] = None,
        indent: Optional[int] = None,
        ensure_ascii: bool = False,
        sort_keys: bool = True
    ):
        """
        Initialize JSON formatter
        
        Args:
            exclude_fields: Fields to exclude from JSON output
            include_fields: Fields to include in JSON output
            indent: JSON indentation (None for compact)
            ensure_ascii: Ensure ASCII output
            sort_keys: Sort JSON keys
        """
        super().__init__(
            exclude_fields=exclude_fields,
            include_fields=include_fields
        )
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.sort_keys = sort_keys
        
        # Default excluded fields for JSON
        default_excludes = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
            'filename', 'module', 'lineno', 'funcName', 'created',
            'msecs', 'relativeCreated', 'thread', 'threadName',
            'processName', 'process', 'getMessage', 'exc_info',
            'exc_text', 'stack_info'
        }
        self.exclude_fields.update(default_excludes)
    
    def format(self, record: LogRecord) -> str:
        """
        Format log record as JSON
        
        Args:
            record: Log record
            
        Returns:
            JSON formatted string
        """
        # Start with basic log structure
        log_entry = {
            'timestamp': self.format_timestamp(record.created),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        if record.stack_info:
            log_entry['stack_info'] = self.formatStack(record.stack_info)
        
        # Add custom fields from record
        record_dict = record.__dict__.copy()
        
        # Process structlog event_dict if present
        if hasattr(record, 'event_dict'):
            event_dict = record.event_dict
            if isinstance(event_dict, dict):
                # Merge event_dict into record_dict
                record_dict.update(event_dict)
        
        # Filter and add custom fields
        filtered_fields = self.filter_fields(record_dict)
        
        # Add non-standard fields to log entry
        for key, value in filtered_fields.items():
            if key not in log_entry and not key.startswith('_'):
                log_entry[key] = self._serialize_value(value)
        
        # Convert to JSON
        try:
            return json.dumps(
                log_entry,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
                sort_keys=self.sort_keys,
                default=self._json_default
            )
        except (TypeError, ValueError) as e:
            # Fallback for non-serializable objects
            log_entry['_serialization_error'] = str(e)
            log_entry['_original_message'] = str(record.getMessage())
            return json.dumps(log_entry, default=str)
    
    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize value for JSON output
        
        Args:
            value: Value to serialize
            
        Returns:
            Serializable value
        """
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, datetime):
            return value.isoformat()
        elif hasattr(value, '__dict__'):
            return self._serialize_value(value.__dict__)
        else:
            return str(value)
    
    def _json_default(self, obj: Any) -> Any:
        """
        JSON serialization fallback
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serializable representation
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)


class ConsoleFormatter(BaseFormatter):
    """
    Console formatter for development and debugging
    
    Produces human-readable colored output with:
    - Colored log levels
    - Structured field display
    - Exception formatting
    - Context information
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
        'BOLD': '\033[1m',        # Bold
        'DIM': '\033[2m',         # Dim
    }
    
    def __init__(
        self,
        use_colors: bool = True,
        show_context: bool = True,
        show_data: bool = True,
        max_field_length: int = 100,
        exclude_fields: Optional[Set[str]] = None,
        include_fields: Optional[Set[str]] = None
    ):
        """
        Initialize console formatter
        
        Args:
            use_colors: Enable colored output
            show_context: Show context information
            show_data: Show data fields
            max_field_length: Maximum field value length
            exclude_fields: Fields to exclude from output
            include_fields: Fields to include in output
        """
        super().__init__(
            exclude_fields=exclude_fields,
            include_fields=include_fields
        )
        self.use_colors = use_colors
        self.show_context = show_context
        self.show_data = show_data
        self.max_field_length = max_field_length
        
        # Default excluded fields for console
        default_excludes = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
            'filename', 'module', 'lineno', 'funcName', 'created',
            'msecs', 'relativeCreated', 'thread', 'threadName',
            'processName', 'process', 'getMessage', 'exc_info',
            'exc_text', 'stack_info', 'timestamp'
        }
        self.exclude_fields.update(default_excludes)
    
    def format(self, record: LogRecord) -> str:
        """
        Format log record for console output
        
        Args:
            record: Log record
            
        Returns:
            Formatted string
        """
        # Format timestamp
        timestamp = self.format_timestamp(record.created)
        
        # Format level with color
        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, '')
            reset = self.COLORS['RESET']
            level = f"{color}{level:<8}{reset}"
        else:
            level = f"{level:<8}"
        
        # Format logger name
        logger_name = record.name
        if len(logger_name) > 20:
            logger_name = f"...{logger_name[-17:]}"
        
        # Basic log line
        message = record.getMessage()
        log_line = f"{timestamp} {level} [{logger_name:<20}] {message}"
        
        # Add context and data if enabled
        additional_info = []
        
        if hasattr(record, 'event_dict') and isinstance(record.event_dict, dict):
            record_dict = record.__dict__.copy()
            record_dict.update(record.event_dict)
        else:
            record_dict = record.__dict__.copy()
        
        # Filter fields
        filtered_fields = self.filter_fields(record_dict)
        
        # Show context
        if self.show_context and 'context' in filtered_fields:
            context = filtered_fields['context']
            if isinstance(context, dict) and context:
                context_str = self._format_dict(context, prefix="  Context: ")
                additional_info.append(context_str)
        
        # Show data fields
        if self.show_data:
            data_fields = {
                k: v for k, v in filtered_fields.items()
                if k not in {'context', 'logger'} and not k.startswith('_')
            }
            if data_fields:
                data_str = self._format_dict(data_fields, prefix="  Data: ")
                additional_info.append(data_str)
        
        # Add exception info
        if record.exc_info:
            exc_str = self.formatException(record.exc_info)
            if self.use_colors:
                exc_str = f"{self.COLORS['DIM']}{exc_str}{self.COLORS['RESET']}"
            additional_info.append(exc_str)
        
        # Combine all parts
        if additional_info:
            return log_line + '\n' + '\n'.join(additional_info)
        else:
            return log_line
    
    def _format_dict(self, data: Dict[str, Any], prefix: str = "") -> str:
        """
        Format dictionary for console output
        
        Args:
            data: Dictionary to format
            prefix: Line prefix
            
        Returns:
            Formatted string
        """
        if not data:
            return ""
        
        lines = []
        for key, value in data.items():
            value_str = self._format_value(value)
            lines.append(f"{prefix}{key}={value_str}")
        
        return '\n'.join(lines)
    
    def _format_value(self, value: Any) -> str:
        """
        Format value for console output
        
        Args:
            value: Value to format
            
        Returns:
            Formatted string
        """
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            if len(value) > self.max_field_length:
                return f'"{value[:self.max_field_length-3]}..."'
            return f'"{value}"'
        elif isinstance(value, (list, tuple)):
            if len(value) > 5:
                return f"[{len(value)} items]"
            items = [self._format_value(item) for item in value[:5]]
            return f"[{', '.join(items)}]"
        elif isinstance(value, dict):
            if len(value) > 3:
                return f"{{{len(value)} keys}}"
            items = [f"{k}:{self._format_value(v)}" for k, v in list(value.items())[:3]]
            return f"{{{', '.join(items)}}}"
        else:
            value_str = str(value)
            if len(value_str) > self.max_field_length:
                return f"{value_str[:self.max_field_length-3]}..."
            return value_str


class CompactJSONFormatter(JSONFormatter):
    """Compact JSON formatter for high-volume logging"""
    
    def __init__(self, **kwargs):
        """Initialize compact JSON formatter"""
        kwargs.setdefault('indent', None)
        kwargs.setdefault('sort_keys', False)
        super().__init__(**kwargs)
        
        # Additional fields to exclude for compactness
        self.exclude_fields.update({
            'stack_info', 'process', 'thread', 'threadName', 'processName'
        })


class DebugFormatter(ConsoleFormatter):
    """Debug formatter with maximum verbosity"""
    
    def __init__(self, **kwargs):
        """Initialize debug formatter"""
        kwargs.setdefault('show_context', True)
        kwargs.setdefault('show_data', True)
        kwargs.setdefault('max_field_length', 500)
        super().__init__(**kwargs)
        
        # Don't exclude as many fields in debug mode
        self.exclude_fields = {
            'msg', 'args', 'getMessage', 'exc_info', 'exc_text'
        }


# Formatter factory functions
def create_json_formatter(
    compact: bool = False,
    exclude_fields: Optional[Set[str]] = None,
    include_fields: Optional[Set[str]] = None
) -> JSONFormatter:
    """
    Create JSON formatter
    
    Args:
        compact: Use compact formatting
        exclude_fields: Fields to exclude
        include_fields: Fields to include
        
    Returns:
        JSONFormatter instance
    """
    if compact:
        return CompactJSONFormatter(
            exclude_fields=exclude_fields,
            include_fields=include_fields
        )
    else:
        return JSONFormatter(
            exclude_fields=exclude_fields,
            include_fields=include_fields
        )


def create_console_formatter(
    debug: bool = False,
    use_colors: bool = True,
    exclude_fields: Optional[Set[str]] = None,
    include_fields: Optional[Set[str]] = None
) -> ConsoleFormatter:
    """
    Create console formatter
    
    Args:
        debug: Use debug formatting
        use_colors: Enable colored output
        exclude_fields: Fields to exclude
        include_fields: Fields to include
        
    Returns:
        ConsoleFormatter instance
    """
    if debug:
        return DebugFormatter(
            use_colors=use_colors,
            exclude_fields=exclude_fields,
            include_fields=include_fields
        )
    else:
        return ConsoleFormatter(
            use_colors=use_colors,
            exclude_fields=exclude_fields,
            include_fields=include_fields
        )


class StructuredFormatter(BaseFormatter):
    """
    Structured formatter for key-value pair output
    
    Produces structured logs in key=value format suitable for:
    - Log parsing tools
    - Grep-friendly searching
    - Human-readable structured data
    """
    
    def __init__(
        self,
        separator: str = " ",
        key_value_separator: str = "=",
        quote_values: bool = True,
        exclude_fields: Optional[Set[str]] = None,
        include_fields: Optional[Set[str]] = None
    ):
        """
        Initialize structured formatter
        
        Args:
            separator: Separator between key-value pairs
            key_value_separator: Separator between key and value
            quote_values: Quote string values
            exclude_fields: Fields to exclude from output
            include_fields: Fields to include in output
        """
        super().__init__(
            exclude_fields=exclude_fields,
            include_fields=include_fields
        )
        self.separator = separator
        self.key_value_separator = key_value_separator
        self.quote_values = quote_values
        
        # Default excluded fields for structured format
        default_excludes = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
            'filename', 'module', 'lineno', 'funcName', 'created',
            'msecs', 'relativeCreated', 'thread', 'threadName',
            'processName', 'process', 'getMessage', 'exc_info',
            'exc_text', 'stack_info'
        }
        self.exclude_fields.update(default_excludes)
    
    def format(self, record: LogRecord) -> str:
        """
        Format log record as structured key-value pairs
        
        Args:
            record: Log record
            
        Returns:
            Structured formatted string
        """
        # Start with basic log structure
        parts = [
            f"timestamp{self.key_value_separator}{self.format_timestamp(record.created)}",
            f"level{self.key_value_separator}{record.levelname}",
            f"logger{self.key_value_separator}{record.name}",
            f"message{self.key_value_separator}{self._format_value(record.getMessage())}"
        ]
        
        # Add custom fields from record
        record_dict = record.__dict__.copy()
        
        # Process structlog event_dict if present
        if hasattr(record, 'event_dict'):
            event_dict = record.event_dict
            if isinstance(event_dict, dict):
                record_dict.update(event_dict)
        
        # Filter and add custom fields
        filtered_fields = self.filter_fields(record_dict)
        
        for key, value in filtered_fields.items():
            if not key.startswith('_'):
                formatted_value = self._format_value(value)
                parts.append(f"{key}{self.key_value_separator}{formatted_value}")
        
        # Add exception info if present
        if record.exc_info:
            exc_str = self.formatException(record.exc_info).replace('\n', '\\n')
            parts.append(f"exception{self.key_value_separator}{self._format_value(exc_str)}")
        
        return self.separator.join(parts)
    
    def _format_value(self, value: Any) -> str:
        """
        Format value for structured output
        
        Args:
            value: Value to format
            
        Returns:
            Formatted string
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            if self.quote_values and (' ' in value or self.separator in value or self.key_value_separator in value):
                return f'"{value}"'
            return value
        elif isinstance(value, (list, tuple)):
            items = [self._format_value(item) for item in value]
            return f"[{','.join(items)}]"
        elif isinstance(value, dict):
            items = [f"{k}:{self._format_value(v)}" for k, v in value.items()]
            return f"{{{','.join(items)}}}"
        else:
            str_value = str(value)
            if self.quote_values and (' ' in str_value or self.separator in str_value or self.key_value_separator in str_value):
                return f'"{str_value}"'
            return str_value


class ColoredFormatter(ConsoleFormatter):
    """
    Colored formatter with enhanced color support
    
    Extends ConsoleFormatter with additional color features:
    - Level-specific colors
    - Field highlighting
    - Error emphasis
    - Custom color schemes
    """
    
    # Extended color palette
    EXTENDED_COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
        'BOLD': '\033[1m',        # Bold
        'DIM': '\033[2m',         # Dim
        'UNDERLINE': '\033[4m',   # Underline
        'BLINK': '\033[5m',       # Blink
        'REVERSE': '\033[7m',     # Reverse
        'STRIKETHROUGH': '\033[9m', # Strikethrough
        # Background colors
        'BG_BLACK': '\033[40m',
        'BG_RED': '\033[41m',
        'BG_GREEN': '\033[42m',
        'BG_YELLOW': '\033[43m',
        'BG_BLUE': '\033[44m',
        'BG_MAGENTA': '\033[45m',
        'BG_CYAN': '\033[46m',
        'BG_WHITE': '\033[47m',
        # Bright colors
        'BRIGHT_BLACK': '\033[90m',
        'BRIGHT_RED': '\033[91m',
        'BRIGHT_GREEN': '\033[92m',
        'BRIGHT_YELLOW': '\033[93m',
        'BRIGHT_BLUE': '\033[94m',
        'BRIGHT_MAGENTA': '\033[95m',
        'BRIGHT_CYAN': '\033[96m',
        'BRIGHT_WHITE': '\033[97m',
    }
    
    def __init__(
        self,
        color_scheme: Optional[Dict[str, str]] = None,
        highlight_fields: Optional[Set[str]] = None,
        **kwargs
    ):
        """
        Initialize colored formatter
        
        Args:
            color_scheme: Custom color scheme mapping
            highlight_fields: Fields to highlight with special colors
            **kwargs: Additional arguments for ConsoleFormatter
        """
        super().__init__(**kwargs)
        
        # Merge extended colors
        self.COLORS.update(self.EXTENDED_COLORS)
        
        # Apply custom color scheme
        if color_scheme:
            self.COLORS.update(color_scheme)
        
        self.highlight_fields = highlight_fields or {'error', 'exception', 'user_id', 'request_id'}
    
    def format(self, record: LogRecord) -> str:
        """
        Format log record with enhanced colors
        
        Args:
            record: Log record
            
        Returns:
            Colored formatted string
        """
        if not self.use_colors:
            return super().format(record)
        
        # Get base formatted output
        formatted = super().format(record)
        
        # Apply level-specific background for critical errors
        if record.levelname == 'CRITICAL':
            formatted = f"{self.COLORS['BG_RED']}{self.COLORS['BRIGHT_WHITE']}{formatted}{self.COLORS['RESET']}"
        elif record.levelname == 'ERROR':
            # Make errors more prominent
            formatted = f"{self.COLORS['BOLD']}{formatted}{self.COLORS['RESET']}"
        
        return formatted
    
    def _format_dict(self, data: Dict[str, Any], prefix: str = "") -> str:
        """
        Format dictionary with field highlighting
        
        Args:
            data: Dictionary to format
            prefix: Line prefix
            
        Returns:
            Formatted string with colors
        """
        if not data:
            return ""
        
        lines = []
        for key, value in data.items():
            value_str = self._format_value(value)
            
            # Highlight special fields
            if self.use_colors and key.lower() in self.highlight_fields:
                key_colored = f"{self.COLORS['BOLD']}{self.COLORS['BRIGHT_YELLOW']}{key}{self.COLORS['RESET']}"
                value_colored = f"{self.COLORS['BRIGHT_CYAN']}{value_str}{self.COLORS['RESET']}"
                lines.append(f"{prefix}{key_colored}={value_colored}")
            else:
                lines.append(f"{prefix}{key}={value_str}")
        
        return '\n'.join(lines)


# Update __all__ to include new formatters
__all__ = [
    "BaseFormatter",
    "JSONFormatter",
    "ConsoleFormatter",
    "StructuredFormatter",
    "ColoredFormatter",
    "CompactJSONFormatter",
    "DebugFormatter",
    "create_json_formatter",
    "create_console_formatter",
]