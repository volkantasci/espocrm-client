"""
EspoCRM Log Handlers

Professional log handlers:
- File handler with rotation
- Console handler with color support
- Rotating file handler
- External monitoring system integration
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler as StdRotatingFileHandler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, Union, Dict, Any, TextIO
import threading
import queue
import time
from datetime import datetime, timezone


class ThreadSafeHandler(logging.Handler):
    """Base class for thread-safe handlers"""
    
    def __init__(self, level: int = logging.NOTSET):
        """Initialize thread-safe handler"""
        super().__init__(level)
        self._lock = threading.RLock()
    
    def emit(self, record: logging.LogRecord) -> None:
        """Thread-safe emit method"""
        with self._lock:
            self._emit(record)
    
    def _emit(self, record: logging.LogRecord) -> None:
        """Actual emit implementation - to be overridden"""
        raise NotImplementedError


class FileHandler(ThreadSafeHandler):
    """
    Enhanced file handler with:
    - Thread-safe operations
    - Automatic directory creation
    - File permission management
    - Error recovery
    """
    
    def __init__(
        self,
        filename: Union[str, Path],
        mode: str = 'a',
        encoding: Optional[str] = 'utf-8',
        delay: bool = False,
        errors: Optional[str] = None,
        create_dirs: bool = True,
        file_permissions: Optional[int] = 0o644
    ):
        """
        Initialize file handler
        
        Args:
            filename: Log file path
            mode: File open mode
            encoding: File encoding
            delay: Delay file opening until first log
            errors: Error handling mode
            create_dirs: Create parent directories if needed
            file_permissions: File permissions (octal)
        """
        super().__init__()
        
        self.filename = Path(filename)
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        self.errors = errors
        self.create_dirs = create_dirs
        self.file_permissions = file_permissions
        
        self.stream: Optional[TextIO] = None
        
        if not delay:
            self._open()
    
    def _open(self) -> None:
        """Open log file"""
        if self.create_dirs:
            self.filename.parent.mkdir(parents=True, exist_ok=True)
        
        self.stream = open(
            self.filename,
            self.mode,
            encoding=self.encoding,
            errors=self.errors
        )
        
        # Set file permissions
        if self.file_permissions is not None:
            try:
                os.chmod(self.filename, self.file_permissions)
            except (OSError, AttributeError):
                # Ignore permission errors on systems that don't support it
                pass
    
    def _emit(self, record: logging.LogRecord) -> None:
        """Emit log record to file"""
        try:
            if self.stream is None:
                self._open()
            
            if self.stream:
                msg = self.format(record)
                self.stream.write(msg + '\n')
                self.stream.flush()
                
        except Exception as e:
            self.handleError(record)
    
    def close(self) -> None:
        """Close file handler"""
        with self._lock:
            if self.stream:
                try:
                    self.stream.close()
                finally:
                    self.stream = None
        super().close()


class ConsoleHandler(ThreadSafeHandler):
    """
    Enhanced console handler with:
    - Color support detection
    - Stream selection (stdout/stderr)
    - Error recovery
    """
    
    def __init__(
        self,
        stream: Optional[TextIO] = None,
        use_stderr_for_errors: bool = True,
        force_colors: Optional[bool] = None
    ):
        """
        Initialize console handler
        
        Args:
            stream: Output stream (default: sys.stdout)
            use_stderr_for_errors: Use stderr for ERROR/CRITICAL levels
            force_colors: Force color usage (None=auto-detect)
        """
        super().__init__()
        
        self.stream = stream or sys.stdout
        self.use_stderr_for_errors = use_stderr_for_errors
        
        # Color support detection
        if force_colors is not None:
            self.supports_color = force_colors
        else:
            self.supports_color = self._detect_color_support()
    
    def _detect_color_support(self) -> bool:
        """Detect if terminal supports colors"""
        # Check if we're in a TTY
        if not hasattr(self.stream, 'isatty') or not self.stream.isatty():
            return False
        
        # Check environment variables
        term = os.environ.get('TERM', '').lower()
        if 'color' in term or term in ('xterm', 'xterm-256color', 'screen'):
            return True
        
        # Check for common CI environments that support colors
        ci_envs = ['GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL', 'BUILDKITE']
        if any(env in os.environ for env in ci_envs):
            return True
        
        return False
    
    def _get_stream_for_level(self, level: int) -> TextIO:
        """Get appropriate stream for log level"""
        if self.use_stderr_for_errors and level >= logging.ERROR:
            return sys.stderr
        return self.stream
    
    def _emit(self, record: logging.LogRecord) -> None:
        """Emit log record to console"""
        try:
            stream = self._get_stream_for_level(record.levelno)
            msg = self.format(record)
            
            # Update formatter color support if needed
            if hasattr(self.formatter, 'use_colors'):
                self.formatter.use_colors = self.supports_color
            
            stream.write(msg + '\n')
            stream.flush()
            
        except Exception:
            self.handleError(record)


class RotatingFileHandler(StdRotatingFileHandler):
    """
    Enhanced rotating file handler with:
    - Thread-safe operations
    - Automatic directory creation
    - Better error handling
    - Compression support
    """
    
    def __init__(
        self,
        filename: Union[str, Path],
        mode: str = 'a',
        maxBytes: int = 10 * 1024 * 1024,  # 10MB
        backupCount: int = 5,
        encoding: Optional[str] = 'utf-8',
        delay: bool = False,
        errors: Optional[str] = None,
        create_dirs: bool = True,
        file_permissions: Optional[int] = 0o644,
        compress_rotated: bool = False
    ):
        """
        Initialize rotating file handler
        
        Args:
            filename: Log file path
            mode: File open mode
            maxBytes: Maximum file size before rotation
            backupCount: Number of backup files to keep
            encoding: File encoding
            delay: Delay file opening until first log
            errors: Error handling mode
            create_dirs: Create parent directories if needed
            file_permissions: File permissions (octal)
            compress_rotated: Compress rotated files
        """
        self.filename_path = Path(filename)
        self.create_dirs = create_dirs
        self.file_permissions = file_permissions
        self.compress_rotated = compress_rotated
        
        if create_dirs:
            self.filename_path.parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(
            str(filename), mode, maxBytes, backupCount, encoding, delay, errors
        )
    
    def _open(self):
        """Open log file with permission setting"""
        stream = super()._open()
        
        # Set file permissions
        if self.file_permissions is not None:
            try:
                os.chmod(self.baseFilename, self.file_permissions)
            except (OSError, AttributeError):
                pass
        
        return stream
    
    def doRollover(self):
        """Perform file rollover with optional compression"""
        super().doRollover()
        
        if self.compress_rotated and self.backupCount > 0:
            self._compress_backup_files()
    
    def _compress_backup_files(self):
        """Compress backup files"""
        try:
            import gzip
            import shutil
            
            for i in range(1, self.backupCount + 1):
                backup_file = f"{self.baseFilename}.{i}"
                compressed_file = f"{backup_file}.gz"
                
                if os.path.exists(backup_file) and not os.path.exists(compressed_file):
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Remove original file after compression
                    os.remove(backup_file)
                    
        except ImportError:
            # gzip not available
            pass
        except Exception:
            # Ignore compression errors
            pass


class TimedRotatingHandler(TimedRotatingFileHandler):
    """
    Enhanced timed rotating file handler with:
    - Thread-safe operations
    - Automatic directory creation
    - Better error handling
    """
    
    def __init__(
        self,
        filename: Union[str, Path],
        when: str = 'midnight',
        interval: int = 1,
        backupCount: int = 7,
        encoding: Optional[str] = 'utf-8',
        delay: bool = False,
        utc: bool = True,
        atTime: Optional[datetime] = None,
        errors: Optional[str] = None,
        create_dirs: bool = True,
        file_permissions: Optional[int] = 0o644
    ):
        """
        Initialize timed rotating file handler
        
        Args:
            filename: Log file path
            when: Rotation interval type ('S', 'M', 'H', 'D', 'midnight', 'W0'-'W6')
            interval: Rotation interval
            backupCount: Number of backup files to keep
            encoding: File encoding
            delay: Delay file opening until first log
            utc: Use UTC time
            atTime: Specific time for daily rotation
            errors: Error handling mode
            create_dirs: Create parent directories if needed
            file_permissions: File permissions (octal)
        """
        self.filename_path = Path(filename)
        self.create_dirs = create_dirs
        self.file_permissions = file_permissions
        
        if create_dirs:
            self.filename_path.parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(
            str(filename), when, interval, backupCount, encoding, delay, utc, atTime, errors
        )
    
    def _open(self):
        """Open log file with permission setting"""
        stream = super()._open()
        
        # Set file permissions
        if self.file_permissions is not None:
            try:
                os.chmod(self.baseFilename, self.file_permissions)
            except (OSError, AttributeError):
                pass
        
        return stream


class AsyncHandler(logging.Handler):
    """
    Asynchronous log handler for high-performance logging
    
    Queues log records and processes them in a background thread
    to avoid blocking the main application thread.
    """
    
    def __init__(
        self,
        target_handler: logging.Handler,
        queue_size: int = 1000,
        timeout: float = 1.0,
        drop_on_full: bool = True
    ):
        """
        Initialize async handler
        
        Args:
            target_handler: Handler to process records asynchronously
            queue_size: Maximum queue size
            timeout: Queue timeout
            drop_on_full: Drop records if queue is full
        """
        super().__init__()
        
        self.target_handler = target_handler
        self.queue_size = queue_size
        self.timeout = timeout
        self.drop_on_full = drop_on_full
        
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._started = False
    
    def start(self) -> None:
        """Start background processing thread"""
        if not self._started:
            self._thread = threading.Thread(target=self._process_queue, daemon=True)
            self._thread.start()
            self._started = True
    
    def stop(self) -> None:
        """Stop background processing thread"""
        if self._started:
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)
            self._started = False
    
    def emit(self, record: logging.LogRecord) -> None:
        """Queue log record for async processing"""
        if not self._started:
            self.start()
        
        try:
            if self.drop_on_full:
                self._queue.put_nowait(record)
            else:
                self._queue.put(record, timeout=self.timeout)
        except queue.Full:
            if not self.drop_on_full:
                # If we can't drop and queue is full, handle synchronously
                self.target_handler.emit(record)
    
    def _process_queue(self) -> None:
        """Process queued log records"""
        while not self._stop_event.is_set():
            try:
                record = self._queue.get(timeout=0.1)
                self.target_handler.emit(record)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                # Ignore errors in background thread
                pass
    
    def close(self) -> None:
        """Close async handler"""
        self.stop()
        self.target_handler.close()
        super().close()


class MonitoringHandler(logging.Handler):
    """
    Handler for external monitoring systems
    
    Prepares logs for integration with:
    - Prometheus metrics
    - Grafana dashboards
    - External monitoring services
    """
    
    def __init__(
        self,
        metrics_callback: Optional[callable] = None,
        alert_callback: Optional[callable] = None,
        error_threshold: int = logging.ERROR
    ):
        """
        Initialize monitoring handler
        
        Args:
            metrics_callback: Callback for metrics collection
            alert_callback: Callback for alerts
            error_threshold: Log level threshold for alerts
        """
        super().__init__()
        
        self.metrics_callback = metrics_callback
        self.alert_callback = alert_callback
        self.error_threshold = error_threshold
        
        # Metrics counters
        self._log_counts: Dict[str, int] = {}
        self._error_counts: Dict[str, int] = {}
        self._last_reset = time.time()
    
    def emit(self, record: logging.LogRecord) -> None:
        """Process log record for monitoring"""
        try:
            # Update counters
            level_name = record.levelname
            self._log_counts[level_name] = self._log_counts.get(level_name, 0) + 1
            
            # Track errors by logger
            if record.levelno >= logging.ERROR:
                logger_name = record.name
                self._error_counts[logger_name] = self._error_counts.get(logger_name, 0) + 1
            
            # Call metrics callback
            if self.metrics_callback:
                self.metrics_callback(record, self._log_counts, self._error_counts)
            
            # Call alert callback for high-severity logs
            if self.alert_callback and record.levelno >= self.error_threshold:
                self.alert_callback(record)
                
        except Exception:
            self.handleError(record)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            'log_counts': self._log_counts.copy(),
            'error_counts': self._error_counts.copy(),
            'last_reset': self._last_reset
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics counters"""
        self._log_counts.clear()
        self._error_counts.clear()
        self._last_reset = time.time()


