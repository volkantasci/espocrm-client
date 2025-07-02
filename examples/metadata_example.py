"""
EspoCRM Metadata Client Örneği

Bu örnek EspoCRM metadata sisteminin nasıl kullanılacağını gösterir:
- Application metadata alma
- Entity discovery
- Field information
- Relationship mapping
- Schema validation
- Metadata caching
"""

import asyncio
from typing import Dict, Any

from espocrm import EspoCRMClient, ClientConfig
from espocrm.auth import APIKeyAuth
from espocrm.models.metadata import FieldType, RelationshipType


def basic_metadata_operations():
    """Temel metadata operasyonları örneği."""
    print("=== Temel Metadata Operasyonları ===")
    
    # Client setup
    config = ClientConfig(
        base_url="https://your-espocrm.com",
        timeout=30,
        debug=True
    )
    auth = APIKeyAuth(api_key="your-api-key")
    
    with EspoCRMClient(config.base_url, auth, config) as client:
        try:
            # Application metadata'sını al
            print("\n1. Application Metadata Alma:")
            app_metadata = client.get_application_metadata()
            print(f"Toplam entity sayısı: {len(app_metadata.get_entity_types())}")
            print(f"Entity türleri: {app_metadata.get_entity_types()[:5]}...")  # İlk 5'i göster
            
            # Entity discovery
            print("\n2. Entity Discovery:")
            entities = client.discover_entities()
            print(f"Keşfedilen entity'ler: {entities}")
            
            # Specific entity metadata
            print("\n3. Account Entity Metadata:")
            account_meta = client.get_entity_metadata("Account")
            if account_meta:
                print(f"Account field'ları: {list(account_meta.fields.keys())[:10]}...")  # İlk 10'u göster
                print(f"Account ilişkileri: {list(account_meta.links.keys())}")
            
        except Exception as e:
            print(f"Hata: {e}")


def field_discovery_example():
    """Field discovery örneği."""
    print("\n=== Field Discovery Örneği ===")
    
    config = ClientConfig(base_url="https://your-espocrm.com")
    auth = APIKeyAuth(api_key="your-api-key")
    
    with EspoCRMClient(config.base_url, auth, config) as client:
        try:
            # Tüm field'ları keşfet
            print("\n1. Account Field'larını Keşfetme:")
            fields = client.discover_entity_fields("Account")
            
            for field_name, field_meta in list(fields.items())[:5]:  # İlk 5'i göster
                print(f"  - {field_name}: {field_meta.type.value}")
                if field_meta.is_required():
                    print(f"    (Zorunlu)")
                if field_meta.is_enum_field() and field_meta.options:
                    print(f"    Seçenekler: {field_meta.options}")
            
            # Enum field'ları keşfet
            print("\n2. Enum Field'larını Keşfetme:")
            enum_fields = client.discover_entity_fields("Lead", field_type=FieldType.ENUM)
            
            for field_name, field_meta in enum_fields.items():
                print(f"  - {field_name}: {field_meta.options}")
            
            # Specific field options
            print("\n3. Lead Status Seçenekleri:")
            status_options = client.get_enum_options("Lead", "status")
            if status_options:
                print(f"  Status seçenekleri: {status_options}")
            
        except Exception as e:
            print(f"Hata: {e}")


def relationship_discovery_example():
    """Relationship discovery örneği."""
    print("\n=== Relationship Discovery Örneği ===")
    
    config = ClientConfig(base_url="https://your-espocrm.com")
    auth = APIKeyAuth(api_key="your-api-key")
    
    with EspoCRMClient(config.base_url, auth, config) as client:
        try:
            # Tüm ilişkileri keşfet
            print("\n1. Account İlişkilerini Keşfetme:")
            relationships = client.discover_entity_relationships("Account")
            
            for link_name, rel_meta in list(relationships.items())[:5]:  # İlk 5'i göster
                print(f"  - {link_name}: {rel_meta.type.value} -> {rel_meta.entity}")
            
            # One-to-many ilişkileri keşfet
            print("\n2. One-to-Many İlişkileri:")
            one_to_many = client.discover_entity_relationships(
                "Account", 
                relationship_type=RelationshipType.ONE_TO_MANY
            )
            
            for link_name, rel_meta in one_to_many.items():
                print(f"  - {link_name} -> {rel_meta.entity}")
            
        except Exception as e:
            print(f"Hata: {e}")


def schema_validation_example():
    """Schema validation örneği."""
    print("\n=== Schema Validation Örneği ===")
    
    config = ClientConfig(base_url="https://your-espocrm.com")
    auth = APIKeyAuth(api_key="your-api-key")
    
    with EspoCRMClient(config.base_url, auth, config) as client:
        try:
            # Geçerli veri
            print("\n1. Geçerli Veri Validation:")
            valid_data = {
                "name": "Test Company",
                "website": "https://test.com",
                "type": "Customer"
            }
            
            errors = client.validate_entity_data("Account", valid_data)
            if not errors:
                print("  ✓ Veri geçerli")
            else:
                print(f"  ✗ Hatalar: {errors}")
            
            # Geçersiz veri
            print("\n2. Geçersiz Veri Validation:")
            invalid_data = {
                "name": "",  # Boş name (muhtemelen zorunlu)
                "website": "invalid-url",  # Geçersiz URL
                "nonexistent_field": "value"  # Var olmayan field
            }
            
            errors = client.validate_entity_data("Account", invalid_data)
            if errors:
                print("  ✗ Validation hataları:")
                for field, field_errors in errors.items():
                    print(f"    {field}: {field_errors}")
            
            # Required field'ları kontrol et
            print("\n3. Zorunlu Field'lar:")
            required_fields = client.get_required_fields("Account")
            print(f"  Zorunlu field'lar: {required_fields}")
            
        except Exception as e:
            print(f"Hata: {e}")


