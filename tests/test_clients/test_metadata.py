"""
EspoCRM Metadata Client Test Module

Metadata operasyonları için kapsamlı testler.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import responses

from espocrm.clients.metadata import MetadataClient, MetadataCache
from espocrm.models.metadata import (
    FieldType,
    RelationshipType,
    FieldMetadata,
    RelationshipMetadata,
    EntityMetadata,
    ApplicationMetadata,
    MetadataRequest
)
from espocrm.exceptions import (
    EspoCRMError,
    EntityNotFoundError,
    ValidationError,
    MetadataError
)


@pytest.mark.unit
@pytest.mark.metadata
class TestMetadataClient:
    """Metadata Client temel testleri."""
    
    def test_metadata_client_initialization(self, mock_client):
        """Metadata client initialization testi."""
        meta_client = MetadataClient(mock_client)
        
        assert meta_client.client == mock_client
        assert meta_client.base_url == mock_client.base_url
        assert meta_client.api_version == mock_client.api_version
        assert isinstance(meta_client.cache, MetadataCache)
    
    def test_get_application_metadata_success(self, mock_client, mock_metadata):
        """Application metadata alma başarı testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {
                    "fields": {
                        "name": {
                            "type": "varchar",
                            "required": True,
                            "maxLength": 255
                        },
                        "type": {
                            "type": "enum",
                            "options": ["Customer", "Investor", "Partner"]
                        }
                    },
                    "links": {
                        "contacts": {
                            "type": "oneToMany",
                            "entity": "Contact",
                            "foreign": "account"
                        }
                    }
                }
            },
            "clientDefs": {
                "Account": {
                    "color": "#3498db",
                    "iconClass": "fas fa-building"
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.get_application_metadata()
        
        # Assertions
        assert isinstance(result, ApplicationMetadata)
        assert result.has_entity("Account")
        assert len(result.entity_defs) == 1
        
        # API call verification
        mock_client.get.assert_called_once_with("Metadata")
    
    def test_get_entity_metadata_success(self, mock_client):
        """Entity metadata alma başarı testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Contact": {
                    "fields": {
                        "firstName": {
                            "type": "varchar",
                            "maxLength": 100
                        },
                        "lastName": {
                            "type": "varchar",
                            "required": True,
                            "maxLength": 100
                        },
                        "emailAddress": {
                            "type": "email"
                        }
                    },
                    "links": {
                        "account": {
                            "type": "belongsTo",
                            "entity": "Account"
                        }
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.get_entity_metadata("Contact")
        
        # Assertions
        assert isinstance(result, EntityMetadata)
        assert result.has_field("firstName")
        assert result.has_field("lastName")
        assert result.has_link("account")
        
        # Required fields check
        required_fields = result.get_required_fields()
        assert "lastName" in required_fields
        assert "firstName" not in required_fields
    
    def test_get_field_metadata_success(self, mock_client):
        """Field metadata alma başarı testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {
                    "fields": {
                        "name": {
                            "type": "varchar",
                            "required": True,
                            "maxLength": 255,
                            "trim": True
                        }
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.get_field_metadata("Account", "name")
        
        # Assertions
        assert isinstance(result, FieldMetadata)
        assert result.type == FieldType.VARCHAR
        assert result.is_required()
        assert result.max_length == 255
    
    def test_get_relationship_metadata_success(self, mock_client):
        """Relationship metadata alma başarı testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {
                    "links": {
                        "contacts": {
                            "type": "oneToMany",
                            "entity": "Contact",
                            "foreign": "account",
                            "foreignKey": "accountId"
                        }
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.get_relationship_metadata("Account", "contacts")
        
        # Assertions
        assert isinstance(result, RelationshipMetadata)
        assert result.type == RelationshipType.ONE_TO_MANY
        assert result.entity == "Contact"
        assert result.foreign == "account"
    
    def test_discover_entities_success(self, mock_client):
        """Entity discovery başarı testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {"fields": {}},
                "Contact": {"fields": {}},
                "Lead": {"fields": {}},
                "Opportunity": {"fields": {}}
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.discover_entities()
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 4
        assert "Account" in result
        assert "Contact" in result
        assert "Lead" in result
        assert "Opportunity" in result
    
    def test_discover_entity_fields_success(self, mock_client):
        """Entity fields discovery başarı testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {
                    "fields": {
                        "name": {"type": "varchar", "required": True},
                        "type": {"type": "enum", "options": ["Customer", "Partner"]},
                        "industry": {"type": "enum", "options": ["Technology", "Healthcare"]},
                        "website": {"type": "url"},
                        "phoneNumber": {"type": "phone"}
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.discover_entity_fields("Account")
        
        # Assertions
        assert isinstance(result, dict)
        assert len(result) == 5
        assert "name" in result
        assert isinstance(result["name"], FieldMetadata)
        assert result["name"].type == FieldType.VARCHAR
        assert result["name"].is_required()
    
    def test_discover_entity_relationships_success(self, mock_client):
        """Entity relationships discovery başarı testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {
                    "links": {
                        "contacts": {
                            "type": "oneToMany",
                            "entity": "Contact"
                        },
                        "opportunities": {
                            "type": "oneToMany", 
                            "entity": "Opportunity"
                        },
                        "parent": {
                            "type": "belongsTo",
                            "entity": "Account"
                        }
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.discover_entity_relationships("Account")
        
        # Assertions
        assert isinstance(result, dict)
        assert len(result) == 3
        assert "contacts" in result
        assert isinstance(result["contacts"], RelationshipMetadata)
        assert result["contacts"].type == RelationshipType.ONE_TO_MANY
    
    def test_validate_entity_data_success(self, mock_client):
        """Entity data validation başarı testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {
                    "fields": {
                        "name": {
                            "type": "varchar",
                            "required": True,
                            "maxLength": 255
                        },
                        "type": {
                            "type": "enum",
                            "options": ["Customer", "Partner", "Investor"]
                        },
                        "industry": {
                            "type": "enum",
                            "options": ["Technology", "Healthcare", "Finance"]
                        }
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        # Valid data
        valid_data = {
            "name": "Test Company",
            "type": "Customer",
            "industry": "Technology"
        }
        
        errors = meta_client.validate_entity_data("Account", valid_data)
        
        # Assertions
        assert isinstance(errors, dict)
        assert len(errors) == 0  # No validation errors
    
    def test_validate_entity_data_with_errors(self, mock_client):
        """Entity data validation error testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {
                    "fields": {
                        "name": {
                            "type": "varchar",
                            "required": True,
                            "maxLength": 50
                        },
                        "type": {
                            "type": "enum",
                            "options": ["Customer", "Partner"]
                        }
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        # Invalid data
        invalid_data = {
            "name": "A" * 100,  # Too long
            "type": "InvalidType"  # Not in enum options
        }
        
        errors = meta_client.validate_entity_data("Account", invalid_data)
        
        # Assertions
        assert isinstance(errors, dict)
        assert len(errors) > 0
        assert "name" in errors  # Max length violation
        assert "type" in errors  # Invalid enum value
    
    def test_entity_exists_check(self, mock_client):
        """Entity existence check testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {"fields": {}},
                "Contact": {"fields": {}}
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        # Assertions
        assert meta_client.entity_exists("Account") is True
        assert meta_client.entity_exists("Contact") is True
        assert meta_client.entity_exists("NonExistent") is False
    
    def test_field_exists_check(self, mock_client):
        """Field existence check testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {
                    "fields": {
                        "name": {"type": "varchar"},
                        "type": {"type": "enum"}
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        # Assertions
        assert meta_client.field_exists("Account", "name") is True
        assert meta_client.field_exists("Account", "type") is True
        assert meta_client.field_exists("Account", "nonexistent") is False
        assert meta_client.field_exists("NonExistent", "name") is False
    
    def test_relationship_exists_check(self, mock_client):
        """Relationship existence check testi."""
        # Mock response setup
        mock_response = {
            "entityDefs": {
                "Account": {
                    "links": {
                        "contacts": {"type": "oneToMany"},
                        "opportunities": {"type": "oneToMany"}
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        # Assertions
        assert meta_client.relationship_exists("Account", "contacts") is True
        assert meta_client.relationship_exists("Account", "opportunities") is True
        assert meta_client.relationship_exists("Account", "nonexistent") is False
        assert meta_client.relationship_exists("NonExistent", "contacts") is False


@pytest.mark.unit
@pytest.mark.metadata
class TestMetadataCache:
    """Metadata Cache testleri."""
    
    def test_cache_initialization(self):
        """Cache initialization testi."""
        cache = MetadataCache(ttl_seconds=300)
        
        assert cache.ttl_seconds == 300
        assert len(cache._cache) == 0
    
    def test_cache_set_get_operations(self):
        """Cache set/get operations testi."""
        cache = MetadataCache(ttl_seconds=60)
        
        # Set data
        test_data = {"entityDefs": {"Account": {"fields": {}}}}
        cache.set("test_key", test_data)
        
        # Get data
        result = cache.get("test_key")
        
        # Assertions
        assert result == test_data
    
    def test_cache_expiration(self):
        """Cache expiration testi."""
        cache = MetadataCache(ttl_seconds=0)  # Immediate expiration
        
        # Set data
        test_data = {"test": "data"}
        cache.set("test_key", test_data)
        
        # Wait a bit for expiration
        import time
        time.sleep(0.1)
        
        # Get data (should be None due to expiration)
        result = cache.get("test_key")
        
        # Assertions
        assert result is None
    
    def test_cache_clear(self):
        """Cache clear testi."""
        cache = MetadataCache()
        
        # Set multiple items
        cache.set("key1", {"data": "1"})
        cache.set("key2", {"data": "2"})
        cache.set("key3", {"data": "3"})
        
        # Clear cache
        cache.clear()
        
        # Assertions
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
    
    def test_cache_info(self):
        """Cache info testi."""
        cache = MetadataCache()
        
        # Set some data
        cache.set("key1", {"data": "1"})
        cache.set("key2", {"data": "2"})
        
        # Get cache info
        info = cache.get_cache_info()
        
        # Assertions
        assert isinstance(info, dict)
        assert "total_keys" in info
        assert "active_keys" in info
        assert "expired_keys" in info
        assert info["total_keys"] == 2
        assert info["active_keys"] == 2
        assert info["expired_keys"] == 0
    
    def test_cache_cleanup_expired(self):
        """Cache cleanup expired items testi."""
        cache = MetadataCache(ttl_seconds=0)  # Immediate expiration
        
        # Set data that will expire
        cache.set("expired_key", {"data": "expired"})
        
        # Wait for expiration
        import time
        time.sleep(0.1)
        
        # Set new data
        cache.set("active_key", {"data": "active"})
        
        # Cleanup expired items
        cache.cleanup_expired()
        
        # Get cache info
        info = cache.get_cache_info()
        
        # Assertions
        assert info["active_keys"] == 1
        assert info["expired_keys"] == 0  # Should be cleaned up


@pytest.mark.unit
@pytest.mark.metadata
@pytest.mark.parametrize
class TestMetadataClientParametrized:
    """Metadata Client parametrized testleri."""
    
    @pytest.mark.parametrize("entity_type", ["Account", "Contact", "Lead", "Opportunity"])
    def test_get_metadata_different_entities(self, mock_client, entity_type):
        """Farklı entity türleri için metadata alma testi."""
        # Mock response
        mock_response = {
            "entityDefs": {
                entity_type: {
                    "fields": {"name": {"type": "varchar"}},
                    "links": {}
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.get_entity_metadata(entity_type)
        
        assert isinstance(result, EntityMetadata)
        assert result.has_field("name")
        mock_client.get.assert_called_once()
    
    @pytest.mark.parametrize("field_type,expected_type", [
        ("varchar", FieldType.VARCHAR),
        ("text", FieldType.TEXT),
        ("int", FieldType.INT),
        ("float", FieldType.FLOAT),
        ("bool", FieldType.BOOL),
        ("date", FieldType.DATE),
        ("datetime", FieldType.DATETIME),
        ("enum", FieldType.ENUM),
        ("email", FieldType.EMAIL),
        ("phone", FieldType.PHONE),
        ("url", FieldType.URL)
    ])
    def test_field_type_mapping(self, mock_client, field_type, expected_type):
        """Field type mapping testi."""
        # Mock response
        mock_response = {
            "entityDefs": {
                "TestEntity": {
                    "fields": {
                        "testField": {"type": field_type}
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.get_field_metadata("TestEntity", "testField")
        
        assert isinstance(result, FieldMetadata)
        assert result.type == expected_type
    
    @pytest.mark.parametrize("relationship_type,expected_type", [
        ("oneToMany", RelationshipType.ONE_TO_MANY),
        ("manyToOne", RelationshipType.MANY_TO_ONE),
        ("manyToMany", RelationshipType.MANY_TO_MANY),
        ("oneToOne", RelationshipType.ONE_TO_ONE),
        ("belongsTo", RelationshipType.BELONGS_TO),
        ("hasMany", RelationshipType.HAS_MANY),
        ("hasOne", RelationshipType.HAS_ONE)
    ])
    def test_relationship_type_mapping(self, mock_client, relationship_type, expected_type):
        """Relationship type mapping testi."""
        # Mock response
        mock_response = {
            "entityDefs": {
                "TestEntity": {
                    "links": {
                        "testRelation": {
                            "type": relationship_type,
                            "entity": "RelatedEntity"
                        }
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.get_relationship_metadata("TestEntity", "testRelation")
        
        assert isinstance(result, RelationshipMetadata)
        assert result.type == expected_type
    
    @pytest.mark.parametrize("error_class,status_code", [
        (EntityNotFoundError, 404),
        (ValidationError, 400),
        (MetadataError, 422),
        (EspoCRMError, 500)
    ])
    def test_metadata_error_handling(self, mock_client, error_class, status_code):
        """Metadata error handling testi."""
        mock_client.get.side_effect = error_class(f"Error {status_code}")
        
        meta_client = MetadataClient(mock_client)
        
        with pytest.raises(error_class):
            meta_client.get_application_metadata()


@pytest.mark.unit
@pytest.mark.metadata
@pytest.mark.validation
class TestMetadataClientValidation:
    """Metadata Client validation testleri."""
    
    def test_entity_type_validation(self, mock_client):
        """Entity type validation testi."""
        meta_client = MetadataClient(mock_client)
        
        # Empty entity type
        with pytest.raises(ValidationError):
            meta_client.get_entity_metadata("")
        
        # None entity type
        with pytest.raises(ValidationError):
            meta_client.get_entity_metadata(None)
    
    def test_field_name_validation(self, mock_client):
        """Field name validation testi."""
        meta_client = MetadataClient(mock_client)
        
        # Empty field name
        with pytest.raises(ValidationError):
            meta_client.get_field_metadata("Account", "")
        
        # None field name
        with pytest.raises(ValidationError):
            meta_client.get_field_metadata("Account", None)
    
    def test_relationship_name_validation(self, mock_client):
        """Relationship name validation testi."""
        meta_client = MetadataClient(mock_client)
        
        # Empty relationship name
        with pytest.raises(ValidationError):
            meta_client.get_relationship_metadata("Account", "")
        
        # None relationship name
        with pytest.raises(ValidationError):
            meta_client.get_relationship_metadata("Account", None)
    
    def test_validation_data_validation(self, mock_client):
        """Validation data validation testi."""
        meta_client = MetadataClient(mock_client)
        
        # None validation data
        with pytest.raises(ValidationError):
            meta_client.validate_entity_data("Account", None)
        
        # Invalid validation data type
        with pytest.raises(ValidationError):
            meta_client.validate_entity_data("Account", "invalid_data")


@pytest.mark.unit
@pytest.mark.metadata
@pytest.mark.performance
class TestMetadataClientPerformance:
    """Metadata Client performance testleri."""
    
    def test_metadata_caching_performance(self, mock_client, performance_timer):
        """Metadata caching performance testi."""
        # Mock response
        mock_response = {
            "entityDefs": {
                "Account": {"fields": {"name": {"type": "varchar"}}}
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        performance_timer.start()
        
        # First call - should hit API
        result1 = meta_client.get_application_metadata()
        
        # Subsequent calls - should use cache
        for _ in range(99):
            result = meta_client.get_application_metadata()
        
        performance_timer.stop()
        
        # Performance assertions
        assert performance_timer.elapsed < 1.0  # 1 saniyeden az
        assert mock_client.get.call_count == 1  # Only one API call
    
    def test_bulk_entity_discovery_performance(self, mock_client, performance_timer):
        """Bulk entity discovery performance testi."""
        # Mock large response
        entities = {f"Entity{i}": {"fields": {}} for i in range(100)}
        mock_response = {"entityDefs": entities}
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        performance_timer.start()
        result = meta_client.discover_entities()
        performance_timer.stop()
        
        # Performance assertions
        assert len(result) == 100
        assert performance_timer.elapsed < 0.5  # 0.5 saniyeden az
    
    def test_field_validation_performance(self, mock_client, performance_timer):
        """Field validation performance testi."""
        # Mock response with many fields
        fields = {f"field{i}": {"type": "varchar", "required": i % 2 == 0} for i in range(50)}
        mock_response = {
            "entityDefs": {
                "TestEntity": {"fields": fields}
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        # Test data with all fields
        test_data = {f"field{i}": f"value{i}" for i in range(50)}
        
        performance_timer.start()
        errors = meta_client.validate_entity_data("TestEntity", test_data)
        performance_timer.stop()
        
        # Performance assertions
        assert isinstance(errors, dict)
        assert performance_timer.elapsed < 0.1  # 0.1 saniyeden az


@pytest.mark.integration
@pytest.mark.metadata
class TestMetadataClientIntegration:
    """Metadata Client integration testleri."""
    
    @responses.activate
    def test_full_metadata_workflow(self, real_client, mock_http_responses):
        """Full metadata workflow integration testi."""
        meta_client = MetadataClient(real_client)
        
        # 1. Get application metadata
        app_metadata = meta_client.get_application_metadata()
        assert isinstance(app_metadata, ApplicationMetadata)
        
        # 2. Discover entities
        entities = meta_client.discover_entities()
        assert isinstance(entities, list)
        assert len(entities) > 0
        
        # 3. Get entity metadata for first entity
        if entities:
            entity_type = entities[0]
            entity_metadata = meta_client.get_entity_metadata(entity_type)
            assert isinstance(entity_metadata, EntityMetadata)
            
            # 4. Discover fields
            fields = meta_client.discover_entity_fields(entity_type)
            assert isinstance(fields, dict)
            
            # 5. Discover relationships
            relationships = meta_client.discover_entity_relationships(entity_type)
            assert isinstance(relationships, dict)
    
    def test_metadata_error_recovery(self, real_client):
        """Metadata error recovery testi."""
        meta_client = MetadataClient(real_client)
        
        # Network error simulation
        with patch.object(real_client, 'get', side_effect=ConnectionError("Network error")):
            with pytest.raises(EspoCRMError):
                meta_client.get_application_metadata()
        
        # Recovery after network error
        mock_response = {"entityDefs": {"Account": {"fields": {}}}}
        with patch.object(real_client, 'get', return_value=mock_response):
            result = meta_client.get_application_metadata()
            assert isinstance(result, ApplicationMetadata)


@pytest.mark.unit
@pytest.mark.metadata
@pytest.mark.security
class TestMetadataClientSecurity:
    """Metadata Client security testleri."""
    
    def test_metadata_access_control(self, mock_client):
        """Metadata access control testi."""
        meta_client = MetadataClient(mock_client)
        
        # Unauthorized access simulation
        mock_client.get.side_effect = EspoCRMError("Unauthorized", status_code=401)
        
        with pytest.raises(EspoCRMError):
            meta_client.get_application_metadata()
        
        # Forbidden metadata access
        mock_client.get.side_effect = EspoCRMError("Forbidden", status_code=403)
        
        with pytest.raises(EspoCRMError):
            meta_client.get_entity_metadata("Account")
    
    def test_metadata_injection_prevention(self, mock_client, security_test_data):
        """Metadata injection prevention testi."""
        meta_client = MetadataClient(mock_client)
        
        # SQL injection in entity names
        for payload in security_test_data["sql_injection"]:
            with pytest.raises((ValidationError, EspoCRMError)):
                meta_client.get_entity_metadata(payload)
    
    def test_metadata_sanitization(self, mock_client, security_test_data):
        """Metadata sanitization testi."""
        meta_client = MetadataClient(mock_client)
        
        # XSS in validation data
        for payload in security_test_data["xss_payloads"]:
            validation_data = {"description": payload}
            
            # Should handle malicious data safely
            try:
                meta_client.validate_entity_data("Account", validation_data)
            except (ValidationError, EspoCRMError):
                pass  # Expected for malicious payloads


@pytest.mark.unit
@pytest.mark.metadata
@pytest.mark.edge_cases
class TestMetadataClientEdgeCases:
    """Metadata Client edge cases testleri."""
    
    def test_empty_metadata_response(self, mock_client):
        """Empty metadata response testi."""
        # Mock empty response
        mock_client.get.return_value = {"entityDefs": {}}
        
        meta_client = MetadataClient(mock_client)
        
        result = meta_client.get_application_metadata()
        
        assert isinstance(result, ApplicationMetadata)
        assert len(result.entity_defs) == 0
    
    def test_malformed_metadata_response(self, mock_client):
        """Malformed metadata response testi."""
        # Mock malformed response
        mock_client.get.return_value = {"invalid": "structure"}
        
        meta_client = MetadataClient(mock_client)
        
        # Should handle malformed data gracefully
        with pytest.raises(MetadataError):
            meta_client.get_application_metadata()
    
    def test_missing_field_metadata(self, mock_client):
        """Missing field metadata testi."""
        # Mock response with missing field
        mock_response = {
            "entityDefs": {
                "Account": {
                    "fields": {}  # No fields defined
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        # Should return None for non-existent field
        result = meta_client.get_field_metadata("Account", "nonexistent")
        assert result is None
    
    def test_circular_relationship_detection(self, mock_client):
        """Circular relationship detection testi."""
        # Mock response with circular relationship
        mock_response = {
            "entityDefs": {
                "Account": {
                    "links": {
                        "parent": {
                            "type": "belongsTo",
                            "entity": "Account"  # Self-reference
                        }
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        # Should handle circular relationships
        result = meta_client.get_relationship_metadata("Account", "parent")
        assert isinstance(result, RelationshipMetadata)
        assert result.entity == "Account"  # Self-reference is valid
    
    def test_very_large_metadata(self, mock_client):
        """Very large metadata testi."""
        # Mock response with many entities and fields
        entities = {}
        for i in range(100):
            fields = {f"field{j}": {"type": "varchar"} for j in range(50)}
            entities[f"Entity{i}"] = {"fields": fields}
        
        mock_response = {"entityDefs": entities}
        mock_client.get.return_value = mock_response
        
        meta_client = MetadataClient(mock_client)
        
        # Should handle large metadata efficiently
        result = meta_client.get_application_metadata()
        assert isinstance(result, ApplicationMetadata)
        assert len(result.entity_defs) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])