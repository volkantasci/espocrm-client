# EspoCRM CRUD Operasyonları

Bu dokümantasyon EspoCRM Python API istemcisinin CRUD (Create, Read, Update, Delete) operasyonlarını ve gelişmiş arama özelliklerini açıklar.

## İçindekiler

- [Temel CRUD Operasyonları](#temel-crud-operasyonları)
- [Arama Parametreleri](#arama-parametreleri)
- [Entity Modelleri](#entity-modelleri)
- [Bulk Operasyonlar](#bulk-operasyonlar)
- [Entity-Specific Metodlar](#entity-specific-metodlar)
- [Örnekler](#örnekler)

## Temel CRUD Operasyonları

### Create (Oluşturma)

Yeni entity kayıtları oluşturmak için:

```python
from espocrm import EspoCRMClient, APIKeyAuth

# Client oluştur
client = EspoCRMClient("https://your-espocrm.com", APIKeyAuth("your-api-key"))

# Yeni Account oluştur
account_data = {
    "name": "Test Şirketi",
    "website": "https://test.com",
    "type": "Customer"
}

response = client.create_entity("Account", account_data)
account_id = response.get_id()
print(f"Oluşturulan Account ID: {account_id}")

# CRUD client üzerinden de yapılabilir
response = client.crud.create("Account", account_data)
```

### Read (Okuma)

Mevcut entity kayıtlarını okumak için:

```python
# ID ile entity oku
response = client.get_entity("Account", account_id)
account = response.get_entity()
print(f"Account adı: {account.name}")

# Sadece belirli field'ları seç
response = client.get_entity("Account", account_id, select=["name", "website"])

# Entity sınıfı ile type-safe okuma
from espocrm import Account
response = client.get_entity("Account", account_id)
account = response.get_entity(Account)
print(f"Website: {account.website}")
```

### Update (Güncelleme)

Mevcut entity kayıtlarını güncellemek için:

```python
# Partial update (varsayılan)
update_data = {
    "website": "https://yeni-site.com",
    "description": "Güncellenmiş açıklama"
}

response = client.update_entity("Account", account_id, update_data)

# Full update
response = client.update_entity("Account", account_id, full_data, partial=False)
```

### Delete (Silme)

Entity kayıtlarını silmek için:

```python
# Entity sil
success = client.delete_entity("Account", account_id)
if success:
    print("Account başarıyla silindi")
```

### List (Listeleme)

Entity listelerini getirmek için:

```python
# Basit listeleme
response = client.list_entities("Account", max_size=10)
print(f"Toplam Account sayısı: {response.total}")

accounts = response.get_entities()
for account in accounts:
    print(f"- {account.name}")
```

## Arama Parametreleri

EspoCRM'in güçlü arama özelliklerini kullanmak için `SearchParams` sınıfını kullanın:

### Temel Arama

```python
from espocrm import SearchParams

# SearchParams oluştur
search = SearchParams()
search.add_contains("name", "Test")
search.add_equals("type", "Customer")
search.set_pagination(0, 20)
search.set_order("createdAt", "desc")

# Arama yap
results = client.search_entities("Account", search)
```

### Where Operatörleri

EspoCRM'in tüm where operatörleri desteklenir:

```python
from espocrm import SearchParams, equals, contains, greater_than, in_list

search = SearchParams()

# Eşitlik kontrolü
search.add_equals("type", "Customer")
search.add_not_equals("industry", "")

# String operatörleri
search.add_contains("name", "Tech")
search.add_starts_with("name", "A")
search.add_ends_with("website", ".com")

# Sayısal karşılaştırma
search.add_greater_than("amount", 10000)
search.add_less_than("probability", 50)

# Liste operatörleri
search.add_in("type", ["Customer", "Partner"])
search.add_not_in("status", ["Inactive"])

# Null kontrolleri
search.add_is_null("description")
search.add_is_not_null("emailAddress")

# Tarih operatörleri
search.add_today("createdAt")
search.add_past("closeDate")
search.add_future("dueDate")

# Aralık kontrolü
search.add_between("amount", 1000, 50000)
```

### Convenience Functions

Daha kısa syntax için convenience functions kullanın:

```python
from espocrm import create_search_params, equals, contains, greater_than

# Hızlı arama oluştur
search = create_search_params(max_size=50)
search.add_where_clause(equals("type", "Customer"))
search.add_where_clause(contains("name", "Tech"))
search.add_where_clause(greater_than("amount", 5000))

results = client.search_entities("Account", search)
```

## Entity Modelleri

Type-safe entity işlemleri için önceden tanımlanmış entity sınıfları:

### Account

```python
from espocrm import Account

# Account oluştur
account = Account(
    name="Test Şirketi",
    website="https://test.com",
    phone_number="+90 212 555 0123",
    email_address="info@test.com",
    type="Customer",
    industry="Technology"
)

# API'ye gönder
response = client.create_entity("Account", account)

# Response'dan Account al
account_response = client.get_entity("Account", account_id)
account = account_response.get_entity(Account)

# Account metodları
print(account.get_full_address("billing"))
print(account.get_display_name())
```

### Contact

```python
from espocrm import Contact

contact = Contact(
    first_name="Ahmet",
    last_name="Yılmaz",
    email_address="ahmet@test.com",
    account_id=account_id,
    title="Yazılım Geliştirici"
)

response = client.create_entity("Contact", contact)

# Contact metodları
contact = response.get_entity(Contact)
print(contact.get_full_name())
print(contact.get_full_address())
```

### Lead

```python
from espocrm import Lead

lead = Lead(
    first_name="Mehmet",
    last_name="Demir",
    email_address="mehmet@lead.com",
    account_name="Lead Şirketi",
    status="New",
    source="Website"
)

response = client.create_entity("Lead", lead)

# Lead metodları
lead = response.get_entity(Lead)
print(lead.get_full_name())
print(f"Converted: {lead.is_converted()}")
```

### Opportunity

```python
from espocrm import Opportunity

opportunity = Opportunity(
    name="Test Opportunity",
    account_id=account_id,
    stage="Prospecting",
    amount=50000.0,
    probability=25
)

response = client.create_entity("Opportunity", opportunity)

# Opportunity metodları
opp = response.get_entity(Opportunity)
print(f"Weighted amount: {opp.get_weighted_amount()}")
print(f"Is won: {opp.is_won()}")
print(f"Is closed: {opp.is_closed()}")
```

### Dynamic Fields

EspoCRM'deki custom field'lar için dynamic field desteği:

```python
# Dynamic field ayarla
account.set_dynamic_field("customField", "custom value")

# Dynamic field oku
value = account.get_dynamic_field("customField")

# Tüm dynamic field'ları al
dynamic_fields = account.get_dynamic_fields()
```

## Bulk Operasyonlar

Çoklu kayıtlar üzerinde işlem yapmak için:

### Bulk Create

```python
# Çoklu Account oluştur
accounts_data = [
    {"name": f"Şirket {i}", "type": "Customer"}
    for i in range(1, 11)
]

result = client.crud.bulk_create("Account", accounts_data)
print(f"Başarılı: {result.successful}/{result.total}")

# Başarılı ID'leri al
created_ids = result.get_successful_ids()
```

### Bulk Update

```python
# Çoklu güncelleme
updates = [
    {"id": account_id, "description": "Bulk güncellenmiş"}
    for account_id in created_ids
]

result = client.crud.bulk_update("Account", updates)
print(f"Güncellenen: {result.successful}/{result.total}")
```

### Bulk Delete

```python
# Çoklu silme
result = client.crud.bulk_delete("Account", created_ids)
print(f"Silinen: {result.successful}/{result.total}")
```

## Entity-Specific Metodlar

Her entity türü için özel metodlar:

### Account Metodları

```python
# Account-specific metodlar
account_response = client.crud.get_account(account_id)
account_response = client.crud.create_account(account_data)
accounts_response = client.crud.list_accounts(search_params)
```

### Contact Metodları

```python
# Contact-specific metodlar
contact_response = client.crud.get_contact(contact_id)
contact_response = client.crud.create_contact(contact_data)
contacts_response = client.crud.list_contacts(search_params)
```

### Lead Metodları

```python
# Lead-specific metodlar
lead_response = client.crud.get_lead(lead_id)
lead_response = client.crud.create_lead(lead_data)
leads_response = client.crud.list_leads(search_params)
```

### Opportunity Metodları

```python
# Opportunity-specific metodlar
opp_response = client.crud.get_opportunity(opp_id)
opp_response = client.crud.create_opportunity(opp_data)
opps_response = client.crud.list_opportunities(search_params)
```

## Utility Metodlar

### Count

```python
# Entity sayısını al
total_accounts = client.count_entities("Account")
customer_accounts = client.count_entities("Account", where=[
    {"type": "equals", "attribute": "type", "value": "Customer"}
])
```

### Exists

```python
# Entity var mı kontrol et
exists = client.entity_exists("Account", account_id)
if exists:
    print("Account mevcut")
```

## Response Handling

### Entity Response

```python
response = client.get_entity("Account", account_id)

# Response bilgileri
print(f"Success: {response.success}")
print(f"Entity Type: {response.entity_type}")
print(f"Entity ID: {response.get_id()}")
print(f"Entity Name: {response.get_name()}")

# Entity al
account = response.get_entity(Account)
```

### List Response

```python
response = client.list_entities("Account", max_size=10)

# Liste bilgileri
print(f"Total: {response.total}")
print(f"Count: {len(response.list)}")
print(f"Has more: {response.has_more()}")

# Sayfa bilgileri
page_info = response.get_page_info()
print(f"Current page: {page_info['current_page']}")
print(f"Total pages: {page_info['total_pages']}")

# Entity'leri al
accounts = response.get_entities(Account)
```

### Bulk Operation Result

```python
result = client.crud.bulk_create("Account", accounts_data)

# Sonuç bilgileri
print(f"Success: {result.success}")
print(f"Total: {result.total}")
print(f"Successful: {result.successful}")
print(f"Failed: {result.failed}")
print(f"Success rate: {result.get_success_rate():.1f}%")

# Başarılı ID'ler
successful_ids = result.get_successful_ids()

# Başarısız işlemler
failed_results = result.get_failed_results()
```

## Error Handling

```python
from espocrm import EspoCRMError, EspoCRMValidationError, EspoCRMNotFoundError

try:
    response = client.get_entity("Account", "invalid-id")
except EspoCRMNotFoundError:
    print("Account bulunamadı")
except EspoCRMValidationError as e:
    print(f"Validation hatası: {e}")
except EspoCRMError as e:
    print(f"API hatası: {e}")
```

## Performans İpuçları

### Pagination

```python
# Büyük listeler için pagination kullanın
offset = 0
max_size = 100

while True:
    search = SearchParams()
    search.set_pagination(offset, max_size)
    
    response = client.list_entities("Account", search_params=search)
    
    # İşlem yap
    accounts = response.get_entities()
    for account in accounts:
        # Process account
        pass
    
    # Daha fazla kayıt var mı?
    if not response.has_more():
        break
    
    offset += max_size
```

### Field Selection

```python
# Sadece gerekli field'ları seçin
response = client.list_entities(
    "Account", 
    select=["id", "name", "website"]
)
```

### Bulk Operations

```python
# Tek tek işlem yerine bulk kullanın
# ❌ Yavaş
for account_data in accounts_data:
    client.create_entity("Account", account_data)

# ✅ Hızlı
result = client.crud.bulk_create("Account", accounts_data)
```

## Tam Örnek

Tam bir CRUD örneği için `examples/crud_example.py` dosyasına bakın.

```python
from espocrm import (
    EspoCRMClient, APIKeyAuth, ClientConfig,
    SearchParams, Account, Contact, equals, contains
)

# Client setup
config = ClientConfig(base_url="https://your-espocrm.com")
auth = APIKeyAuth("your-api-key")

with EspoCRMClient(config.base_url, auth, config) as client:
    # Account oluştur
    account_data = {
        "name": "Test Şirketi",
        "website": "https://test.com",
        "type": "Customer"
    }
    
    account_response = client.create_entity("Account", account_data)
    account_id = account_response.get_id()
    
    # Contact oluştur
    contact_data = {
        "firstName": "Ahmet",
        "lastName": "Yılmaz",
        "accountId": account_id,
        "emailAddress": "ahmet@test.com"
    }
    
    contact_response = client.create_entity("Contact", contact_data)
    
    # Arama yap
    search = SearchParams()
    search.add_equals("type", "Customer")
    search.add_contains("name", "Test")
    
    results = client.search_entities("Account", search)
    
    print(f"Bulunan Account sayısı: {results.total}")
```

Bu dokümantasyon EspoCRM CRUD operasyonlarının temel kullanımını kapsar. Daha detaylı örnekler ve gelişmiş kullanım için örnek dosyalara bakın.