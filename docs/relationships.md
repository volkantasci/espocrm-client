# EspoCRM Relationship Yönetimi

EspoCRM Python Client, entity'ler arası ilişki yönetimi için kapsamlı bir API sağlar. Bu dokümantasyon relationship operasyonlarının nasıl kullanılacağını açıklar.

## İçindekiler

- [Temel Kavramlar](#temel-kavramlar)
- [RelationshipClient](#relationshipclient)
- [İlişkili Kayıtları Listeleme](#ilişkili-kayıtları-listeleme)
- [Link Operasyonları](#link-operasyonları)
- [Unlink Operasyonları](#unlink-operasyonları)
- [Mass Relate](#mass-relate)
- [Request Modelleri](#request-modelleri)
- [Entity Helper Methods](#entity-helper-methods)
- [Convenience Methods](#convenience-methods)
- [Hata Yönetimi](#hata-yönetimi)
- [Örnekler](#örnekler)

## Temel Kavramlar

### Relationship Türleri

EspoCRM'de üç ana relationship türü vardır:

1. **One-to-Many**: Bir entity'nin birden fazla başka entity ile ilişkisi
   - Örnek: Account -> Opportunities
   - Bir Account'un birden fazla Opportunity'si olabilir

2. **Many-to-Many**: Çoklu entity'ler arası çift yönlü ilişki
   - Örnek: Contact -> Teams
   - Bir Contact birden fazla Team'e üye olabilir, bir Team'de birden fazla Contact olabilir

3. **Parent-to-Children**: Hiyerarşik ilişki
   - Örnek: Account -> Contacts
   - Bir Account'un birden fazla Contact'ı olabilir

### Link Adları

Her relationship'in bir link adı vardır:
- `contacts` - Contact'lar ile ilişki
- `opportunities` - Opportunity'ler ile ilişki
- `teams` - Team'ler ile ilişki
- `cases` - Case'ler ile ilişki
- `documents` - Document'lar ile ilişki

## RelationshipClient

[`RelationshipClient`](../espocrm/clients/relationships.py:67) sınıfı tüm relationship operasyonlarını yönetir.

### Başlatma

```python
from espocrm import EspoCRMClient, ClientConfig
from espocrm.auth import APIKeyAuth

config = ClientConfig(base_url="https://your-espocrm.com")
auth = APIKeyAuth(api_key="your-api-key")

with EspoCRMClient(config.base_url, auth, config) as client:
    # RelationshipClient otomatik olarak client.relationships olarak erişilebilir
    relationships = client.relationships
```

## İlişkili Kayıtları Listeleme

### Basit Listeleme

```python
# Account'un tüm Contact'larını listele
response = client.relationships.list_related(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts"
)

contacts = response.get_entities()
print(f"Toplam Contact sayısı: {response.total}")
```

### Filtreleme ve Sıralama

```python
# Filtrelenmiş ve sıralanmış listeleme
response = client.relationships.list_related(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    max_size=20,
    order_by="name",
    order="asc",
    select=["id", "name", "emailAddress"]
)
```

### SearchParams ile Gelişmiş Arama

```python
from espocrm.models import SearchParams, contains, equals

# Gelişmiş arama parametreleri
search_params = SearchParams()
search_params.add_where_clause(contains("name", "John"))
search_params.add_where_clause(equals("doNotCall", False))
search_params.set_order("createdAt", "desc")
search_params.set_pagination(0, 10)

response = client.relationships.list_related(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    search_params=search_params
)
```

## Link Operasyonları

### Tek Kayıt İlişkilendirme

```python
# Account'a tek Contact ilişkilendir
result = client.relationships.link_single(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_id="507f1f77bcf86cd799439012"
)

if result.success:
    print("✅ İlişkilendirme başarılı")
else:
    print("❌ İlişkilendirme başarısız")
    for error in result.errors:
        print(f"Hata: {error}")
```

### Çoklu Kayıt İlişkilendirme

```python
# Account'a birden fazla Contact ilişkilendir
contact_ids = [
    "507f1f77bcf86cd799439012",
    "507f1f77bcf86cd799439013",
    "507f1f77bcf86cd799439014"
]

result = client.relationships.link_multiple(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_ids=contact_ids
)

print(f"Başarı oranı: {result.get_success_rate():.1f}%")
print(f"Başarılı: {result.successful_count}/{result.target_count}")
```

## Unlink Operasyonları

### Tek Kayıt İlişki Kaldırma

```python
# Account'tan tek Contact ilişkisini kaldır
result = client.relationships.unlink_single(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_id="507f1f77bcf86cd799439012"
)
```

### Çoklu Kayıt İlişki Kaldırma

```python
# Account'tan birden fazla Contact ilişkisini kaldır
contact_ids = ["507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"]

result = client.relationships.unlink_multiple(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_ids=contact_ids
)
```

### Tüm İlişkileri Kaldırma

```python
# Account'un tüm Contact ilişkilerini kaldır
result = client.relationships.unlink_all(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts"
)

print(f"Kaldırılan ilişki sayısı: {result.successful_count}")
```

## Mass Relate

Mass relate operasyonu, search criteria'ya uyan tüm kayıtları toplu olarak ilişkilendirir.

```python
# Belirli kriterlere uyan tüm Contact'ları Account'a ilişkilendir
where_criteria = [
    {
        "type": "equals",
        "attribute": "accountId",
        "value": None  # Account'a bağlı olmayan Contact'lar
    },
    {
        "type": "contains",
        "attribute": "emailAddress",
        "value": "@company.com"  # Belirli domain'den Contact'lar
    }
]

result = client.relationships.mass_relate(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    where=where_criteria
)

print(f"Etkilenen kayıt sayısı: {result.successful_count}")
```

## Request Modelleri

### LinkRequest

[`LinkRequest`](../espocrm/models/requests.py:42) sınıfı link operasyonları için kullanılır:

```python
from espocrm.models.requests import create_link_request

# Tek kayıt için LinkRequest
link_request = create_link_request(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_id="507f1f77bcf86cd799439012"
)

print(f"Endpoint: {link_request.get_endpoint()}")
print(f"Link türü: {link_request.get_link_type()}")
print(f"API data: {link_request.to_api_dict()}")
```

### UnlinkRequest

[`UnlinkRequest`](../espocrm/models/requests.py:200) sınıfı unlink operasyonları için kullanılır:

```python
from espocrm.models.requests import create_unlink_request

# Tek kayıt için UnlinkRequest
unlink_request = create_unlink_request(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_id="507f1f77bcf86cd799439012"
)

print(f"Unlink türü: {unlink_request.get_unlink_type()}")
```

### RelationshipListRequest

[`RelationshipListRequest`](../espocrm/models/requests.py:280) sınıfı ilişkili kayıtları listeleme için kullanılır:

```python
from espocrm.models.requests import create_relationship_list_request

# Liste request'i
list_request = create_relationship_list_request(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    max_size=20,
    order_by="name"
)

params = list_request.to_query_params()
```

## Entity Helper Methods

Entity sınıfları relationship yönetimi için helper metodlar sağlar.

### EntityRecord Base Methods

```python
from espocrm.models import Account

# Account entity'si oluştur
account_data = {
    "id": "507f1f77bcf86cd799439011",
    "name": "Test Company",
    "contacts": [
        {"id": "507f1f77bcf86cd799439012", "name": "John Doe"},
        {"id": "507f1f77bcf86cd799439013", "name": "Jane Smith"}
    ]
}

account = Account.create_from_dict(account_data)

# Relationship helper methods
contact_ids = account.get_relationship_ids("contacts")
contact_names = account.get_relationship_names("contacts")
has_contact = account.has_relationship("contacts", "507f1f77bcf86cd799439012")
contact_count = account.get_relationship_count("contacts")

print(f"Contact ID'leri: {contact_ids}")
print(f"Contact isimleri: {contact_names}")
print(f"John Doe var mı: {has_contact}")
print(f"Contact sayısı: {contact_count}")
```

### Account-Specific Methods

```python
# Account'a özel relationship methods
account = Account.create_from_dict(account_data)

# Contact methods
contact_ids = account.get_contact_ids()
contact_names = account.get_contact_names()
has_contact = account.has_contact("507f1f77bcf86cd799439012")

# Opportunity methods
opportunity_ids = account.get_opportunity_ids()
has_opportunity = account.has_opportunity("507f1f77bcf86cd799439020")

# Case methods
case_ids = account.get_case_ids()
has_case = account.has_case("507f1f77bcf86cd799439030")
```

### Contact-Specific Methods

```python
from espocrm.models import Contact

contact = Contact.create_from_dict(contact_data)

# Account relationship
account_id = contact.get_account_id()
account_name = contact.get_account_name()
has_account = contact.has_account()

# Team relationships
team_ids = contact.get_team_ids()
team_names = contact.get_team_names()
has_team = contact.has_team("507f1f77bcf86cd799439040")
```

## Convenience Methods

Ana client convenience methods sağlar:

```python
# İlişkili entity'leri listele
response = client.list_related_entities(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts"
)

# Entity'leri ilişkilendir (tek veya çoklu)
result = client.link_entities(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_ids=["507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"]
)

# İlişkileri kaldır
result = client.unlink_entities(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_ids=["507f1f77bcf86cd799439012"]
)

# Mass relate
result = client.mass_relate_entities(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    where=[{"type": "equals", "attribute": "accountId", "value": None}]
)

# İlişki kontrolü
exists = client.check_entity_relationship(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_id="507f1f77bcf86cd799439012"
)
```

### Specific Entity Convenience Methods

```python
# Account-Contact ilişkileri
result = client.relationships.link_account_contacts(
    account_id="507f1f77bcf86cd799439011",
    contact_ids=["507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"]
)

result = client.relationships.unlink_account_contacts(
    account_id="507f1f77bcf86cd799439011",
    contact_ids=["507f1f77bcf86cd799439012"]
)

# Account-Opportunity ilişkileri
result = client.relationships.link_account_opportunities(
    account_id="507f1f77bcf86cd799439011",
    opportunity_ids="507f1f77bcf86cd799439020"
)

# Contact-Team ilişkileri
result = client.relationships.link_contact_teams(
    contact_id="507f1f77bcf86cd799439012",
    team_ids=["507f1f77bcf86cd799439040"]
)
```

## Hata Yönetimi

### RelationshipOperationResult

Tüm relationship operasyonları [`RelationshipOperationResult`](../espocrm/clients/relationships.py:17) döndürür:

```python
result = client.relationships.link_single(
    entity_type="Account",
    entity_id="507f1f77bcf86cd799439011",
    link="contacts",
    target_id="507f1f77bcf86cd799439012"
)

# Sonuç kontrolü
if result.success:
    print("✅ Operasyon başarılı")
    print(f"Özet: {result.get_summary()}")
else:
    print("❌ Operasyon başarısız")
    print(f"Başarı oranı: {result.get_success_rate():.1f}%")
    
    if result.has_errors():
        print("Hatalar:")
        for error in result.errors:
            print(f"  - {error}")

# Detaylı bilgiler
print(f"Operasyon türü: {result.operation_type}")
print(f"Entity: {result.entity_type}/{result.entity_id}")
print(f"Link: {result.link}")
print(f"Hedef sayısı: {result.target_count}")
print(f"Başarılı: {result.successful_count}")
print(f"Başarısız: {result.failed_count}")
```

### Exception Handling

```python
try:
    result = client.relationships.link_single(
        entity_type="Account",
        entity_id="invalid-id",
        link="contacts",
        target_id="507f1f77bcf86cd799439012"
    )
except EspoCRMValidationError as e:
    print(f"Validation hatası: {e}")
except EspoCRMError as e:
    print(f"API hatası: {e}")
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
```

## Örnekler

### Tam Workflow Örneği

```python
from espocrm import EspoCRMClient, ClientConfig
from espocrm.auth import APIKeyAuth
from espocrm.models import SearchParams, equals

# Client setup
config = ClientConfig(base_url="https://your-espocrm.com")
auth = APIKeyAuth(api_key="your-api-key")

with EspoCRMClient(config.base_url, auth, config) as client:
    account_id = "507f1f77bcf86cd799439011"
    
    # 1. Mevcut Contact'ları listele
    print("Mevcut Contact'lar:")
    response = client.relationships.list_related(
        entity_type="Account",
        entity_id=account_id,
        link="contacts",
        select=["id", "name", "emailAddress"]
    )
    
    for contact in response.get_entities():
        print(f"  - {contact.name} ({contact.email_address})")
    
    # 2. Yeni Contact'ları ilişkilendir
    new_contact_ids = ["507f1f77bcf86cd799439020", "507f1f77bcf86cd799439021"]
    
    result = client.relationships.link_multiple(
        entity_type="Account",
        entity_id=account_id,
        link="contacts",
        target_ids=new_contact_ids
    )
    
    print(f"\nYeni Contact'lar eklendi: {result.get_summary()}")
    
    # 3. Güncellenmiş listeyi kontrol et
    response = client.relationships.list_related(
        entity_type="Account",
        entity_id=account_id,
        link="contacts"
    )
    
    print(f"Toplam Contact sayısı: {response.total}")
    
    # 4. Belirli bir Contact'ın varlığını kontrol et
    exists = client.relationships.check_relationship_exists(
        entity_type="Account",
        entity_id=account_id,
        link="contacts",
        target_id="507f1f77bcf86cd799439020"
    )
    
    print(f"Contact 507f1f77bcf86cd799439020 var mı: {exists}")
```

### Metadata ve Relationship Bilgileri

```python
# Entity'nin tüm relationship'lerini öğren
metadata = client.relationships.get_relationship_metadata(
    entity_type="Account"
)

print("Account Relationship'leri:")
for link_name, link_info in metadata.items():
    print(f"  - {link_name}: {link_info.get('type')} -> {link_info.get('entity')}")

# Belirli bir link hakkında detaylı bilgi
contact_link_info = client.relationships.get_relationship_metadata(
    entity_type="Account",
    link="contacts"
)

print(f"Contacts link bilgisi: {contact_link_info}")
```

Bu dokümantasyon EspoCRM Python Client'ının relationship yönetimi özelliklerinin kapsamlı bir rehberini sağlar. Daha fazla örnek için [`examples/relationship_example.py`](../examples/relationship_example.py) dosyasına bakabilirsiniz.