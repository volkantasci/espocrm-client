"""
EspoCRM Helper Utilities Module

Bu modül EspoCRM API istemcisi için utility functions,
data manipulation helpers ve common operations sağlar.
"""

import re
import hashlib
import secrets
import time
from typing import Any, Dict, List, Optional, Union, Callable, Iterator
from datetime import datetime, timezone
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def snake_to_camel(snake_str: str) -> str:
    """
    Converts snake_case string to camelCase.
    
    Args:
        snake_str: Snake_case string
        
    Returns:
        camelCase string
    """
    if not snake_str:
        return snake_str
    
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """
    camelCase string'i snake_case'e çevirir.
    
    Args:
        camel_str: camelCase string
        
    Returns:
        snake_case string
        
    Example:
        >>> camel_to_snake('userName')
        'user_name'
        >>> camel_to_snake('firstNameLastName')
        'first_name_last_name'
    """
    if not camel_str:
        return camel_str
    
    # Büyük harflerden önce underscore ekle
    snake_str = re.sub('([a-z0-9])([A-Z])', r'\1_\2', camel_str)
    return snake_str.lower()


def pascal_to_snake(pascal_str: str) -> str:
    """
    PascalCase string'i snake_case'e çevirir.
    
    Args:
        pascal_str: PascalCase string
        
    Returns:
        snake_case string
        
    Example:
        >>> pascal_to_snake('UserName')
        'user_name'
        >>> pascal_to_snake('FirstNameLastName')
        'first_name_last_name'
    """
    if not pascal_str:
        return pascal_str
    
    # İlk karakteri küçük harfe çevir, sonra camel_to_snake uygula
    camel_str = pascal_str[0].lower() + pascal_str[1:] if len(pascal_str) > 1 else pascal_str.lower()
    return camel_to_snake(camel_str)


def snake_to_pascal(snake_str: str) -> str:
    """
    snake_case string'i PascalCase'e çevirir.
    
    Args:
        snake_str: snake_case string
        
    Returns:
        PascalCase string
        
    Example:
        >>> snake_to_pascal('user_name')
        'UserName'
        >>> snake_to_pascal('first_name_last_name')
        'FirstNameLastName'
    """
    if not snake_str:
        return snake_str
    
    return ''.join(word.capitalize() for word in snake_str.split('_'))


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    İki dictionary'yi deep merge eder.
    
    Args:
        dict1: İlk dictionary
        dict2: İkinci dictionary (öncelikli)
        
    Returns:
        Merge edilmiş dictionary
        
    Example:
        >>> deep_merge({'a': 1, 'b': {'c': 2}}, {'b': {'d': 3}, 'e': 4})
        {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Nested dictionary'yi flatten eder.
    
    Args:
        data: Flatten edilecek dictionary
        parent_key: Parent key prefix
        sep: Key separator
        
    Returns:
        Flatten edilmiş dictionary
        
    Example:
        >>> flatten_dict({'a': {'b': {'c': 1}}, 'd': 2})
        {'a.b.c': 1, 'd': 2}
    """
    items = []
    
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    
    return dict(items)


def unflatten_dict(data: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """
    Flatten edilmiş dictionary'yi unflatten eder.
    
    Args:
        data: Unflatten edilecek dictionary
        sep: Key separator
        
    Returns:
        Unflatten edilmiş dictionary
        
    Example:
        >>> unflatten_dict({'a.b.c': 1, 'd': 2})
        {'a': {'b': {'c': 1}}, 'd': 2}
    """
    result = {}
    
    for key, value in data.items():
        keys = key.split(sep)
        current = result
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    return result


def filter_dict(data: Dict[str, Any], keys: List[str], include: bool = True) -> Dict[str, Any]:
    """
    Dictionary'yi belirtilen key'lere göre filtreler.
    
    Args:
        data: Filtrelenecek dictionary
        keys: Filtre key'leri
        include: True ise sadece belirtilen key'ler, False ise hariç
        
    Returns:
        Filtrelenmiş dictionary
        
    Example:
        >>> filter_dict({'a': 1, 'b': 2, 'c': 3}, ['a', 'c'])
        {'a': 1, 'c': 3}
        >>> filter_dict({'a': 1, 'b': 2, 'c': 3}, ['b'], include=False)
        {'a': 1, 'c': 3}
    """
    if include:
        return {k: v for k, v in data.items() if k in keys}
    else:
        return {k: v for k, v in data.items() if k not in keys}


def clean_dict(data: Dict[str, Any], remove_none: bool = True, remove_empty: bool = False) -> Dict[str, Any]:
    """
    Dictionary'den None ve/veya boş değerleri temizler.
    
    Args:
        data: Temizlenecek dictionary
        remove_none: None değerleri kaldır
        remove_empty: Boş değerleri kaldır (empty string, list, dict)
        
    Returns:
        Temizlenmiş dictionary
        
    Example:
        >>> clean_dict({'a': 1, 'b': None, 'c': '', 'd': []})
        {'a': 1, 'c': '', 'd': []}
        >>> clean_dict({'a': 1, 'b': None, 'c': '', 'd': []}, remove_empty=True)
        {'a': 1}
    """
    result = {}
    
    for key, value in data.items():
        # None kontrolü
        if remove_none and value is None:
            continue
        
        # Empty kontrolü
        if remove_empty:
            if value == '' or value == [] or value == {}:
                continue
        
        result[key] = value
    
    return result


def generate_request_id() -> str:
    """
    Unique request ID oluşturur.
    
    Returns:
        Unique request ID
        
    Example:
        >>> generate_request_id()
        'req_1234567890abcdef'
    """
    timestamp = int(time.time() * 1000)  # Milliseconds
    random_part = secrets.token_hex(8)
    return f"req_{timestamp}_{random_part}"


def generate_hash(data: str, algorithm: str = 'sha256') -> str:
    """
    String'in hash'ini oluşturur.
    
    Args:
        data: Hash'lenecek veri
        algorithm: Hash algoritması
        
    Returns:
        Hash string
        
    Example:
        >>> generate_hash('hello world')
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data.encode('utf-8'))
    return hash_obj.hexdigest()


