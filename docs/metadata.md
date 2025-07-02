# EspoCRM Metadata Yönetimi

EspoCRM Python Client'ın metadata yönetimi sistemi, EspoCRM API'nin metadata özelliklerini tam olarak destekler. Bu sistem dynamic entity discovery, schema validation, field introspection ve intelligent caching özellikleri sağlar.

## İçindekiler

- [Temel Kullanım](#temel-kullanım)
- [Application Metadata](#application-metadata)
- [Entity Discovery](#entity-discovery)
- [Field Information](#field-information)
- [Relationship Mapping](#relationship-mapping)
- [Schema Validation](#schema-validation)
- [Metadata Caching](#metadata-caching)
- [API Capabilities](#api-capabilities)
- [Gelişmiş Özellikler](#gelişmiş-özellikler)

## Temel Kullanım

```python
from espocrm import EspoCRMClient, ClientConfig
from espocrm.auth import APIKeyAuth

# Client setup
config = ClientConfig(base_url="https://your-espocrm.com")
auth = APIKeyAuth(api_key="your-api-key")

with EspoCRMClient(config.base_url, auth, config) as client:
    # Application metadata'sını al
    app_metadata = client.get_application_metadata()
    
    # Entity türlerini keşfet
    entities = client.discover_entities()
    print(f"Available entities: {entities}")
    
    # Specific entity metadata
    account_meta = client.get_entity_metadata("Account")
    if account_meta:
        print(f"Account fields: {list(account_meta.fields.keys())}")
```

## Application Metadata

Application metadata, EspoCRM sisteminin tüm metadata bilgilerini içerir.

### Metadata Alma

```python
# Tüm metadata'yı al
app_metadata = client.get_application_metadata()

# Selective metadata alma
app_metadata = client.get_application_metadata(
    include_client_defs=True,
    include_scopes=True,
    include_fields=True
)

# Cache'i bypass et
app_metadata = client.get_application_metadata(force_refresh=True)
```

### Metadata Yapısı

```python
# Entity türlerini al
entity_types = app_metadata.get_entity_types()

# Specific entity metadata
account_meta = app_metadata.get_entity_metadata("Account")

# Entity var mı kontrol et
has_account = app_metadata.has_entity("Account")

# Entity field'ı al
name_field = app_metadata.get_entity_field("Account", "name")
```

## Entity Discovery

Mevcut entity türlerini dinamik olarak keşfetme.

### Entity Keşfi

```python
# Tüm entity'leri keşfet
entities = client.discover_entities()
print(f"Discovered entities: {entities}")

# Entity existence kontrolü
if client.entity_exists("Account"):
    print("Account entity exists")

# Cache'den entity listesi
entities = client.discover_entities(force_refresh=False)
```

### Entity Metadata

```python
# Specific entity metadata
account_meta = client.get_entity_metadata("Account")

if account_meta:
    # Field'ları al
    fields = account_meta.fields
    
    # İlişkileri al
    relationships = account_meta.links
    
    # Zorunlu field'ları al
    required_fields = account_meta.get_required_fields()
    
    # İlişki field'larını al
    relationship_fields = account_meta.get_relationship_fields()
```

## Field Information

Entity field'larının detaylı bilgilerini alma.

### Field Discovery

```python
# Tüm field'ları keşfet
fields = client.discover_entity_fields("Account")

for field_name, field_meta in fields.items():
    print(f"{field_name}: {field_meta.type.value}")
    
    if field_meta.is_required():
        print(f"  - Required field")
    
    if field_meta.is_enum_field():
        print(f"  - Options: {field_meta.options}")
```

### Field Type Filtering

```python
from espocrm.models.metadata import FieldType

# Sadece enum field'ları
enum_fields = client.discover_entity_fields(
    "Lead", 
    field_type=FieldType.ENUM
)

# Sadece ilişki field'ları
link_fields = client.discover_entity_fields(
    "Account", 
    field_type=FieldType.LINK
)
```

### Field Metadata

```python
# Specific field metadata
field_meta = client.get_entity_field_metadata("Account", "name")

if field_meta:
    print(f"Type: {field_meta.type}")
    print(f"Required: {field_meta.is_required()}")
    print(f"Max Length: {field_meta.max_length}")
    
    # Validation kuralları
    rules = field_meta.get_validation_rules()
    print(f"Validation rules: {rules}")
```

### Enum Options

```python
# Enum field seçenekleri
status_options = client.get_enum_options("Lead", "status")
if status_options:
    print(f"Lead status options: {status_options}")

# Field existence kontrolü
if client.field_exists("Account", "name"):
    print("Account.name field exists")
```

## Relationship Mapping

Entity ilişkilerini keşfetme ve mapping.

### Relationship Discovery

```python
# Tüm ilişkileri keşfet
relationships = client.discover_entity_relationships("Account")

for link_name, rel_meta in relationships.items():
    print(f"{link_name}: {rel_meta.type.value} -> {rel_meta.entity}")
```

### Relationship Type Filtering

```python
from espocrm.models.metadata import RelationshipType

# One-to-many ilişkileri
one_to_many = client.discover_entity_relationships(
    "Account",
    relationship_type=RelationshipType.ONE_TO_MANY
)

# Many-to-many ilişkileri
many_to_many = client.discover_entity_relationships(
    "Contact",
    relationship_type=RelationshipType.MANY_TO_MANY
)
```

### Relationship Metadata

```python
# Specific relationship metadata
rel_meta = client.get_entity_relationship_metadata("Account", "contacts")

if rel_meta:
    print(f"Type: {rel_meta.type}")
    print(f"Entity: {rel_meta.entity}")
    print(f"Foreign Key: {rel_meta.foreign_key}")
    
    # İlişki türü kontrolü
    if rel_meta.is_one_to_many():
        print("This is a one-to-many relationship")
```

## Schema Validation

Entity verilerini schema'ya göre doğrulama.

### Data Validation

```python
# Entity verilerini doğrula
data = {
    "name": "Test Company",
    "website": "https://test.com",
    "type": "Customer"
}

errors = client.validate_entity_data("Account", data)

if not errors:
    print("Data is valid")
else:
    print("Validation errors:")
    for field, field_errors in errors.items():
        print(f"  {field}: {field_errors}")
```

### Required Fields

```python
# Zorunlu field'ları al
required_fields = client.get_required_fields("Account")
print(f"Required fields: {required_fields}")

# Validation kuralları
rules = client.get_field_validation_rules("Account", "name")
print(f"Name field rules: {rules}")
```

### Custom Validation

```python
def validate_account_data(client, data):
    """Custom account data validation."""
    errors = {}
    
    # Schema validation
    schema_errors = client.validate_entity_data("Account", data)
    if schema_errors:
        errors.update(schema_errors)
    
    # Custom business rules
    if data.get("website") and not data["website"].startswith("https://"):
        errors["website"] = ["Website must use HTTPS"]
    
    return errors

# Kullanım
data = {"name": "Test", "website": "http://test.com"}
validation_errors = validate_account_data(client, data)
```

## Metadata Caching

Performance için intelligent caching sistemi.

### Cache Management

```python
# Cache'i warm up et
client.warm_metadata_cache()

# Specific entity'ler için
client.warm_metadata_cache(["Account", "Contact", "Lead"])

# Cache bilgileri
cache_info = client.get_metadata_cache_info()
print(f"Cache info: {cache_info}")

# Cache'i temizle
client.clear_metadata_cache()
```

### Cache Configuration

```python
# Custom cache TTL ile client oluştur
with EspoCRMClient(config.base_url, auth, config) as client:
    # Metadata client'ın cache TTL'ini ayarla
    client.metadata.cache.ttl_seconds = 7200  # 2 saat
```

### Cache Strategies

```python
# Cache warming strategy
def warm_essential_metadata(client):
    """Essential metadata'yı cache'e yükle."""
    essential_entities = ["Account", "Contact", "Lead", "Opportunity"]
    
    try:
        client.warm_metadata_cache(essential_entities)
        print("Essential metadata cached successfully")
    except Exception as e:
        print(f"Cache warming failed: {e}")

# Selective refresh
def refresh_entity_metadata(client, entity_type):
    """Specific entity metadata'sını refresh et."""
    client.get_entity_metadata(entity_type, force_refresh=True)
    print(f"{entity_type} metadata refreshed")
```

## API Capabilities

EspoCRM API'nin yeteneklerini tespit etme.

### Capability Detection

```python
# API capabilities'i tespit et
capabilities = client.detect_api_capabilities()

print(f"Entity count: {capabilities['entity_count']}")
print(f"Supported field types: {capabilities['supported_field_types']}")
print(f"Supported relationship types: {capabilities['supported_relationship_types']}")
```

### Feature Detection

```python
# Specific feature'ları kontrol et
def check_api_features(client):
    """API feature'larını kontrol et."""
    capabilities = client.detect_api_capabilities()
    
    features = {
        "has_attachments": "Attachment" in capabilities["entities"],
        "has_streams": "Note" in capabilities["entities"],
        "supports_enum_fields": "enum" in capabilities["supported_field_types"],
        "supports_many_to_many": "manyToMany" in capabilities["supported_relationship_types"]
    }
    
    return features

features = check_api_features(client)
print(f"API features: {features}")
```

## Gelişmiş Özellikler

### Specific Metadata Paths

```python
# Specific metadata path'den veri al
status_options = client.metadata.get_specific_metadata(
    "entityDefs.Lead.fields.status.options"
)

# Nested path
account_fields = client.metadata.get_specific_metadata(
    "entityDefs.Account.fields"
)
```

### Dynamic Entity Creation

```python
def create_dynamic_entity(client, entity_type, data):
    """Dynamic entity creation with validation."""
    # Önce entity'nin var olduğunu kontrol et
    if not client.entity_exists(entity_type):
        raise ValueError(f"Entity type '{entity_type}' does not exist")
    
    # Data validation
    errors = client.validate_entity_data(entity_type, data)
    if errors:
        raise ValueError(f"Validation errors: {errors}")
    
    # Entity'yi oluştur
    return client.create_entity(entity_type, data)
```

### Schema Introspection

```python
def introspect_entity_schema(client, entity_type):
    """Entity schema'sını detaylı analiz et."""
    entity_meta = client.get_entity_metadata(entity_type)
    if not entity_meta:
        return None
    
    schema = {
        "entity_type": entity_type,
        "field_count": len(entity_meta.fields),
        "relationship_count": len(entity_meta.links),
        "required_fields": entity_meta.get_required_fields(),
        "enum_fields": {},
        "relationship_fields": {},
        "field_types": {}
    }
    
    # Field analysis
    for field_name, field_meta in entity_meta.fields.items():
        schema["field_types"][field_name] = field_meta.type.value
        
        if field_meta.is_enum_field():
            schema["enum_fields"][field_name] = field_meta.options
        
        if field_meta.is_relationship_field():
            schema["relationship_fields"][field_name] = field_meta.entity
    
    return schema

# Kullanım
schema = introspect_entity_schema(client, "Account")
print(f"Account schema: {schema}")
```

### Metadata Comparison

```python
def compare_entity_schemas(client, entity1, entity2):
    """İki entity'nin schema'larını karşılaştır."""
    meta1 = client.get_entity_metadata(entity1)
    meta2 = client.get_entity_metadata(entity2)
    
    if not meta1 or not meta2:
        return None
    
    comparison = {
        "common_fields": set(meta1.fields.keys()) & set(meta2.fields.keys()),
        "unique_to_first": set(meta1.fields.keys()) - set(meta2.fields.keys()),
        "unique_to_second": set(meta2.fields.keys()) - set(meta1.fields.keys()),
        "common_relationships": set(meta1.links.keys()) & set(meta2.links.keys())
    }
    
    return comparison

# Kullanım
comparison = compare_entity_schemas(client, "Account", "Contact")
print(f"Schema comparison: {comparison}")
```

## Best Practices

### 1. Cache Management

```python
# Application başlangıcında cache'i warm up et
def initialize_metadata_cache(client):
    """Metadata cache'ini başlat."""
    try:
        # Essential entity'leri cache'e yükle
        essential_entities = ["Account", "Contact", "Lead", "Opportunity"]
        client.warm_metadata_cache(essential_entities)
        
        # API capabilities'i cache'e yükle
        client.detect_api_capabilities()
        
        print("Metadata cache initialized successfully")
    except Exception as e:
        print(f"Cache initialization failed: {e}")
```

### 2. Error Handling

```python
def safe_metadata_operation(client, operation, *args, **kwargs):
    """Safe metadata operation with error handling."""
    try:
        return operation(*args, **kwargs)
    except Exception as e:
        print(f"Metadata operation failed: {e}")
        
        # Fallback: cache'i temizle ve tekrar dene
        try:
            client.clear_metadata_cache()
            return operation(*args, force_refresh=True, **kwargs)
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            raise
```

### 3. Performance Optimization

```python
def optimize_metadata_usage(client):
    """Metadata kullanımını optimize et."""
    # 1. Batch operations
    entities_to_check = ["Account", "Contact", "Lead"]
    
    # Tek seferde tüm metadata'yı al
    client.warm_metadata_cache(entities_to_check)
    
    # 2. Cache'den kullan
    for entity_type in entities_to_check:
        # force_refresh=False (default) - cache'den al
        metadata = client.get_entity_metadata(entity_type)
        # Process metadata...
    
    # 3. Periodic cache refresh
    import time
    last_refresh = time.time()
    refresh_interval = 3600  # 1 saat
    
    if time.time() - last_refresh > refresh_interval:
        client.get_application_metadata(force_refresh=True)
        last_refresh = time.time()
```

## Hata Yönetimi

Metadata operasyonlarında karşılaşılabilecek hatalar:

```python
from espocrm.exceptions import EspoCRMError, EspoCRMValidationError

try:
    metadata = client.get_application_metadata()
except EspoCRMError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

# Validation hataları
try:
    errors = client.validate_entity_data("Account", invalid_data)
except EspoCRMValidationError as e:
    print(f"Validation error: {e}")
```

## Sonuç

EspoCRM Metadata sistemi, dynamic ve type-safe bir şekilde EspoCRM API'nin metadata özelliklerini kullanmanızı sağlar. Intelligent caching, schema validation ve comprehensive introspection özellikleri ile robust uygulamalar geliştirebilirsiniz.

Daha fazla örnek için `examples/metadata_example.py` dosyasına bakabilirsiniz.