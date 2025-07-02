"""
EspoCRM Entities Model Test Module

Entity modelleri için kapsamlı testler.
"""

import pytest
import json
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, patch

from espocrm.models.entities import Entity, EntityCollection
from espocrm.models.base import BaseModel
from espocrm.exceptions import ValidationError, EntityError


@pytest.mark.unit
@pytest.mark.models
class TestEntity:
    """Entity model temel testleri."""
    
    def test_entity_initialization(self):
        """Entity initialization testi."""
        data = {
            "id": "account_123",
            "name": "Test Company",
            "type": "Customer",
            "createdAt": "2024-01-01T10:00:00+00:00"
        }
        
        entity = Entity("Account", data)
        
        # Assertions
        assert entity.entity_type == "Account"
        assert entity.id == "account_123"
        assert entity.get("name") == "Test Company"
        assert entity.get("type") == "Customer"
        assert entity.data == data
    
    def test_entity_initialization_without_id(self):
        """ID olmadan entity initialization testi."""
        data = {
            "name": "New Company",
            "type": "Customer"
        }
        
        entity = Entity("Account", data)
        
        # Assertions
        assert entity.entity_type == "Account"
        assert entity.id is None
        assert entity.get("name") == "New Company"
    
    def test_entity_get_method(self):
        """Entity get method testi."""
        data = {
            "id": "contact_123",
            "firstName": "John",
            "lastName": "Doe",
            "emailAddress": "john.doe@test.com"
        }
        
        entity = Entity("Contact", data)
        
        # Assertions
        assert entity.get("firstName") == "John"
        assert entity.get("lastName") == "Doe"
        assert entity.get("emailAddress") == "john.doe@test.com"
        assert entity.get("nonexistent") is None
        assert entity.get("nonexistent", "default") == "default"
    
    def test_entity_set_method(self):
        """Entity set method testi."""
        data = {"id": "account_123", "name": "Original Name"}
        entity = Entity("Account", data)
        
        # Set new value
        entity.set("name", "Updated Name")
        entity.set("industry", "Technology")
        
        # Assertions
        assert entity.get("name") == "Updated Name"
        assert entity.get("industry") == "Technology"
        assert "industry" in entity.data
    
    def test_entity_has_method(self):
        """Entity has method testi."""
        data = {
            "id": "lead_123",
            "firstName": "Jane",
            "status": "New",
            "source": None
        }
        
        entity = Entity("Lead", data)
        
        # Assertions
        assert entity.has("firstName") is True
        assert entity.has("status") is True
        assert entity.has("source") is True  # None value but key exists
        assert entity.has("nonexistent") is False
    
    def test_entity_remove_method(self):
        """Entity remove method testi."""
        data = {
            "id": "opportunity_123",
            "name": "Big Deal",
            "stage": "Prospecting",
            "amount": 50000
        }
        
        entity = Entity("Opportunity", data)
        
        # Remove field
        entity.remove("stage")
        
        # Assertions
        assert entity.has("stage") is False
        assert entity.get("stage") is None
        assert "stage" not in entity.data
        assert entity.has("name") is True  # Other fields remain
    
    def test_entity_update_method(self):
        """Entity update method testi."""
        data = {"id": "account_123", "name": "Original Name", "type": "Customer"}
        entity = Entity("Account", data)
        
        # Update with new data
        update_data = {
            "name": "Updated Name",
            "industry": "Technology",
            "website": "https://updated.com"
        }
        entity.update(update_data)
        
        # Assertions
        assert entity.get("name") == "Updated Name"
        assert entity.get("type") == "Customer"  # Original field preserved
        assert entity.get("industry") == "Technology"
        assert entity.get("website") == "https://updated.com"
    
    def test_entity_to_dict_method(self):
        """Entity to_dict method testi."""
        data = {
            "id": "contact_123",
            "firstName": "John",
            "lastName": "Doe",
            "createdAt": "2024-01-01T10:00:00+00:00"
        }
        
        entity = Entity("Contact", data)
        result = entity.to_dict()
        
        # Assertions
        assert isinstance(result, dict)
        assert result == data
        assert result is not entity.data  # Should be a copy
    
    def test_entity_to_json_method(self):
        """Entity to_json method testi."""
        data = {
            "id": "account_123",
            "name": "Test Company",
            "amount": 1000.50
        }
        
        entity = Entity("Account", data)
        json_str = entity.to_json()
        
        # Assertions
        assert isinstance(json_str, str)
        parsed_data = json.loads(json_str)
        assert parsed_data == data
    
    def test_entity_from_json_method(self):
        """Entity from_json method testi."""
        data = {
            "id": "lead_123",
            "firstName": "Jane",
            "status": "New"
        }
        json_str = json.dumps(data)
        
        entity = Entity.from_json("Lead", json_str)
        
        # Assertions
        assert isinstance(entity, Entity)
        assert entity.entity_type == "Lead"
        assert entity.get("firstName") == "Jane"
        assert entity.get("status") == "New"
    
    def test_entity_equality(self):
        """Entity equality testi."""
        data1 = {"id": "account_123", "name": "Test Company"}
        data2 = {"id": "account_123", "name": "Test Company"}
        data3 = {"id": "account_456", "name": "Other Company"}
        
        entity1 = Entity("Account", data1)
        entity2 = Entity("Account", data2)
        entity3 = Entity("Account", data3)
        entity4 = Entity("Contact", data1)  # Different type
        
        # Assertions
        assert entity1 == entity2  # Same type and data
        assert entity1 != entity3  # Different data
        assert entity1 != entity4  # Different type
        assert entity1 != "not_an_entity"  # Different class
    
    def test_entity_string_representation(self):
        """Entity string representation testi."""
        data = {"id": "account_123", "name": "Test Company"}
        entity = Entity("Account", data)
        
        str_repr = str(entity)
        
        # Assertions
        assert "Account" in str_repr
        assert "account_123" in str_repr
        assert "Test Company" in str_repr
    
    def test_entity_repr_method(self):
        """Entity repr method testi."""
        data = {"id": "contact_123", "firstName": "John"}
        entity = Entity("Contact", data)
        
        repr_str = repr(entity)
        
        # Assertions
        assert "Entity" in repr_str
        assert "Contact" in repr_str
        assert "contact_123" in repr_str