def mask_sensitive_data(data: str, visible_chars: int = 4, mask_char: str = '*') -> str:
    """
    Sensitive data'yı maskeler.
    
    Args:
        data: Maskelenecek veri
        visible_chars: Görünür karakter sayısı
        mask_char: Mask karakteri
        
    Returns:
        Maskelenmiş string
        
    Example:
        >>> mask_sensitive_data('secret123456')
        'secr********'
        >>> mask_sensitive_data('api_key_12345', visible_chars=6)
        'api_ke*******'
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def chunk_list(data: List[Any], chunk_size: int) -> Iterator[List[Any]]:
    """
    List'i belirtilen boyutta chunk'lara böler.
    
    Args:
        data: Bölünecek list
        chunk_size: Chunk boyutu
        
    Yields:
        List chunk'ları
        
    Example:
        >>> list(chunk_list([1, 2, 3, 4, 5], 2))
        [[1, 2], [3, 4], [5]]
    """
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Retries function execution on specified exceptions.
    
    Args:
        max_retries: Maximum retry attempts
        delay: Initial delay between retries
        backoff_factor: Factor by which the delay should be multiplied
        exceptions: Exceptions that trigger a retry
        
    Returns:
        A decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {current_delay}s: {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts: {str(e)}"
                        )
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def timing_decorator(func: Callable) -> Callable:
    """
    Logs function execution time.
    
    Args:
        func: Function to measure timing for
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # milliseconds
            logger.debug(
                f"Function {func.__name__} executed in {round(execution_time, 2)}ms"
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000  # milliseconds
            logger.error(
                f"Function {func.__name__} failed in {round(execution_time, 2)}ms: {str(e)}"
            )
            raise
    
    return wrapper


def get_utc_timestamp() -> str:
    """
    Returns UTC timestamp string in ISO format.
    
    Returns:
        UTC timestamp (ISO format)
    """
    return datetime.now(timezone.utc).isoformat()


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parses ISO format datetime string.
    
    Args:
        iso_string: ISO format datetime string
        
    Returns:
        datetime object
    """
    # Farklı ISO format'larını destekle
    formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',  # 2023-12-07T15:30:45.123456Z
        '%Y-%m-%dT%H:%M:%SZ',     # 2023-12-07T15:30:45Z
        '%Y-%m-%dT%H:%M:%S.%f',   # 2023-12-07T15:30:45.123456
        '%Y-%m-%dT%H:%M:%S',      # 2023-12-07T15:30:45
        '%Y-%m-%d %H:%M:%S',      # 2023-12-07 15:30:45
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(iso_string, fmt)
            # Timezone bilgisi yoksa UTC kabul et
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse datetime string: {iso_string}")


def safe_get(data: Dict[str, Any], key_path: str, default: Any = None, sep: str = '.') -> Any:
    """
    Nested dictionary'den güvenli şekilde değer alır.
    
    Args:
        data: Dictionary
        key_path: Key path (dot notation)
        default: Default değer
        sep: Key separator
        
    Returns:
        Değer veya default
        
    Example:
        >>> safe_get({'a': {'b': {'c': 1}}}, 'a.b.c')
        1
        >>> safe_get({'a': {'b': {}}}, 'a.b.c', 'not found')
        'not found'
    """
    keys = key_path.split(sep)
    current = data
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def safe_set(data: Dict[str, Any], key_path: str, value: Any, sep: str = '.') -> None:
    """
    Nested dictionary'ye güvenli şekilde değer atar.
    
    Args:
        data: Dictionary
        key_path: Key path (dot notation)
        value: Atanacak değer
        sep: Key separator
        
    Example:
        >>> data = {}
        >>> safe_set(data, 'a.b.c', 1)
        >>> data
        {'a': {'b': {'c': 1}}}
    """
    keys = key_path.split(sep)
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def format_bytes(bytes_count: int) -> str:
    """
    Byte sayısını human-readable format'a çevirir.
    
    Args:
        bytes_count: Byte sayısı
        
    Returns:
        Formatted string
        
    Example:
        >>> format_bytes(1024)
        '1.0 KB'
        >>> format_bytes(1048576)
        '1.0 MB'
    """
    if bytes_count == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(bytes_count)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


# Export edilecek fonksiyonlar
__all__ = [
    "snake_to_camel",
    "camel_to_snake",
    "pascal_to_snake",
    "snake_to_pascal",
    "deep_merge",
    "flatten_dict",
    "unflatten_dict",
    "filter_dict",
    "clean_dict",
    "generate_request_id",
    "generate_hash",
    "mask_sensitive_data",
    "chunk_list",
    "retry_on_exception",
    "timing_decorator",
    "get_utc_timestamp",
    "parse_iso_datetime",
    "safe_get",
    "safe_set",
    "format_bytes",
]