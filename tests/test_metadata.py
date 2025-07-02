"""
EspoCRM Metadata Client Test

Bu dosya metadata sisteminin temel fonksiyonalitesini test eder.
"""

from unittest.mock import Mock, patch
from datetime import datetime

from espocrm.models.metadata import (
    FieldType,
    RelationshipType,
    FieldMetadata,
    RelationshipMetadata,
    EntityMetadata,
    ApplicationMetadata,
    MetadataRequest
)
from espocrm.clients.metadata import MetadataClient, MetadataCache


class TestMetadataModels:
    """Metadata model testleri."""
    
    def test_field_metadata_creation(self):
        """FieldMetadata oluşturma testi."""
        field = FieldMetadata(
            type=FieldType.VARCHAR,
            required=True,
            max_length=255
        )
        
        assert field.type == FieldType.VARCHAR
        assert field.is_required() == True
        assert field.max_length == 255
        assert field.is_relationship_field() == False
        assert field.is_enum_field() == False
    
    def test_enum_field_metadata(self):
        """Enum field metadata testi."""
        field = FieldMetadata(
            type=FieldType.ENUM,
            options=["New", "Assigned", "In Process", "Completed"]
        )
        
        assert field.is_enum_field() == True
        assert field.options == ["New", "Assigned", "In Process", "Completed"]
    
    def test_relationship_metadata_creation(self):
        """RelationshipMetadata oluşturma testi."""
        rel = RelationshipMetadata(
            type=RelationshipType.ONE_TO_MANY,
            entity="Contact",
            foreign="accountId"
        )
        
        assert rel.type == RelationshipType.ONE_TO_MANY
        assert rel.entity == "Contact"
        assert rel.is_one_to_many() == True
        assert rel.is_many_to_many() == False
    
    def test_entity_metadata_creation(self):
        """EntityMetadata oluşturma testi."""
        fields = {
            "name": FieldMetadata(type=FieldType.VARCHAR, required=True),
            "status": FieldMetadata(type=FieldType.ENUM, options=["New", "Active"])
        }
        
        links = {
            "contacts": RelationshipMetadata(
                type=RelationshipType.ONE_TO_MANY,
                entity="Contact"
            )
        }
        
        entity = EntityMetadata(fields=fields, links=links)
        
        assert len(entity.fields) == 2
        assert len(entity.links) == 1
        assert entity.has_field("name") == True
        assert entity.has_field("nonexistent") == False
        assert entity.has_link("contacts") == True
        
        required_fields = entity.get_required_fields()
        assert "name" in required_fields
        assert "status" not in required_fields
    
    def test_application_metadata_creation(self):
        """ApplicationMetadata oluşturma testi."""
        entity_defs = {
            "Account": EntityMetadata(
                fields={
                    "name": FieldMetadata(type=FieldType.VARCHAR, required=True)
                }
            )
        }
        
        app_meta = ApplicationMetadata(entity_defs=entity_defs)
        
        assert len(app_meta.entity_defs) == 1
        assert app_meta.has_entity("Account") == True
        assert app_meta.has_entity("Contact") == False
        
        entity_types = app_meta.get_entity_types()
        assert "Account" in entity_types
    
    def test_metadata_request_creation(self):
        """MetadataRequest oluşturma testi."""
        request = MetadataRequest(
            key="entityDefs.Lead.fields.status.options",
            include_client_defs=False
        )
        
        params = request.to_query_params()
        assert params["key"] == "entityDefs.Lead.fields.status.options"
        assert params["includeClientDefs"] == "false"


