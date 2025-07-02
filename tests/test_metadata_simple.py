"""
EspoCRM Metadata Client Basit Test

Bu dosya metadata sisteminin temel fonksiyonalitesini test eder.
"""

from unittest.mock import Mock
import sys
import os

# Proje root'unu path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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


def test_field_metadata():
    """FieldMetadata testi."""
    print("Testing FieldMetadata...")
    
    # Varchar field
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
    
    # Enum field
    enum_field = FieldMetadata(
        type=FieldType.ENUM,
        options=["New", "Assigned", "Completed"]
    )
    
    assert enum_field.is_enum_field() == True
    assert enum_field.options == ["New", "Assigned", "Completed"]
    
    print("✓ FieldMetadata tests passed")


def test_relationship_metadata():
    """RelationshipMetadata testi."""
    print("Testing RelationshipMetadata...")
    
    rel = RelationshipMetadata(
        type=RelationshipType.ONE_TO_MANY,
        entity="Contact",
        foreign="accountId"
    )
    
    assert rel.type == RelationshipType.ONE_TO_MANY
    assert rel.entity == "Contact"
    assert rel.is_one_to_many() == True
    assert rel.is_many_to_many() == False
    
    print("✓ RelationshipMetadata tests passed")


def test_entity_metadata():
    """EntityMetadata testi."""
    print("Testing EntityMetadata...")
    
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
    
    print("✓ EntityMetadata tests passed")


def test_application_metadata():
    """ApplicationMetadata testi."""
    print("Testing ApplicationMetadata...")
    
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
    
    print("✓ ApplicationMetadata tests passed")


def test_metadata_request():
    """MetadataRequest testi."""
    print("Testing MetadataRequest...")
    
    request = MetadataRequest(
        key="entityDefs.Lead.fields.status.options",
        include_client_defs=False
    )
    
    params = request.to_query_params()
    assert params["key"] == "entityDefs.Lead.fields.status.options"
    assert params["includeClientDefs"] == "false"
    
    print("✓ MetadataRequest tests passed")


def test_metadata_cache():
    """MetadataCache testi."""
    print("Testing MetadataCache...")
    
    cache = MetadataCache(ttl_seconds=60)
    
    # Set ve get
    cache.set("test_key", {"data": "test_value"})
    result = cache.get("test_key")
    
    assert result == {"data": "test_value"}
    
    # Cache info
    info = cache.get_cache_info()
    assert info["total_keys"] == 1
    assert info["active_keys"] == 1
    
    # Clear
    cache.clear()
    assert cache.get("test_key") is None
    
    print("✓ MetadataCache tests passed")


def test_metadata_client():
    """MetadataClient testi."""
    print("Testing MetadataClient...")
    
    # Mock client setup
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
    
    metadata_client = MetadataClient(mock_client)
    
    # Application metadata
    app_metadata = metadata_client.get_application_metadata()
    assert isinstance(app_metadata, ApplicationMetadata)
    assert app_metadata.has_entity("Account") == True
    
    # Entity metadata
    entity_meta = metadata_client.get_entity_metadata("Account")
    assert isinstance(entity_meta, EntityMetadata)
    assert entity_meta.has_field("name") == True
    assert entity_meta.has_link("contacts") == True
    
    # Entity discovery
    entities = metadata_client.discover_entities()
    assert "Account" in entities
    assert isinstance(entities, list)
    
    # Field discovery
    fields = metadata_client.discover_entity_fields("Account")
    assert "name" in fields
    assert isinstance(fields["name"], FieldMetadata)
    assert fields["name"].type == FieldType.VARCHAR
    
    # Relationship discovery
    relationships = metadata_client.discover_entity_relationships("Account")
    assert "contacts" in relationships
    assert isinstance(relationships["contacts"], RelationshipMetadata)
    assert relationships["contacts"].type == RelationshipType.ONE_TO_MANY
    
    # Existence checks
    assert metadata_client.entity_exists("Account") == True
    assert metadata_client.entity_exists("NonExistent") == False
    assert metadata_client.field_exists("Account", "name") == True
    assert metadata_client.field_exists("Account", "nonexistent") == False
    assert metadata_client.relationship_exists("Account", "contacts") == True
    assert metadata_client.relationship_exists("Account", "nonexistent") == False
    
    print("✓ MetadataClient tests passed")


def test_validation():
    """Validation testi."""
    print("Testing validation...")
    
    # Field validation rules
    field = FieldMetadata(
        type=FieldType.VARCHAR,
        required=True,
        max_length=100
    )
    
    rules = field.get_validation_rules()
    assert rules["required"] == True
    assert rules["max_length"] == 100
    
    # Entity data validation
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
    invalid_data = {
        "status": "Active"
    }
    errors = app_meta.validate_entity_data("Test", invalid_data)
    assert len(errors) > 0
    assert "required" in errors
    
    print("✓ Validation tests passed")


def main():
    """Ana test fonksiyonu."""
    print("EspoCRM Metadata System Tests")
    print("=" * 40)
    
    tests = [
        test_field_metadata,
        test_relationship_metadata,
        test_entity_metadata,
        test_application_metadata,
        test_metadata_request,
        test_metadata_cache,
        test_metadata_client,
        test_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)