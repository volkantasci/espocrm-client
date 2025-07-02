"""
EspoCRM Metrics Collection

Professional metrics collection system:
- API call metrics (response time, success/failure rates)
- Performance monitoring
- Counter and timer utilities
- External monitoring system integration
"""

import time
import threading
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Deque
from statistics import mean, median
import logging


@dataclass
class RequestMetrics:
    """Metrics for a single API request"""
    
    method: str
    endpoint: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    request_size_bytes: Optional[int] = None
    response_size_bytes: Optional[int] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if request was successful"""
        return self.status_code is not None and 200 <= self.status_code < 400
    
    @property
    def is_client_error(self) -> bool:
        """Check if request had client error"""
        return self.status_code is not None and 400 <= self.status_code < 500
    
    @property
    def is_server_error(self) -> bool:
        """Check if request had server error"""
        return self.status_code is not None and self.status_code >= 500
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'method': self.method,
            'endpoint': self.endpoint,
            'status_code': self.status_code,
            'response_time_ms': self.response_time_ms,
            'request_size_bytes': self.request_size_bytes,
            'response_size_bytes': self.response_size_bytes,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message,
            'user_id': self.user_id,
            'request_id': self.request_id,
            'is_success': self.is_success,
            'is_client_error': self.is_client_error,
            'is_server_error': self.is_server_error,
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    
    operation: str
    duration_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'operation': self.operation,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
        }


@dataclass
class CounterMetrics:
    """Counter metrics"""
    
    name: str
    value: int = 0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def increment(self, amount: int = 1) -> None:
        """Increment counter"""
        self.value += amount
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'value': self.value,
            'labels': self.labels,
            'timestamp': self.timestamp.isoformat(),
        }


class Timer:
    """High-precision timer for performance measurement"""
    
    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize timer
        
        Args:
            name: Timer name
            context: Additional context
        """
        self.name = name
        self.context = context or {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start(self) -> 'Timer':
        """Start timer"""
        self.start_time = time.perf_counter()
        return self
    
    def stop(self) -> float:
        """
        Stop timer and return duration
        
        Returns:
            Duration in milliseconds
        """
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        self.end_time = time.perf_counter()
        return self.duration_ms
    
    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds"""
        if self.start_time is None:
            return 0.0
        
        end_time = self.end_time or time.perf_counter()
        return (end_time - self.start_time) * 1000
    
    def __enter__(self) -> 'Timer':
        """Context manager entry"""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.stop()


class MetricsAggregator:
    """Aggregates metrics over time windows"""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize metrics aggregator
        
        Args:
            window_size: Maximum number of metrics to keep in memory
        """
        self.window_size = window_size
        self._request_metrics: Deque[RequestMetrics] = deque(maxlen=window_size)
        self._performance_metrics: Deque[PerformanceMetrics] = deque(maxlen=window_size)
        self._lock = threading.RLock()
    
    def add_request_metric(self, metric: RequestMetrics) -> None:
        """Add request metric"""
        with self._lock:
            self._request_metrics.append(metric)
    
    def add_performance_metric(self, metric: PerformanceMetrics) -> None:
        """Add performance metric"""
        with self._lock:
            self._performance_metrics.append(metric)
    
    def get_request_stats(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get aggregated request statistics
        
        Args:
            time_window: Time window for statistics (None for all)
            
        Returns:
            Aggregated statistics
        """
        with self._lock:
            metrics = list(self._request_metrics)
        
        if time_window:
            cutoff = datetime.now(timezone.utc) - time_window
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        if not metrics:
            return {}
        
        # Calculate statistics
        total_requests = len(metrics)
        successful_requests = sum(1 for m in metrics if m.is_success)
        client_errors = sum(1 for m in metrics if m.is_client_error)
        server_errors = sum(1 for m in metrics if m.is_server_error)
        
        response_times = [m.response_time_ms for m in metrics if m.response_time_ms is not None]
        
        # Group by endpoint
        endpoint_stats = defaultdict(lambda: {'count': 0, 'success': 0, 'errors': 0, 'response_times': []})
        for metric in metrics:
            key = f"{metric.method} {metric.endpoint}"
            endpoint_stats[key]['count'] += 1
            if metric.is_success:
                endpoint_stats[key]['success'] += 1
            else:
                endpoint_stats[key]['errors'] += 1
            if metric.response_time_ms is not None:
                endpoint_stats[key]['response_times'].append(metric.response_time_ms)
        
        # Calculate endpoint statistics
        for endpoint, stats in endpoint_stats.items():
            if stats['response_times']:
                stats['avg_response_time'] = mean(stats['response_times'])
                stats['median_response_time'] = median(stats['response_times'])
                stats['max_response_time'] = max(stats['response_times'])
                stats['min_response_time'] = min(stats['response_times'])
            stats['success_rate'] = stats['success'] / stats['count'] if stats['count'] > 0 else 0
            del stats['response_times']  # Remove raw data
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'client_errors': client_errors,
            'server_errors': server_errors,
            'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
            'error_rate': (client_errors + server_errors) / total_requests if total_requests > 0 else 0,
            'avg_response_time': mean(response_times) if response_times else 0,
            'median_response_time': median(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'endpoint_stats': dict(endpoint_stats),
            'time_window': str(time_window) if time_window else 'all',
            'sample_size': len(metrics)
        }
    
    def get_performance_stats(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get aggregated performance statistics
        
        Args:
            time_window: Time window for statistics (None for all)
            
        Returns:
            Aggregated statistics
        """
        with self._lock:
            metrics = list(self._performance_metrics)
        
        if time_window:
            cutoff = datetime.now(timezone.utc) - time_window
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        if not metrics:
            return {}
        
        # Group by operation
        operation_stats = defaultdict(lambda: {'count': 0, 'durations': []})
        for metric in metrics:
            operation_stats[metric.operation]['count'] += 1
            operation_stats[metric.operation]['durations'].append(metric.duration_ms)
        
        # Calculate operation statistics
        for operation, stats in operation_stats.items():
            durations = stats['durations']
            stats['avg_duration'] = mean(durations)
            stats['median_duration'] = median(durations)
            stats['max_duration'] = max(durations)
            stats['min_duration'] = min(durations)
            del stats['durations']  # Remove raw data
        
        all_durations = [m.duration_ms for m in metrics]
        
        return {
            'total_operations': len(metrics),
            'avg_duration': mean(all_durations),
            'median_duration': median(all_durations),
            'max_duration': max(all_durations),
            'min_duration': min(all_durations),
            'operation_stats': dict(operation_stats),
            'time_window': str(time_window) if time_window else 'all',
            'sample_size': len(metrics)
        }


class MetricsCollector:
    """
    Main metrics collection system
    
    Collects and aggregates various types of metrics:
    - API request metrics
    - Performance metrics
    - Custom counters
    - System metrics
    """
    
    def __init__(
        self,
        window_size: int = 1000,
        enable_aggregation: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize metrics collector
        
        Args:
            window_size: Maximum metrics to keep in memory
            enable_aggregation: Enable metrics aggregation
            logger: Logger for metrics events
        """
        self.window_size = window_size
        self.enable_aggregation = enable_aggregation
        self.logger = logger or logging.getLogger(__name__)
        
        # Metrics storage
        self._counters: Dict[str, CounterMetrics] = {}
        self._timers: Dict[str, Timer] = {}
        
        # Aggregator
        if enable_aggregation:
            self._aggregator = MetricsAggregator(window_size)
        else:
            self._aggregator = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Callbacks for external systems
        self._metric_callbacks: List[Callable[[Dict[str, Any]], None]] = []
    
    def add_metric_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add callback for metric events
        
        Args:
            callback: Callback function that receives metric data
        """
        self._metric_callbacks.append(callback)
    
    def _notify_callbacks(self, metric_data: Dict[str, Any]) -> None:
        """Notify all registered callbacks"""
        for callback in self._metric_callbacks:
            try:
                callback(metric_data)
            except Exception as e:
                self.logger.error(f"Error in metric callback: {e}")
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        **kwargs
    ) -> RequestMetrics:
        """
        Record API request metrics
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            **kwargs: Additional metric data
            
        Returns:
            RequestMetrics instance
        """
        metric = RequestMetrics(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=response_time_ms,
            **kwargs
        )
        
        if self._aggregator:
            self._aggregator.add_request_metric(metric)
        
        # Log the metric
        self.logger.info(
            f"API Request: {method} {endpoint}",
            extra={
                'metric_type': 'request',
                'metric_data': metric.to_dict()
            }
        )
        
        # Notify callbacks
        self._notify_callbacks({
            'type': 'request',
            'data': metric.to_dict()
        })
        
        return metric
    
    def record_performance(
        self,
        operation: str,
        duration_ms: float,
        context: Optional[Dict[str, Any]] = None
    ) -> PerformanceMetrics:
        """
        Record performance metrics
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            context: Additional context
            
        Returns:
            PerformanceMetrics instance
        """
        metric = PerformanceMetrics(
            operation=operation,
            duration_ms=duration_ms,
            context=context or {}
        )
        
        if self._aggregator:
            self._aggregator.add_performance_metric(metric)
        
        # Log the metric
        self.logger.info(
            f"Performance: {operation}",
            extra={
                'metric_type': 'performance',
                'metric_data': metric.to_dict()
            }
        )
        
        # Notify callbacks
        self._notify_callbacks({
            'type': 'performance',
            'data': metric.to_dict()
        })
        
        return metric
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> CounterMetrics:
        """
        Get or create counter
        
        Args:
            name: Counter name
            labels: Counter labels
            
        Returns:
            CounterMetrics instance
        """
        labels = labels or {}
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        
        with self._lock:
            if key not in self._counters:
                self._counters[key] = CounterMetrics(name=name, labels=labels)
            return self._counters[key]
    
    def increment_counter(self, name: str, amount: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment counter
        
        Args:
            name: Counter name
            amount: Increment amount
            labels: Counter labels
        """
        counter = self.get_counter(name, labels)
        counter.increment(amount)
        
        # Log counter update
        self.logger.debug(
            f"Counter incremented: {name}",
            extra={
                'metric_type': 'counter',
                'metric_data': counter.to_dict()
            }
        )
    
    def create_timer(self, name: str, context: Optional[Dict[str, Any]] = None) -> Timer:
        """
        Create timer
        
        Args:
            name: Timer name
            context: Timer context
            
        Returns:
            Timer instance
        """
        return Timer(name=name, context=context)
    
    @contextmanager
    def time_operation(self, operation: str, context: Optional[Dict[str, Any]] = None):
        """
        Context manager for timing operations
        
        Args:
            operation: Operation name
            context: Additional context
            
        Yields:
            Timer instance
        """
        timer = self.create_timer(operation, context)
        timer.start()
        try:
            yield timer
        finally:
            duration_ms = timer.stop()
            self.record_performance(operation, duration_ms, context)
    
    def get_stats(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get comprehensive statistics
        
        Args:
            time_window: Time window for statistics
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'time_window': str(time_window) if time_window else 'all'
        }
        
        if self._aggregator:
            stats['requests'] = self._aggregator.get_request_stats(time_window)
            stats['performance'] = self._aggregator.get_performance_stats(time_window)
        
        # Add counter stats
        with self._lock:
            stats['counters'] = {
                name: counter.to_dict()
                for name, counter in self._counters.items()
            }
        
        return stats
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self._counters.clear()
            self._timers.clear()
            
        if self._aggregator:
            self._aggregator = MetricsAggregator(self.window_size)
        
        self.logger.info("Metrics reset")


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get global metrics collector
    
    Returns:
        MetricsCollector instance
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """
    Set global metrics collector
    
    Args:
        collector: MetricsCollector instance
    """
    global _global_collector
    _global_collector = collector


# Convenience functions
def record_request(method: str, endpoint: str, **kwargs) -> RequestMetrics:
    """Record API request using global collector"""
    return get_metrics_collector().record_request(method, endpoint, **kwargs)


def record_performance(operation: str, duration_ms: float, **kwargs) -> PerformanceMetrics:
    """Record performance using global collector"""
    return get_metrics_collector().record_performance(operation, duration_ms, **kwargs)


def increment_counter(name: str, amount: int = 1, **kwargs) -> None:
    """Increment counter using global collector"""
    return get_metrics_collector().increment_counter(name, amount, **kwargs)


def time_operation(operation: str, context: Optional[Dict[str, Any]] = None):
    """Time operation using global collector"""
    return get_metrics_collector().time_operation(operation, context)


def get_stats(time_window: Optional[timedelta] = None) -> Dict[str, Any]:
    """Get stats using global collector"""
    return get_metrics_collector().get_stats(time_window)


class LogMetrics:
    """
    Log-specific metrics collection
    
    Tracks logging-related metrics:
    - Log counts by level
    - Error rates
    - Response times
    - Logger performance
    """
    
    def __init__(self):
        """Initialize log metrics"""
        self.total_logs = 0
        self.error_count = 0
        self.warning_count = 0
        self.log_levels: Dict[str, int] = defaultdict(int)
        self.response_times: List[float] = []
        self._lock = threading.RLock()
    
    def record_log(self, level: str, duration: Optional[float] = None) -> None:
        """
        Record a log entry
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            duration: Optional duration for the logged operation
        """
        with self._lock:
            self.total_logs += 1
            self.log_levels[level] += 1
            
            if level == 'ERROR' or level == 'CRITICAL':
                self.error_count += 1
            elif level == 'WARNING':
                self.warning_count += 1
            
            if duration is not None:
                self.response_times.append(duration)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get log statistics
        
        Returns:
            Dictionary with log statistics
        """
        with self._lock:
            stats = {
                'total_logs': self.total_logs,
                'error_count': self.error_count,
                'warning_count': self.warning_count,
                'log_levels': dict(self.log_levels),
            }
            
            if self.response_times:
                stats.update({
                    'average_response_time': mean(self.response_times),
                    'min_response_time': min(self.response_times),
                    'max_response_time': max(self.response_times),
                    'median_response_time': median(self.response_times),
                })
            else:
                stats.update({
                    'average_response_time': 0.0,
                    'min_response_time': 0.0,
                    'max_response_time': 0.0,
                    'median_response_time': 0.0,
                })
            
            return stats
    
    def reset(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self.total_logs = 0
            self.error_count = 0
            self.warning_count = 0
            self.log_levels.clear()
            self.response_times.clear()


# Update __all__ to include LogMetrics
__all__ = [
    "RequestMetrics",
    "PerformanceMetrics",
    "CounterMetrics",
    "Timer",
    "MetricsAggregator",
    "MetricsCollector",
    "LogMetrics",
    "get_metrics_collector",
    "set_metrics_collector",
    "record_request",
    "record_performance",
    "increment_counter",
    "time_operation",
    "get_stats",
]