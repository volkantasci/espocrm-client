# Quick Start Guide

Get up and running with EspoCRM Python Client in minutes!

## Prerequisites

- Python 3.8 or higher
- EspoCRM instance with API access
- API credentials (API key, username/password, or HMAC credentials)

## Installation

```bash
pip install espocrm-python-client
```

## Basic Setup

### 1. Import the Client

```python
from espocrm import EspoCRMClient
from espocrm.auth import APIKeyAuth
```

### 2. Configure Authentication

Choose your preferred authentication method:

=== "API Key (Recommended)"

    ```python
    auth = APIKeyAuth("your-api-key")
    client = EspoCRMClient("https://your-espocrm.com", auth)
    ```

=== "Basic Authentication"

    ```python
    from espocrm.auth import BasicAuth
    
    auth = BasicAuth("username", "password")
    client = EspoCRMClient("https://your-espocrm.com", auth)
    ```

=== "HMAC Authentication"

    ```python
    from espocrm.auth import HMACAuth
    
    auth = HMACAuth("api-key", "secret-key")
    client = EspoCRMClient("https://your-espocrm.com", auth)
    ```

### 3. Test the Connection

```python
try:
    # Test connection by getting application metadata
    metadata = client.metadata.get_app_metadata()
    print(f"✅ Connected to EspoCRM: {metadata.version}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## Your First CRUD Operations

### Create a Record

```python
# Create a new Lead
lead_data = {
    "firstName": "John",
    "lastName": "Doe",
    "emailAddress": "john.doe@example.com",
    "phone": "+1-555-0123",
    "status": "New",
    "source": "Website"
}

try:
    lead = client.crud.create("Lead", lead_data)
    print(f"✅ Created Lead: {lead.id}")
    print(f"   Name: {lead.firstName} {lead.lastName}")
    print(f"   Email: {lead.emailAddress}")
except Exception as e:
    print(f"❌ Failed to create Lead: {e}")
```

### Read Records

```python
# Get a specific record
try:
    lead = client.crud.get("Lead", lead.id)
    print(f"📋 Lead Details:")
    print(f"   ID: {lead.id}")
    print(f"   Name: {lead.firstName} {lead.lastName}")
    print(f"   Status: {lead.status}")
    print(f"   Created: {lead.createdAt}")
except Exception as e:
    print(f"❌ Failed to get Lead: {e}")

# List multiple records
try:
    leads = client.crud.list("Lead", limit=10)
    print(f"📋 Found {leads.total} Leads:")
    for lead in leads.records:
        print(f"   • {lead.firstName} {lead.lastName} ({lead.status})")
except Exception as e:
    print(f"❌ Failed to list Leads: {e}")
```

### Update a Record

```python
# Update the lead's status
updates = {
    "status": "Qualified",
    "description": "Qualified lead from website contact form"
}

try:
    success = client.crud.update("Lead", lead.id, updates)
    if success:
        print("✅ Lead updated successfully")
    else:
        print("❌ Failed to update Lead")
except Exception as e:
    print(f"❌ Update failed: {e}")
```

### Delete a Record

```python
# Delete the lead
try:
    success = client.crud.delete("Lead", lead.id)
    if success:
        print("✅ Lead deleted successfully")
    else:
        print("❌ Failed to delete Lead")
except Exception as e:
    print(f"❌ Delete failed: {e}")
```

## Working with Different Entity Types

### Accounts

```python
# Create an Account
account_data = {
    "name": "Acme Corporation",
    "type": "Customer",
    "industry": "Technology",
    "website": "https://acme.com",
    "emailAddress": "info@acme.com",
    "phoneNumber": "+1-555-0100"
}

account = client.crud.create("Account", account_data)
print(f"Created Account: {account.name}")
```

### Contacts

```python
# Create a Contact
contact_data = {
    "firstName": "Jane",
    "lastName": "Smith",
    "emailAddress": "jane.smith@acme.com",
    "phoneNumber": "+1-555-0101",
    "title": "CTO",
    "accountId": account.id  # Link to the account
}

contact = client.crud.create("Contact", contact_data)
print(f"Created Contact: {contact.firstName} {contact.lastName}")
```

### Opportunities

```python
# Create an Opportunity
opportunity_data = {
    "name": "Acme Software License",
    "stage": "Prospecting",
    "amount": 50000.00,
    "probability": 25,
    "closeDate": "2025-03-31",
    "accountId": account.id
}

opportunity = client.crud.create("Opportunity", opportunity_data)
print(f"Created Opportunity: {opportunity.name}")
```

## Advanced Search

```python
from espocrm.models import SearchParams

# Search for qualified leads created in the last 30 days
search_params = SearchParams(
    where=[
        {
            "type": "equals",
            "attribute": "status",
            "value": "Qualified"
        },
        {
            "type": "after",
            "attribute": "createdAt",
            "value": "2025-01-01"
        }
    ],
    order_by="createdAt",
    order="desc",
    limit=20,
    select=["id", "firstName", "lastName", "emailAddress", "status", "createdAt"]
)

results = client.crud.search("Lead", search_params)
print(f"Found {len(results.records)} qualified leads:")
for lead in results.records:
    print(f"  • {lead.firstName} {lead.lastName} - {lead.createdAt}")
```

## Working with Relationships

```python
# Link a Contact to an Account
client.relationships.relate("Account", account.id, "contacts", contact.id)
print("✅ Contact linked to Account")

# Get all contacts for an account
contacts = client.relationships.list("Account", account.id, "contacts")
print(f"Account has {len(contacts.records)} contacts:")
for contact in contacts.records:
    print(f"  • {contact.firstName} {contact.lastName}")