@pytest.mark.unit
@pytest.mark.models
class TestEntityValidation:
    """Entity validation testleri."""
    
    def test_entity_type_validation(self):
        """Entity type validation testi."""
        data = {"id": "test_123", "name": "Test"}
        
        # Valid entity types
        valid_types = ["Account", "Contact", "Lead", "Opportunity", "User"]
        for entity_type in valid_types:
            entity = Entity(entity_type, data)
            assert entity.entity_type == entity_type
        
        # Invalid entity types
        invalid_types = ["", None, 123, "invalid type", "account"]  # lowercase
        for invalid_type in invalid_types:
            with pytest.raises(ValidationError):
                Entity(invalid_type, data)
    
    def test_entity_data_validation(self):
        """Entity data validation testi."""
        # Valid data
        valid_data = [
            {"id": "test_123", "name": "Test"},
            {"name": "Test without ID"},
            {}  # Empty dict is valid
        ]
        
        for data in valid_data:
            entity = Entity("Account", data)
            assert isinstance(entity.data, dict)
        
        # Invalid data
        invalid_data = [None, "string", 123, [1, 2, 3]]
        
        for data in invalid_data:
            with pytest.raises(ValidationError):
                Entity("Account", data)
    
    def test_entity_id_validation(self):
        """Entity ID validation testi."""
        # Valid IDs
        valid_ids = ["account_123", "contact_456", "lead_789", "opportunity_012"]
        
        for entity_id in valid_ids:
            data = {"id": entity_id, "name": "Test"}
            entity = Entity("Account", data)
            assert entity.id == entity_id
        
        # Invalid IDs
        invalid_ids = ["", "invalid id", "id\nwith\nnewlines", "id<with>html"]
        
        for entity_id in invalid_ids:
            data = {"id": entity_id, "name": "Test"}
            with pytest.raises(ValidationError):
                Entity("Account", data)
    
    def test_field_name_validation(self):
        """Field name validation testi."""
        entity = Entity("Account", {"id": "test_123"})
        
        # Valid field names
        valid_fields = ["name", "firstName", "lastName", "emailAddress", "phoneNumber"]
        
        for field_name in valid_fields:
            entity.set(field_name, "test_value")
            assert entity.get(field_name) == "test_value"
        
        # Invalid field names
        invalid_fields = ["", None, 123, "field with spaces", "field\nwith\nnewlines"]
        
        for field_name in invalid_fields:
            with pytest.raises(ValidationError):
                entity.set(field_name, "test_value")
    
    def test_field_value_validation(self):
        """Field value validation testi."""
        entity = Entity("Account", {"id": "test_123"})
        
        # Valid values (most types are allowed)
        valid_values = [
            "string",
            123,
            123.45,
            True,
            False,
            None,
            [],
            {},
            date.today(),
            datetime.now()
        ]
        
        for i, value in enumerate(valid_values):
            field_name = f"field_{i}"
            entity.set(field_name, value)
            assert entity.get(field_name) == value