class TestMetadataCache:
    """Metadata cache testleri."""
    
    def test_cache_basic_operations(self):
        """Cache temel operasyonları testi."""
        cache = MetadataCache(ttl_seconds=60)
        
        # Set ve get
        cache.set("test_key", {"data": "test_value"})
        result = cache.get("test_key")
        
        assert result == {"data": "test_value"}
    
    def test_cache_expiration(self):
        """Cache expiration testi."""
        cache = MetadataCache(ttl_seconds=0)  # Hemen expire olsun
        
        cache.set("test_key", {"data": "test_value"})
        
        # Biraz bekle (expiration için)
        import time
        time.sleep(0.1)
        
        result = cache.get("test_key")
        assert result is None  # Expire olmuş olmalı
    
    def test_cache_clear(self):
        """Cache clear testi."""
        cache = MetadataCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_info(self):
        """Cache info testi."""
        cache = MetadataCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        info = cache.get_cache_info()
        
        assert info["total_keys"] == 2
        assert info["active_keys"] == 2
        assert info["expired_keys"] == 0


class TestMetadataClient:
    """Metadata client testleri."""
    
    def setup_mock_client(self):
        """Mock main client."""
        client = Mock()
        client.get.return_value = {
            "entityDefs": {
                "Account": {
                    "fields": {
                        "name": {
                            "type": "varchar",
                            "required": True,
                            "maxLength": 255
                        }
                    },
                    "links": {
                        "contacts": {
                            "type": "oneToMany",
                            "entity": "Contact"
                        }
                    }
                }
            }
        }
        return client
    
    def setup_metadata_client(self):
        """Metadata client instance."""
        mock_client = self.setup_mock_client()
        return MetadataClient(mock_client), mock_client
    
    def test_get_application_metadata(self):
        """Application metadata alma testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        app_metadata = metadata_client.get_application_metadata()
        
        assert isinstance(app_metadata, ApplicationMetadata)
        assert app_metadata.has_entity("Account") == True
        
        # API call kontrolü
        mock_client.get.assert_called_once()
    
    def test_get_entity_metadata(self):
        """Entity metadata alma testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        entity_meta = metadata_client.get_entity_metadata("Account")
        
        assert isinstance(entity_meta, EntityMetadata)
        assert entity_meta.has_field("name") == True
        assert entity_meta.has_link("contacts") == True
    
    def test_discover_entities(self):
        """Entity discovery testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        entities = metadata_client.discover_entities()
        
        assert "Account" in entities
        assert isinstance(entities, list)
    
    def test_discover_entity_fields(self):
        """Entity field discovery testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        fields = metadata_client.discover_entity_fields("Account")
        
        assert "name" in fields
        assert isinstance(fields["name"], FieldMetadata)
        assert fields["name"].type == FieldType.VARCHAR
    
    def test_discover_entity_relationships(self):
        """Entity relationship discovery testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        relationships = metadata_client.discover_entity_relationships("Account")
        
        assert "contacts" in relationships
        assert isinstance(relationships["contacts"], RelationshipMetadata)
        assert relationships["contacts"].type == RelationshipType.ONE_TO_MANY
    
    def test_validate_entity_data(self):
        """Entity data validation testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        
        # Geçerli veri
        valid_data = {"name": "Test Company"}
        errors = metadata_client.validate_entity_data("Account", valid_data)
        assert len(errors) == 0
        
        # Geçersiz veri (required field eksik)
        invalid_data = {}
        errors = metadata_client.validate_entity_data("Account", invalid_data)
        assert len(errors) > 0
    
    def test_cache_operations(self):
        """Cache operasyonları testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        
        # İlk call - API'den gelecek
        metadata_client.get_application_metadata()
        
        # İkinci call - cache'den gelecek
        metadata_client.get_application_metadata()
        
        # API sadece bir kez çağrılmalı
        assert mock_client.get.call_count == 1
        
        # Cache info
        cache_info = metadata_client.get_cache_info()
        assert "total_keys" in cache_info
        
        # Cache clear
        metadata_client.clear_cache()
        cache_info = metadata_client.get_cache_info()
        assert cache_info["total_keys"] == 0
    
    def test_entity_exists(self):
        """Entity existence kontrolü testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        assert metadata_client.entity_exists("Account") == True
        assert metadata_client.entity_exists("NonExistent") == False
    
    def test_field_exists(self):
        """Field existence kontrolü testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        assert metadata_client.field_exists("Account", "name") == True
        assert metadata_client.field_exists("Account", "nonexistent") == False
    
    def test_relationship_exists(self):
        """Relationship existence kontrolü testi."""
        metadata_client, mock_client = self.setup_metadata_client()
        assert metadata_client.relationship_exists("Account", "contacts") == True
        assert metadata_client.relationship_exists("Account", "nonexistent") == False


class TestMetadataValidation:
    """Metadata validation testleri."""
    
    def test_field_validation_rules(self):
        """Field validation kuralları testi."""
        field = FieldMetadata(
            type=FieldType.VARCHAR,
            required=True,
            max_length=100,
            min=5,
            max=200
        )
        
        rules = field.get_validation_rules()
        
        assert rules["required"] == True
        assert rules["max_length"] == 100
        assert rules["min"] == 5
        assert rules["max"] == 200
    
    def test_enum_validation_rules(self):
        """Enum validation kuralları testi."""
        field = FieldMetadata(
            type=FieldType.ENUM,
            options=["Option1", "Option2", "Option3"]
        )
        
        rules = field.get_validation_rules()
        
        assert rules["choices"] == ["Option1", "Option2", "Option3"]
    
    def test_entity_data_validation(self):
        """Entity data validation testi."""
        # Entity metadata oluştur
        fields = {
            "name": FieldMetadata(
                type=FieldType.VARCHAR,
                required=True,
                max_length=50
            ),
            "status": FieldMetadata(
                type=FieldType.ENUM,
                options=["Active", "Inactive"]
            )
        }
        
        entity_meta = EntityMetadata(fields=fields)
        app_meta = ApplicationMetadata(entity_defs={"Test": entity_meta})
        
        # Geçerli veri
        valid_data = {
            "name": "Test Name",
            "status": "Active"
        }
        errors = app_meta.validate_entity_data("Test", valid_data)
        assert len(errors) == 0
        
        # Geçersiz veri - required field eksik
        invalid_data1 = {
            "status": "Active"
        }
        errors = app_meta.validate_entity_data("Test", invalid_data1)
        assert "required" in errors
        
        # Geçersiz veri - enum değeri yanlış
        invalid_data2 = {
            "name": "Test Name",
            "status": "InvalidStatus"
        }
        errors = app_meta.validate_entity_data("Test", invalid_data2)
        assert "status" in errors


if __name__ == "__main__":
    # Basit test runner
    import sys
    
    test_classes = [
        TestMetadataModels,
        TestMetadataCache,
        TestMetadataClient,
        TestMetadataValidation
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n=== {test_class.__name__} ===")
        
        instance = test_class()
        methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for method_name in methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                
                # Fixture'ları manuel olarak handle et
                if hasattr(method, '__code__') and 'mock_client' in method.__code__.co_varnames:
                    mock_client = Mock()
                    mock_client.get.return_value = {
                        "entityDefs": {
                            "Account": {
                                "fields": {
                                    "name": {
                                        "type": "varchar",
                                        "required": True,
                                        "maxLength": 255
                                    }
                                },
                                "links": {
                                    "contacts": {
                                        "type": "oneToMany",
                                        "entity": "Contact"
                                    }
                                }
                            }
                        }
                    }
                    
                    if 'metadata_client' in method.__code__.co_varnames:
                        metadata_client = MetadataClient(mock_client)
                        method(metadata_client, mock_client)
                    else:
                        method(mock_client)
                else:
                    method()
                
                print(f"  ✓ {method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ✗ {method_name}: {e}")
    
    print(f"\n=== Test Sonuçları ===")
    print(f"Toplam: {total_tests}")
    print(f"Başarılı: {passed_tests}")
    print(f"Başarısız: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("✓ Tüm testler başarılı!")
        sys.exit(0)
    else:
        print("✗ Bazı testler başarısız!")
        sys.exit(1)