def caching_example():
    """Metadata caching örneği."""
    print("\n=== Metadata Caching Örneği ===")
    
    config = ClientConfig(base_url="https://your-espocrm.com")
    auth = APIKeyAuth(api_key="your-api-key")
    
    with EspoCRMClient(config.base_url, auth, config) as client:
        try:
            # Cache'i warm up et
            print("\n1. Cache Warming:")
            client.warm_metadata_cache(["Account", "Contact", "Lead"])
            print("  ✓ Cache warmed up")
            
            # Cache bilgilerini al
            print("\n2. Cache Bilgileri:")
            cache_info = client.get_metadata_cache_info()
            print(f"  Toplam key'ler: {cache_info['total_keys']}")
            print(f"  Aktif key'ler: {cache_info['active_keys']}")
            print(f"  TTL: {cache_info['ttl_seconds']} saniye")
            
            # Cache'den veri al (hızlı)
            print("\n3. Cache'den Veri Alma:")
            import time
            
            start_time = time.time()
            entities = client.discover_entities()  # Cache'den gelecek
            end_time = time.time()
            
            print(f"  Cache'den alma süresi: {(end_time - start_time) * 1000:.2f}ms")
            print(f"  Entity sayısı: {len(entities)}")
            
            # Cache'i temizle
            print("\n4. Cache Temizleme:")
            client.clear_metadata_cache()
            print("  ✓ Cache temizlendi")
            
        except Exception as e:
            print(f"Hata: {e}")


def api_capabilities_example():
    """API capabilities detection örneği."""
    print("\n=== API Capabilities Detection ===")
    
    config = ClientConfig(base_url="https://your-espocrm.com")
    auth = APIKeyAuth(api_key="your-api-key")
    
    with EspoCRMClient(config.base_url, auth, config) as client:
        try:
            # API capabilities'i tespit et
            capabilities = client.detect_api_capabilities()
            
            print(f"Entity sayısı: {capabilities['entity_count']}")
            print(f"Desteklenen field türleri: {len(capabilities['supported_field_types'])}")
            print(f"Desteklenen ilişki türleri: {len(capabilities['supported_relationship_types'])}")
            
            print(f"\nField türleri: {capabilities['supported_field_types'][:10]}...")  # İlk 10'u göster
            print(f"İlişki türleri: {capabilities['supported_relationship_types']}")
            
            # Entity existence kontrolü
            print(f"\nAccount entity var mı: {client.entity_exists('Account')}")
            print(f"NonExistent entity var mı: {client.entity_exists('NonExistent')}")
            
            # Field existence kontrolü
            print(f"Account.name field var mı: {client.field_exists('Account', 'name')}")
            print(f"Account.nonexistent field var mı: {client.field_exists('Account', 'nonexistent')}")
            
        except Exception as e:
            print(f"Hata: {e}")


def specific_metadata_example():
    """Specific metadata path örneği."""
    print("\n=== Specific Metadata Path Örneği ===")
    
    config = ClientConfig(base_url="https://your-espocrm.com")
    auth = APIKeyAuth(api_key="your-api-key")
    
    with EspoCRMClient(config.base_url, auth, config) as client:
        try:
            # Specific path'den metadata al
            print("\n1. Lead Status Options:")
            status_options = client.metadata.get_specific_metadata(
                "entityDefs.Lead.fields.status.options"
            )
            print(f"  Status seçenekleri: {status_options}")
            
            print("\n2. Account Fields:")
            account_fields = client.metadata.get_specific_metadata(
                "entityDefs.Account.fields"
            )
            if isinstance(account_fields, dict):
                print(f"  Field sayısı: {len(account_fields)}")
                print(f"  Field'lar: {list(account_fields.keys())[:5]}...")  # İlk 5'i göster
            
        except Exception as e:
            print(f"Hata: {e}")


def main():
    """Ana fonksiyon - tüm örnekleri çalıştırır."""
    print("EspoCRM Metadata Client Örnekleri")
    print("=" * 50)
    
    try:
        basic_metadata_operations()
        field_discovery_example()
        relationship_discovery_example()
        schema_validation_example()
        caching_example()
        api_capabilities_example()
        specific_metadata_example()
        
    except KeyboardInterrupt:
        print("\n\nÖrnekler kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"\nGenel hata: {e}")
    
    print("\n" + "=" * 50)
    print("Örnekler tamamlandı!")


if __name__ == "__main__":
    main()