@pytest.mark.unit
@pytest.mark.models
class TestEntityTypeConversion:
    """Entity type conversion testleri."""
    
    def test_string_field_conversion(self):
        """String field conversion testi."""
        entity = Entity("Account", {"id": "test_123"})
        
        # Various types that should convert to string
        test_values = [
            (123, "123"),
            (123.45, "123.45"),
            (True, "True"),
            (False, "False")
        ]
        
        for input_val, expected in test_values:
            entity.set("stringField", input_val, convert_type=True)
            assert entity.get("stringField") == expected
    
    def test_numeric_field_conversion(self):
        """Numeric field conversion testi."""
        entity = Entity("Account", {"id": "test_123"})
        
        # String to number conversion
        entity.set("intField", "123", convert_type=True, target_type=int)
        assert entity.get("intField") == 123
        
        entity.set("floatField", "123.45", convert_type=True, target_type=float)
        assert entity.get("floatField") == 123.45
        
        # Invalid conversions should raise error
        with pytest.raises(ValidationError):
            entity.set("intField", "not_a_number", convert_type=True, target_type=int)
    
    def test_boolean_field_conversion(self):
        """Boolean field conversion testi."""
        entity = Entity("Account", {"id": "test_123"})
        
        # Various values that should convert to boolean
        true_values = ["true", "True", "1", 1, "yes", "on"]
        false_values = ["false", "False", "0", 0, "no", "off", ""]
        
        for value in true_values:
            entity.set("boolField", value, convert_type=True, target_type=bool)
            assert entity.get("boolField") is True
        
        for value in false_values:
            entity.set("boolField", value, convert_type=True, target_type=bool)
            assert entity.get("boolField") is False
    
    def test_date_field_conversion(self):
        """Date field conversion testi."""
        entity = Entity("Account", {"id": "test_123"})
        
        # String to date conversion
        date_strings = [
            "2024-01-01",
            "2024-12-31",
            "2024-06-15"
        ]
        
        for date_str in date_strings:
            entity.set("dateField", date_str, convert_type=True, target_type=date)
            result = entity.get("dateField")
            assert isinstance(result, date)
            assert result.isoformat() == date_str
    
    def test_datetime_field_conversion(self):
        """DateTime field conversion testi."""
        entity = Entity("Account", {"id": "test_123"})
        
        # String to datetime conversion
        datetime_str = "2024-01-01T10:30:00+00:00"
        entity.set("datetimeField", datetime_str, convert_type=True, target_type=datetime)
        
        result = entity.get("datetimeField")
        assert isinstance(result, datetime)