# Handler factory functions
def create_file_handler(
    filename: Union[str, Path],
    max_size: Optional[int] = None,
    backup_count: int = 5,
    **kwargs
) -> Union[FileHandler, RotatingFileHandler]:
    """
    Create file handler with optional rotation
    
    Args:
        filename: Log file path
        max_size: Maximum file size for rotation (None=no rotation)
        backup_count: Number of backup files
        **kwargs: Additional handler arguments
        
    Returns:
        File handler instance
    """
    if max_size:
        return RotatingFileHandler(
            filename=filename,
            maxBytes=max_size,
            backupCount=backup_count,
            **kwargs
        )
    else:
        return FileHandler(filename=filename, **kwargs)


def create_console_handler(**kwargs) -> ConsoleHandler:
    """
    Create console handler
    
    Args:
        **kwargs: Handler arguments
        
    Returns:
        Console handler instance
    """
    return ConsoleHandler(**kwargs)


def create_async_handler(
    target_handler: logging.Handler,
    **kwargs
) -> AsyncHandler:
    """
    Create async handler wrapper
    
    Args:
        target_handler: Handler to wrap
        **kwargs: Async handler arguments
        
    Returns:
        Async handler instance
    """
    return AsyncHandler(target_handler=target_handler, **kwargs)


class HTTPHandler(logging.Handler):
    """
    HTTP handler for sending logs to remote endpoints
    
    Sends log records to HTTP endpoints for:
    - Centralized logging services
    - Log aggregation systems
    - Monitoring dashboards
    - Alert systems
    """
    
    def __init__(
        self,
        url: str,
        method: str = 'POST',
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        batch_size: int = 1,
        flush_interval: float = 5.0
    ):
        """
        Initialize HTTP handler
        
        Args:
            url: Target URL for log submissions
            method: HTTP method (POST, PUT, etc.)
            headers: Additional HTTP headers
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts
            retry_delay: Delay between retries
            batch_size: Number of logs to batch together
            flush_interval: Interval to flush batched logs
        """
        super().__init__()
        
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Batching support
        self._batch: list = []
        self._last_flush = time.time()
        self._lock = threading.RLock()
        
        # Default headers
        self.headers.setdefault('Content-Type', 'application/json')
        self.headers.setdefault('User-Agent', 'EspoCRM-Python-Client/1.0')
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record via HTTP"""
        try:
            log_entry = self._format_record(record)
            
            with self._lock:
                self._batch.append(log_entry)
                
                # Check if we should flush
                should_flush = (
                    len(self._batch) >= self.batch_size or
                    time.time() - self._last_flush >= self.flush_interval
                )
                
                if should_flush:
                    self._flush_batch()
                    
        except Exception:
            self.handleError(record)
    
    def _format_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Format log record for HTTP transmission"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key not in log_entry and not key.startswith('_') and key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                try:
                    # Only include JSON-serializable values
                    import json
                    json.dumps(value)
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)
        
        return log_entry
    
    def _flush_batch(self) -> None:
        """Flush batched log records"""
        if not self._batch:
            return
        
        batch_to_send = self._batch.copy()
        self._batch.clear()
        self._last_flush = time.time()
        
        # Send in background thread to avoid blocking
        thread = threading.Thread(
            target=self._send_batch,
            args=(batch_to_send,),
            daemon=True
        )
        thread.start()
    
    def _send_batch(self, batch: list) -> None:
        """Send batch of log records via HTTP"""
        import json
        
        try:
            # Prepare payload
            if len(batch) == 1:
                payload = batch[0]
            else:
                payload = {'logs': batch}
            
            data = json.dumps(payload, default=str)
            
            # Send with retries
            for attempt in range(self.retry_count + 1):
                try:
                    import requests
                    
                    response = requests.request(
                        method=self.method,
                        url=self.url,
                        data=data,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    response.raise_for_status()
                    break  # Success
                    
                except Exception as e:
                    if attempt < self.retry_count:
                        time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    else:
                        # Final attempt failed, log error locally
                        import sys
                        print(f"HTTPHandler failed to send logs: {e}", file=sys.stderr)
                        
        except Exception as e:
            import sys
            print(f"HTTPHandler error: {e}", file=sys.stderr)
    
    def flush(self) -> None:
        """Flush any pending log records"""
        with self._lock:
            self._flush_batch()
    
    def close(self) -> None:
        """Close HTTP handler"""
        self.flush()
        super().close()


# Update __all__ to include new handler
__all__ = [
    "ThreadSafeHandler",
    "FileHandler",
    "ConsoleHandler",
    "RotatingFileHandler",
    "TimedRotatingHandler",
    "AsyncHandler",
    "MonitoringHandler",
    "HTTPHandler",
    "create_file_handler",
    "create_console_handler",
    "create_async_handler",
]