# Unlink the contact
client.relationships.unrelate("Account", account.id, "contacts", contact.id)
print("✅ Contact unlinked from Account")
```

## Error Handling

```python
from espocrm.exceptions import (
    EspoCRMError,
    EspoCRMAuthenticationError,
    EspoCRMNotFoundError,
    EspoCRMValidationError
)

try:
    # Attempt to get a non-existent record
    lead = client.crud.get("Lead", "non-existent-id")
except EspoCRMNotFoundError:
    print("❌ Lead not found")
except EspoCRMAuthenticationError:
    print("❌ Authentication failed - check your credentials")
except EspoCRMValidationError as e:
    print(f"❌ Validation error: {e}")
except EspoCRMError as e:
    print(f"❌ EspoCRM API error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

## Using Environment Variables

For better security, use environment variables for configuration:

```bash
# Set environment variables
export ESPOCRM_URL="https://your-espocrm.com"
export ESPOCRM_API_KEY="your-api-key"
```

```python
from espocrm import create_client

# Automatically uses environment variables
client = create_client()

# Or create config from environment
from espocrm.config import create_config_from_env

config = create_config_from_env()
client = EspoCRMClient.from_config(config)
```

## Logging

Enable structured logging to monitor your application:

```python
from espocrm.logging import setup_logging, get_logger

# Setup logging
setup_logging(level="INFO", format="json")

# Get a logger
logger = get_logger("my_app")

# Log with context
logger.info(
    "Lead created successfully",
    extra={
        "lead_id": lead.id,
        "lead_name": f"{lead.firstName} {lead.lastName}",
        "execution_time_ms": 245
    }
)
```

## CLI Tool

You can also use the command-line interface:

```bash
# Set environment variables
export ESPOCRM_URL="https://your-espocrm.com"
export ESPOCRM_API_KEY="your-api-key"

# List leads
espocrm-cli list Lead --limit 5

# Get specific lead
espocrm-cli get Lead lead-id

# Create a lead
espocrm-cli create Lead '{"firstName": "John", "lastName": "Doe", "emailAddress": "john@example.com"}'

# Update a lead
espocrm-cli update Lead lead-id '{"status": "Qualified"}'

# Get metadata
espocrm-cli metadata --entity-type Lead
```

## Complete Example

Here's a complete example that demonstrates the main features:

```python
#!/usr/bin/env python3
"""
EspoCRM Python Client - Complete Example
"""

from espocrm import EspoCRMClient
from espocrm.auth import APIKeyAuth
from espocrm.models import SearchParams
from espocrm.logging import setup_logging, get_logger
from espocrm.exceptions import EspoCRMError

# Setup logging
setup_logging(level="INFO")
logger = get_logger(__name__)

def main():
    # Initialize client
    auth = APIKeyAuth("your-api-key")
    client = EspoCRMClient("https://your-espocrm.com", auth)
    
    try:
        # Test connection
        metadata = client.metadata.get_app_metadata()
        logger.info(f"Connected to EspoCRM v{metadata.version}")
        
        # Create an account
        account_data = {
            "name": "Tech Solutions Inc.",
            "type": "Customer",
            "industry": "Technology"
        }
        account = client.crud.create("Account", account_data)
        logger.info(f"Created account: {account.name}")
        
        # Create a contact
        contact_data = {
            "firstName": "Alice",
            "lastName": "Johnson",
            "emailAddress": "alice@techsolutions.com",
            "accountId": account.id
        }
        contact = client.crud.create("Contact", contact_data)
        logger.info(f"Created contact: {contact.firstName} {contact.lastName}")
        
        # Create an opportunity
        opportunity_data = {
            "name": "Software Implementation",
            "stage": "Prospecting",
            "amount": 75000.00,
            "accountId": account.id
        }
        opportunity = client.crud.create("Opportunity", opportunity_data)
        logger.info(f"Created opportunity: {opportunity.name}")
        
        # Search for recent opportunities
        search_params = SearchParams(
            where=[
                {"type": "greaterThan", "attribute": "amount", "value": 50000}
            ],
            order_by="amount",
            order="desc",
            limit=10
        )
        
        results = client.crud.search("Opportunity", search_params)
        logger.info(f"Found {len(results.records)} high-value opportunities")
        
        # List account relationships
        contacts = client.relationships.list("Account", account.id, "contacts")
        opportunities = client.relationships.list("Account", account.id, "opportunities")
        
        logger.info(f"Account has {len(contacts.records)} contacts and {len(opportunities.records)} opportunities")
        
    except EspoCRMError as e:
        logger.error(f"EspoCRM API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
```

## Next Steps

Now that you've learned the basics, explore more advanced features:

- [Authentication Methods](authentication.md) - Detailed authentication setup
- [CRUD Operations](crud.md) - Complete CRUD reference
- [Search & Filtering](advanced/search.md) - Advanced search capabilities
- [Relationship Management](relationships.md) - Working with entity relationships
- [Error Handling](advanced/error-handling.md) - Comprehensive error handling
- [Performance Optimization](advanced/performance.md) - Tips for better performance
- [CLI Tool](cli.md) - Command-line interface reference

## Getting Help

- 📚 [Full Documentation](index.md)
- 🐛 [Report Issues](https://github.com/espocrm/espocrm-python-client/issues)
- 💬 [Discussions](https://github.com/espocrm/espocrm-python-client/discussions)
- 📧 [Support Email](mailto:support@espocrm-python-client.com)