@pytest.mark.unit
@pytest.mark.models
class TestEntityCollection:
    """EntityCollection testleri."""
    
    def test_collection_initialization(self):
        """Collection initialization testi."""
        entities_data = [
            {"id": "account_1", "name": "Company 1"},
            {"id": "account_2", "name": "Company 2"},
            {"id": "account_3", "name": "Company 3"}
        ]
        
        entities = [Entity("Account", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Assertions
        assert len(collection) == 3
        assert collection.count() == 3
        assert all(isinstance(entity, Entity) for entity in collection)
    
    def test_collection_iteration(self):
        """Collection iteration testi."""
        entities_data = [
            {"id": "contact_1", "firstName": "John"},
            {"id": "contact_2", "firstName": "Jane"}
        ]
        
        entities = [Entity("Contact", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Test iteration
        names = []
        for entity in collection:
            names.append(entity.get("firstName"))
        
        assert names == ["John", "Jane"]
    
    def test_collection_indexing(self):
        """Collection indexing testi."""
        entities_data = [
            {"id": "lead_1", "status": "New"},
            {"id": "lead_2", "status": "Assigned"},
            {"id": "lead_3", "status": "In Process"}
        ]
        
        entities = [Entity("Lead", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Test indexing
        assert collection[0].get("status") == "New"
        assert collection[1].get("status") == "Assigned"
        assert collection[2].get("status") == "In Process"
        assert collection[-1].get("status") == "In Process"
    
    def test_collection_slicing(self):
        """Collection slicing testi."""
        entities_data = [{"id": f"entity_{i}", "name": f"Entity {i}"} for i in range(5)]
        entities = [Entity("Account", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Test slicing
        slice_result = collection[1:4]
        assert isinstance(slice_result, EntityCollection)
        assert len(slice_result) == 3
        assert slice_result[0].get("name") == "Entity 1"
        assert slice_result[2].get("name") == "Entity 3"
    
    def test_collection_filtering(self):
        """Collection filtering testi."""
        entities_data = [
            {"id": "account_1", "type": "Customer", "industry": "Technology"},
            {"id": "account_2", "type": "Partner", "industry": "Healthcare"},
            {"id": "account_3", "type": "Customer", "industry": "Technology"},
            {"id": "account_4", "type": "Investor", "industry": "Finance"}
        ]
        
        entities = [Entity("Account", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Filter by type
        customers = collection.filter(lambda e: e.get("type") == "Customer")
        assert len(customers) == 2
        assert all(e.get("type") == "Customer" for e in customers)
        
        # Filter by industry
        tech_companies = collection.filter(lambda e: e.get("industry") == "Technology")
        assert len(tech_companies) == 2
        assert all(e.get("industry") == "Technology" for e in tech_companies)
    
    def test_collection_mapping(self):
        """Collection mapping testi."""
        entities_data = [
            {"id": "contact_1", "firstName": "John", "lastName": "Doe"},
            {"id": "contact_2", "firstName": "Jane", "lastName": "Smith"}
        ]
        
        entities = [Entity("Contact", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Map to full names
        full_names = collection.map(lambda e: f"{e.get('firstName')} {e.get('lastName')}")
        assert full_names == ["John Doe", "Jane Smith"]
        
        # Map to IDs
        ids = collection.map(lambda e: e.id)
        assert ids == ["contact_1", "contact_2"]
    
    def test_collection_finding(self):
        """Collection finding testi."""
        entities_data = [
            {"id": "opportunity_1", "stage": "Prospecting", "amount": 10000},
            {"id": "opportunity_2", "stage": "Qualification", "amount": 25000},
            {"id": "opportunity_3", "stage": "Proposal", "amount": 50000}
        ]
        
        entities = [Entity("Opportunity", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Find by ID
        found_entity = collection.find_by_id("opportunity_2")
        assert found_entity is not None
        assert found_entity.get("stage") == "Qualification"
        
        # Find by condition
        large_opportunity = collection.find(lambda e: e.get("amount") > 40000)
        assert large_opportunity is not None
        assert large_opportunity.get("amount") == 50000
        
        # Find non-existent
        not_found = collection.find_by_id("nonexistent")
        assert not_found is None
    
    def test_collection_sorting(self):
        """Collection sorting testi."""
        entities_data = [
            {"id": "account_1", "name": "Zebra Corp", "createdAt": "2024-01-03"},
            {"id": "account_2", "name": "Alpha Inc", "createdAt": "2024-01-01"},
            {"id": "account_3", "name": "Beta LLC", "createdAt": "2024-01-02"}
        ]
        
        entities = [Entity("Account", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Sort by name
        sorted_by_name = collection.sort(key=lambda e: e.get("name"))
        names = [e.get("name") for e in sorted_by_name]
        assert names == ["Alpha Inc", "Beta LLC", "Zebra Corp"]
        
        # Sort by creation date
        sorted_by_date = collection.sort(key=lambda e: e.get("createdAt"))
        dates = [e.get("createdAt") for e in sorted_by_date]
        assert dates == ["2024-01-01", "2024-01-02", "2024-01-03"]
    
    def test_collection_grouping(self):
        """Collection grouping testi."""
        entities_data = [
            {"id": "contact_1", "accountId": "account_1", "title": "Manager"},
            {"id": "contact_2", "accountId": "account_1", "title": "Developer"},
            {"id": "contact_3", "accountId": "account_2", "title": "Manager"},
            {"id": "contact_4", "accountId": "account_2", "title": "Designer"}
        ]
        
        entities = [Entity("Contact", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Group by account
        grouped = collection.group_by(lambda e: e.get("accountId"))
        
        assert len(grouped) == 2
        assert "account_1" in grouped
        assert "account_2" in grouped
        assert len(grouped["account_1"]) == 2
        assert len(grouped["account_2"]) == 2
    
    def test_collection_aggregation(self):
        """Collection aggregation testi."""
        entities_data = [
            {"id": "opportunity_1", "amount": 10000, "probability": 25},
            {"id": "opportunity_2", "amount": 25000, "probability": 50},
            {"id": "opportunity_3", "amount": 50000, "probability": 75}
        ]
        
        entities = [Entity("Opportunity", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Sum amounts
        total_amount = collection.sum(lambda e: e.get("amount"))
        assert total_amount == 85000
        
        # Average probability
        avg_probability = collection.average(lambda e: e.get("probability"))
        assert avg_probability == 50.0
        
        # Max amount
        max_amount = collection.max(lambda e: e.get("amount"))
        assert max_amount == 50000
        
        # Min amount
        min_amount = collection.min(lambda e: e.get("amount"))
        assert min_amount == 10000


@pytest.mark.unit
@pytest.mark.models
@pytest.mark.performance
class TestEntityPerformance:
    """Entity performance testleri."""
    
    def test_large_entity_creation_performance(self, performance_timer):
        """Large entity creation performance testi."""
        # Large entity data
        large_data = {f"field_{i}": f"value_{i}" for i in range(1000)}
        large_data["id"] = "large_entity_123"
        
        performance_timer.start()
        entity = Entity("LargeEntity", large_data)
        performance_timer.stop()
        
        # Performance assertions
        assert len(entity.data) == 1001  # 1000 fields + id
        assert performance_timer.elapsed < 0.1  # 100ms'den az
    
    def test_bulk_entity_operations_performance(self, performance_timer):
        """Bulk entity operations performance testi."""
        # Create many entities
        entities_data = [
            {"id": f"entity_{i}", "name": f"Entity {i}", "value": i}
            for i in range(1000)
        ]
        
        performance_timer.start()
        entities = [Entity("TestEntity", data) for data in entities_data]
        collection = EntityCollection(entities)
        
        # Perform operations
        filtered = collection.filter(lambda e: e.get("value") % 2 == 0)
        mapped = filtered.map(lambda e: e.get("name"))
        performance_timer.stop()
        
        # Performance assertions
        assert len(filtered) == 500  # Even numbers
        assert len(mapped) == 500
        assert performance_timer.elapsed < 1.0  # 1 saniyeden az
    
    def test_entity_serialization_performance(self, performance_timer):
        """Entity serialization performance testi."""
        # Create entity with moderate amount of data
        data = {f"field_{i}": f"value_{i}" for i in range(100)}
        data["id"] = "test_entity_123"
        entity = Entity("TestEntity", data)
        
        performance_timer.start()
        
        # Serialize/deserialize 100 times
        for _ in range(100):
            json_str = entity.to_json()
            Entity.from_json("TestEntity", json_str)
        
        performance_timer.stop()
        
        # Performance assertions
        assert performance_timer.elapsed < 0.5  # 500ms'den az


@pytest.mark.unit
@pytest.mark.models
@pytest.mark.edge_cases
class TestEntityEdgeCases:
    """Entity edge cases testleri."""
    
    def test_entity_with_none_values(self):
        """None değerlerle entity testi."""
        data = {
            "id": "test_123",
            "name": None,
            "description": None,
            "active": True
        }
        
        entity = Entity("TestEntity", data)
        
        # None values should be handled properly
        assert entity.get("name") is None
        assert entity.get("description") is None
        assert entity.get("active") is True
        assert entity.has("name") is True  # Key exists even if value is None
    
    def test_entity_with_empty_strings(self):
        """Empty string'lerle entity testi."""
        data = {
            "id": "test_123",
            "name": "",
            "description": "",
            "category": "valid"
        }
        
        entity = Entity("TestEntity", data)
        
        # Empty strings should be preserved
        assert entity.get("name") == ""
        assert entity.get("description") == ""
        assert entity.get("category") == "valid"
    
    def test_entity_with_special_characters(self):
        """Özel karakterlerle entity testi."""
        data = {
            "id": "test_123",
            "name": "Company with Special Chars: !@#$%^&*()",
            "description": "Description with\nnewlines\tand\ttabs",
            "unicode": "Unicode: üñíçødé 中文 العربية"
        }
        
        entity = Entity("TestEntity", data)
        
        # Special characters should be preserved
        assert "!@#$%^&*()" in entity.get("name")
        assert "\n" in entity.get("description")
        assert "\t" in entity.get("description")
        assert "üñíçødé" in entity.get("unicode")
    
    def test_entity_with_nested_data(self):
        """Nested data ile entity testi."""
        data = {
            "id": "test_123",
            "name": "Test Entity",
            "address": {
                "street": "123 Main St",
                "city": "Test City",
                "country": "Test Country"
            },
            "tags": ["tag1", "tag2", "tag3"],
            "metadata": {
                "created": "2024-01-01",
                "source": "api",
                "nested": {
                    "level": 2,
                    "data": "deep"
                }
            }
        }
        
        entity = Entity("TestEntity", data)
        
        # Nested data should be preserved
        assert isinstance(entity.get("address"), dict)
        assert entity.get("address")["street"] == "123 Main St"
        assert isinstance(entity.get("tags"), list)
        assert len(entity.get("tags")) == 3
        assert entity.get("metadata")["nested"]["level"] == 2
    
    def test_entity_with_very_long_strings(self):
        """Çok uzun string'lerle entity testi."""
        long_string = "A" * 10000  # 10KB string
        
        data = {
            "id": "test_123",
            "name": "Test Entity",
            "longDescription": long_string
        }
        
        entity = Entity("TestEntity", data)
        
        # Long strings should be handled
        assert len(entity.get("longDescription")) == 10000
        assert entity.get("longDescription") == long_string
    
    def test_entity_field_name_conflicts(self):
        """Field name conflicts testi."""
        data = {
            "id": "test_123",
            "entity_type": "ShouldNotConflict",  # Conflicts with property
            "data": "ShouldNotConflict"  # Conflicts with property
        }
        
        entity = Entity("TestEntity", data)
        
        # Property access should work correctly
        assert entity.entity_type == "TestEntity"  # Property
        assert entity.get("entity_type") == "ShouldNotConflict"  # Data field
        assert isinstance(entity.data, dict)  # Property
        assert entity.get("data") == "ShouldNotConflict"  # Data field


if __name__ == "__main__":
    pytest.main([__file__, "-v"])