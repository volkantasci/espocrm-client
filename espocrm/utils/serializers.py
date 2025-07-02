"""
EspoCRM Serialization Module

Bu modül EspoCRM API istemcisi için JSON serialization/deserialization,
date/datetime handling ve EspoCRM specific data transformations sağlar.
"""

import json
import re
from datetime import datetime, date, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union, Tuple
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


class EspoCRMJSONEncoder(json.JSONEncoder):
    """
    EspoCRM için özelleştirilmiş JSON encoder.
    
    Date/datetime, Decimal ve diğer Python tiplerini EspoCRM formatına çevirir.
    """
    
    def default(self, obj: Any) -> Any:
        """JSON serialization için custom encoder."""
        if isinstance(obj, datetime):
            # EspoCRM datetime format: YYYY-MM-DD HH:MM:SS
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        
        elif isinstance(obj, date):
            # EspoCRM date format: YYYY-MM-DD
            return obj.strftime('%Y-%m-%d')
        
        elif isinstance(obj, time):
            # EspoCRM time format: HH:MM:SS
            return obj.strftime('%H:%M:%S')
        
        elif isinstance(obj, Decimal):
            # Decimal'ı float'a çevir
            return float(obj)
        
        elif hasattr(obj, '__dict__'):
            # Model objelerini dict'e çevir
            return obj.__dict__
        
        elif hasattr(obj, 'to_dict'):
            # to_dict metodu varsa kullan
            return obj.to_dict()
        
        return super().default(obj)


class EspoCRMJSONDecoder(json.JSONDecoder):
    """
    EspoCRM için özelleştirilmiş JSON decoder.
    
    EspoCRM formatındaki date/datetime string'lerini Python objelerine çevirir.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)
    
    def object_hook(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """JSON deserialization için custom decoder."""
        if not isinstance(obj, dict):
            return obj
        
        # Date/datetime field'ları dönüştür
        for key, value in obj.items():
            if isinstance(value, str):
                # DateTime pattern: YYYY-MM-DD HH:MM:SS
                if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', value):
                    try:
                        obj[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass
                
                # Date pattern: YYYY-MM-DD
                elif re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                    try:
                        obj[key] = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                # Time pattern: HH:MM:SS
                elif re.match(r'^\d{2}:\d{2}:\d{2}$', value):
                    try:
                        obj[key] = datetime.strptime(value, '%H:%M:%S').time()
                    except ValueError:
                        pass
        
        return obj


class DataSerializer:
    """
    EspoCRM veri serialization/deserialization sınıfı.
    
    JSON encoding/decoding, data transformation ve validation sağlar.
    """
    
    def __init__(
        self,
        date_format: str = '%Y-%m-%d',
        datetime_format: str = '%Y-%m-%d %H:%M:%S',
        time_format: str = '%H:%M:%S',
        ensure_ascii: bool = False,
        indent: Optional[int] = None
    ):
        """
        Data serializer'ı başlatır.
        
        Args:
            date_format: Date format string
            datetime_format: DateTime format string
            time_format: Time format string
            ensure_ascii: JSON'da ASCII karakterleri zorla
            indent: JSON indentation
        """
        self.date_format = date_format
        self.datetime_format = datetime_format
        self.time_format = time_format
        self.ensure_ascii = ensure_ascii
        self.indent = indent
        
        # JSON encoder/decoder
        self.encoder = EspoCRMJSONEncoder(
            ensure_ascii=ensure_ascii,
            indent=indent
        )
        self.decoder = EspoCRMJSONDecoder()
    
    def serialize(self, data: Any) -> str:
        """
        Python objesini JSON string'e çevirir.
        
        Args:
            data: Serialize edilecek veri
            
        Returns:
            JSON string
            
        Raises:
            ValueError: Serialization hatası
        """
        try:
            return self.encoder.encode(data)
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error: {e}")
            raise ValueError(f"Failed to serialize data: {e}")
    
    def deserialize(self, json_str: str) -> Any:
        """
        JSON string'i Python objesine çevirir.
        
        Args:
            json_str: JSON string
            
        Returns:
            Python objesi
            
        Raises:
            ValueError: Deserialization hatası
        """
        try:
            return self.decoder.decode(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Deserialization error: {e}")
            raise ValueError(f"Failed to deserialize JSON: {e}")
    
    def serialize_to_bytes(self, data: Any, encoding: str = 'utf-8') -> bytes:
        """
        Python objesini JSON bytes'a çevirir.
        
        Args:
            data: Serialize edilecek veri
            encoding: Encoding formatı
            
        Returns:
            JSON bytes
        """
        json_str = self.serialize(data)
        return json_str.encode(encoding)
    
    def deserialize_from_bytes(self, json_bytes: bytes, encoding: str = 'utf-8') -> Any:
        """
        JSON bytes'ı Python objesine çevirir.
        
        Args:
            json_bytes: JSON bytes
            encoding: Encoding formatı
            
        Returns:
            Python objesi
        """
        json_str = json_bytes.decode(encoding)
        return self.deserialize(json_str)
    
    def transform_for_espocrm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Python verisini EspoCRM formatına dönüştürür.
        
        Args:
            data: Dönüştürülecek veri
            
        Returns:
            EspoCRM formatında veri
        """
        if not isinstance(data, dict):
            return data
        
        transformed = {}
        
        for key, value in data.items():
            # None değerleri null olarak gönder
            if value is None:
                transformed[key] = None
            
            # Boolean değerleri
            elif isinstance(value, bool):
                transformed[key] = value
            
            # Date/datetime dönüşümleri
            elif isinstance(value, datetime):
                transformed[key] = value.strftime(self.datetime_format)
            
            elif isinstance(value, date):
                transformed[key] = value.strftime(self.date_format)
            
            elif isinstance(value, time):
                transformed[key] = value.strftime(self.time_format)
            
            # Decimal dönüşümü
            elif isinstance(value, Decimal):
                transformed[key] = float(value)
            
            # List/dict recursive dönüşüm
            elif isinstance(value, list):
                transformed[key] = [
                    self.transform_for_espocrm(item) if isinstance(item, dict) else item
                    for item in value
                ]
            
            elif isinstance(value, dict):
                transformed[key] = self.transform_for_espocrm(value)
            
            # Diğer değerler
            else:
                transformed[key] = value
        
        return transformed
    
    def transform_from_espocrm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        EspoCRM verisini Python formatına dönüştürür.
        
        Args:
            data: EspoCRM'den gelen veri
            
        Returns:
            Python formatında veri
        """
        # JSON decoder zaten date/datetime dönüşümlerini yapıyor
        return data


def build_query_string(params: Dict[str, Any], doseq: bool = False) -> str:
    """
    Query parameters'ı URL query string'e çevirir.
    
    PHP'nin http_build_query fonksiyonuna benzer davranış.
    
    Args:
        params: Query parameters
        doseq: Sequence'ları ayrı parametreler olarak işle
        
    Returns:
        URL query string
        
    Example:
        >>> build_query_string({'name': 'John', 'age': 30})
        'name=John&age=30'
        >>> build_query_string({'tags': ['python', 'api']})
        'tags[]=python&tags[]=api'
    """
    if not params:
        return ''
    
    def _encode_param(key: str, value: Any, parent_key: str = '') -> List[Tuple[str, str]]:
        """Parametreyi encode eder."""
        result = []
        
        if isinstance(value, dict):
            # Nested dictionary
            for sub_key, sub_value in value.items():
                new_key = f"{parent_key}[{sub_key}]" if parent_key else f"{key}[{sub_key}]"
                result.extend(_encode_param(sub_key, sub_value, new_key))
        
        elif isinstance(value, (list, tuple)):
            # Array/list
            if doseq:
                # Her element için ayrı parametre
                for item in value:
                    array_key = f"{parent_key}[]" if parent_key else f"{key}[]"
                    result.append((array_key, str(item)))
            else:
                # Comma-separated
                array_key = parent_key if parent_key else key
                result.append((array_key, ','.join(str(item) for item in value)))
        
        elif isinstance(value, bool):
            # Boolean değerler
            param_key = parent_key if parent_key else key
            result.append((param_key, '1' if value else '0'))
        
        elif value is None:
            # None değerler
            param_key = parent_key if parent_key else key
            result.append((param_key, ''))
        
        else:
            # Diğer değerler
            param_key = parent_key if parent_key else key
            result.append((param_key, str(value)))
        
        return result
    
    # Tüm parametreleri encode et
    encoded_params = []
    for key, value in params.items():
        encoded_params.extend(_encode_param(key, value))
    
    # URL encode et
    return urlencode(encoded_params, doseq=False)


def parse_espocrm_response(response_data: Any) -> Dict[str, Any]:
    """
    EspoCRM API response'unu parse eder.
    
    Args:
        response_data: API'den gelen raw data
        
    Returns:
        Parse edilmiş veri
    """
    if not isinstance(response_data, dict):
        return {'data': response_data}
    
    # EspoCRM standart response formatı
    parsed = {
        'data': response_data.get('list', response_data),
        'total': response_data.get('total'),
        'offset': response_data.get('offset'),
        'maxSize': response_data.get('maxSize'),
        'success': response_data.get('success', True),
        'error': response_data.get('error'),
        'message': response_data.get('message')
    }
    
    # None değerleri temizle
    return {k: v for k, v in parsed.items() if v is not None}


def validate_espocrm_data(data: Dict[str, Any], required_fields: Optional[List[str]] = None) -> bool:
    """
    EspoCRM veri formatını validate eder.
    
    Args:
        data: Validate edilecek veri
        required_fields: Zorunlu field'lar
        
    Returns:
        Validation başarılı mı
        
    Raises:
        ValueError: Validation hatası
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    # Required fields kontrolü
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
    
    # EspoCRM ID format kontrolü
    if 'id' in data and data['id']:
        id_value = str(data['id'])
        if not re.match(r'^[a-zA-Z0-9]{17}$', id_value):
            logger.warning(f"Invalid EspoCRM ID format: {id_value}")
    
    return True


# Default serializer instance
_default_serializer = DataSerializer()


def serialize(data: Any) -> str:
    """Default serializer ile veriyi serialize eder."""
    return _default_serializer.serialize(data)


def deserialize(json_str: str) -> Any:
    """Default serializer ile JSON'ı deserialize eder."""
    return _default_serializer.deserialize(json_str)


def to_espocrm_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """Veriyi EspoCRM formatına dönüştürür."""
    return _default_serializer.transform_for_espocrm(data)


def from_espocrm_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """EspoCRM verisini Python formatına dönüştürür."""
    return _default_serializer.transform_from_espocrm(data)


# Export edilecek sınıf ve fonksiyonlar
__all__ = [
    "EspoCRMJSONEncoder",
    "EspoCRMJSONDecoder",
    "DataSerializer",
    "build_query_string",
    "parse_espocrm_response",
    "validate_espocrm_data",
    "serialize",
    "deserialize",
    "to_espocrm_format",
    "from_espocrm_format",
]