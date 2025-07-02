# EspoCRM Stream API

EspoCRM Stream API, kullanıcı aktivitelerini takip etmek, stream'leri görüntülemek ve stream'e post yapmak için kullanılır. Bu dokümantasyon EspoCRM Python Client'ın stream özelliklerini açıklar.

## İçindekiler

- [Temel Kullanım](#temel-kullanım)
- [Stream Listeleme](#stream-listeleme)
- [Stream'e Post Yapma](#streame-post-yapma)
- [Entity Follow/Unfollow](#entity-followunfollow)
- [Stream Filtering](#stream-filtering)
- [Attachment Desteği](#attachment-desteği)
- [Entity Helper Methods](#entity-helper-methods)
- [Stream Note Türleri](#stream-note-türleri)
- [Hata Yönetimi](#hata-yönetimi)
- [İleri Düzey Kullanım](#ileri-düzey-kullanım)

## Temel Kullanım

```python
from espocrm import EspoCRMClient, ClientConfig
from espocrm.auth import APIKeyAuth
from espocrm.models.stream import StreamNoteType

# Client oluştur
config = ClientConfig(base_url="https://your-espocrm.com")
auth = APIKeyAuth(api_key="your-api-key")

with EspoCRMClient(config.base_url, auth, config) as client:
    # Stream client'a erişim
    stream_client = client.stream
    
    # Veya doğrudan client üzerinden
    stream_notes = client.get_user_stream()
```

## Stream Listeleme

### User Stream

Kullanıcının takip ettiği tüm aktiviteleri listeler:

```python
# Basit user stream
stream_notes = client.stream.list_user_stream(
    max_size=20,
    offset=0
)

# Filtrelenmiş user stream
filtered_stream = client.stream.list_user_stream(
    max_size=10,
    note_types=[StreamNoteType.POST, StreamNoteType.CREATE],
    after="2024-01-01T00:00:00Z"
)

# Belirli kullanıcının aktiviteleri
user_activities = client.stream.list_user_stream(
    user_id="user_id_here",
    max_size=15
)
```

### Entity Stream

Belirli bir entity'nin stream'ini listeler:

```python
# Account stream'i
account_stream = client.stream.list_entity_stream(
    entity_type="Account",
    entity_id="account_id_here",
    max_size=10
)

# Convenience methods
account_stream = client.stream.get_account_stream("account_id_here")
contact_stream = client.stream.get_contact_stream("contact_id_here")
opportunity_stream = client.stream.get_opportunity_stream("opportunity_id_here")
lead_stream = client.stream.get_lead_stream("lead_id_here")
```

## Stream'e Post Yapma

### Basit Post

```python
# Temel post
stream_note = client.stream.post_to_stream(
    parent_type="Account",
    parent_id="account_id_here",
    post="Bu bir test post'udur."
)

print(f"Post oluşturuldu: {stream_note.id}")
```

### HTML İçerikli Post

```python
html_content = """
<p><strong>Proje Güncellemesi</strong></p>
<ul>
    <li>Milestone 1 tamamlandı</li>
    <li>Milestone 2 başlatıldı</li>
    <li>Takım toplantısı planlandı</li>
</ul>
<p><em>Detaylar için lütfen iletişime geçin.</em></p>
"""

stream_note = client.stream.post_to_stream(
    parent_type="Account",
    parent_id="account_id_here",
    post=html_content
)
```

### Attachment ile Post

```python
# Önce attachment'ları upload edin (Attachment API ile)
attachment_ids = ["attachment_id_1", "attachment_id_2"]

stream_note = client.stream.post_to_stream(
    parent_type="Account",
    parent_id="account_id_here",
    post="Dosyalar ekte bulunmaktadır.",
    attachments_ids=attachment_ids
)

print(f"Attachment sayısı: {stream_note.get_attachment_count()}")
```

### Internal Note

```python
# Sadece internal kullanıcılara görünür
internal_note = client.stream.post_to_stream(
    parent_type="Account",
    parent_id="account_id_here",
    post="Bu bir internal note'dur.",
    is_internal=True
)
```

### Team Kısıtlamalı Post

```python
# Sadece belirli team'lere görünür
team_note = client.stream.post_to_stream(
    parent_type="Account",
    parent_id="account_id_here",
    post="Bu post sadece sales team'e görünür.",
    teams_ids=["sales_team_id", "management_team_id"]
)
```

### Convenience Methods

```python
# Entity-specific post methods
client.stream.post_to_account("account_id", "Account post")
client.stream.post_to_contact("contact_id", "Contact post")
client.stream.post_to_opportunity("opportunity_id", "Opportunity post")
client.stream.post_to_lead("lead_id", "Lead post")
```

## Entity Follow/Unfollow

### Follow İşlemleri

```python
# Entity'yi takip et
success = client.stream.follow_entity("Account", "account_id_here")
if success:
    print("Account başarıyla takip edildi")

# Follow durumunu kontrol et
is_following = client.stream.is_following_entity("Account", "account_id_here")
print(f"Takip durumu: {is_following}")

# Takibi bırak
success = client.stream.unfollow_entity("Account", "account_id_here")
if success:
    print("Account takibi bırakıldı")
```

### Convenience Methods

```python
# Entity-specific follow methods
client.stream.follow_account("account_id")
client.stream.follow_contact("contact_id")
client.stream.follow_opportunity("opportunity_id")
client.stream.follow_lead("lead_id")

# Unfollow methods
client.stream.unfollow_account("account_id")
client.stream.unfollow_contact("contact_id")
client.stream.unfollow_opportunity("opportunity_id")
client.stream.unfollow_lead("lead_id")
```

## Stream Filtering

### Note Type Filtering

```python
from espocrm.models.stream import StreamNoteType

# Sadece post'lar
posts = client.stream.list_user_stream(
    note_types=[StreamNoteType.POST]
)

# Sistem aktiviteleri
system_notes = client.stream.list_user_stream(
    note_types=[
        StreamNoteType.CREATE,
        StreamNoteType.UPDATE,
        StreamNoteType.STATUS,
        StreamNoteType.ASSIGN
    ]
)

# Email aktiviteleri
email_notes = client.stream.list_user_stream(
    note_types=[
        StreamNoteType.EMAIL_RECEIVED,
        StreamNoteType.EMAIL_SENT
    ]
)
```

### Tarih Filtering

```python
from datetime import datetime, timedelta

# Son 7 günün aktiviteleri
week_ago = (datetime.now() - timedelta(days=7)).isoformat()
recent_notes = client.stream.list_user_stream(
    after=week_ago,
    max_size=50
)

# Belirli tarihten sonraki aktiviteler
specific_date = "2024-01-01T00:00:00Z"
filtered_notes = client.stream.list_user_stream(
    after=specific_date
)
```

### Kullanıcı Filtering

```python
# Belirli kullanıcının aktiviteleri
user_notes = client.stream.list_user_stream(
    user_id="specific_user_id",
    max_size=20
)
```

## Attachment Desteği

### Attachment Bilgileri

```python
# Stream note'un attachment bilgilerini kontrol et
stream_note = client.stream.get_stream_note("note_id_here")

if stream_note.has_attachments():
    print(f"Attachment sayısı: {stream_note.get_attachment_count()}")
    
    # Attachment ID'leri
    if stream_note.attachments_ids:
        for attachment_id in stream_note.attachments_ids:
            print(f"Attachment ID: {attachment_id}")
    
    # Attachment isimleri
    if stream_note.attachments_names:
        for att_id, att_name in stream_note.attachments_names.items():
            print(f"Attachment: {att_name} (ID: {att_id})")
    
    # Attachment türleri
    if stream_note.attachments_types:
        for att_id, att_type in stream_note.attachments_types.items():
            print(f"Type: {att_type} (ID: {att_id})")
```

### Attachment Upload

```python
# Not: Attachment upload için ayrı Attachment API kullanılır
# Bu örnek upload edilmiş attachment'ların kullanımını gösterir

# 1. Önce dosyaları upload edin (Attachment API ile)
# uploaded_attachments = client.attachments.upload_files([
#     "path/to/file1.pdf",
#     "path/to/file2.xlsx"
# ])

# 2. Upload edilen attachment ID'lerini kullanın
# attachment_ids = [att["id"] for att in uploaded_attachments]

# 3. Stream post'unda kullanın
# stream_note = client.stream.post_to_stream(
#     parent_type="Account",
#     parent_id="account_id",
#     post="Dosyalar ekte",
#     attachments_ids=attachment_ids
# )
```

## Entity Helper Methods

Entity modelleri üzerinden doğrudan stream operasyonları:

```python
from espocrm.models.entities import Account

# Account entity'si oluştur
account_data = client.crud.read("Account", "account_id_here")
account = Account.from_api_response(account_data)

# Entity helper methods
# Stream getir
stream_notes = account.get_stream(client, max_size=10)

# Post yap
post_note = account.post_to_stream(client, "Entity helper ile post")

# Takip et
follow_result = account.follow(client)

# Takip durumunu kontrol et
is_followed = account.is_followed(client)

# Takibi bırak
unfollow_result = account.unfollow(client)
```

## Stream Note Türleri

### Mevcut Note Türleri

```python
from espocrm.models.stream import StreamNoteType

# Kullanıcı aktiviteleri
StreamNoteType.POST           # Kullanıcı post'u
StreamNoteType.CREATE         # Kayıt oluşturma
StreamNoteType.UPDATE         # Kayıt güncelleme
StreamNoteType.STATUS         # Durum değişikliği
StreamNoteType.ASSIGN         # Atama değişikliği

# İlişki aktiviteleri
StreamNoteType.RELATE         # İlişki oluşturma
StreamNoteType.UNRELATE       # İlişki kaldırma

# Email aktiviteleri
StreamNoteType.EMAIL_RECEIVED # Email alma
StreamNoteType.EMAIL_SENT     # Email gönderme

# Diğer aktiviteler
StreamNoteType.CALL_MADE      # Arama yapma
StreamNoteType.CALL_RECEIVED  # Arama alma
StreamNoteType.MEETING_HELD   # Toplantı yapma
StreamNoteType.TASK_COMPLETED # Görev tamamlama
```

### Note Type Kontrolü

```python
stream_note = client.stream.get_stream_note("note_id")

# Note türü kontrolü
if stream_note.is_post_type():
    print("Bu bir kullanıcı post'u")
    print(f"İçerik: {stream_note.get_display_text()}")

if stream_note.is_system_note():
    print("Bu bir sistem notu")
    print(f"Aktivite: {stream_note.get_display_text()}")

# Specific type kontrolü
if stream_note.type == StreamNoteType.CREATE:
    print("Yeni kayıt oluşturuldu")
elif stream_note.type == StreamNoteType.UPDATE:
    print("Kayıt güncellendi")
    # Update data'sına erişim
    if stream_note.data and stream_note.data.fields:
        print("Değişen alanlar:", stream_note.data.fields)
```

## Hata Yönetimi

### Yaygın Hatalar

```python
from espocrm.exceptions import EspoCRMError, EspoCRMValidationError

try:
    # Stream operasyonu
    stream_notes = client.stream.list_user_stream()
    
except EspoCRMValidationError as e:
    print(f"Validation hatası: {e}")
    # Geçersiz parametreler
    
except EspoCRMError as e:
    print(f"API hatası: {e}")
    # API seviyesinde hata
    
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
```

### Validation Hataları

```python
try:
    # Geçersiz post içeriği
    client.stream.post_to_stream(
        parent_type="Account",
        parent_id="invalid_id",  # Geçersiz ID formatı
        post=""  # Boş içerik
    )
    
except EspoCRMValidationError as e:
    print(f"Validation hatası: {e}")
    # - Parent ID 17 karakter olmalı
    # - Post içeriği boş olamaz
```

## İleri Düzey Kullanım

### Pagination ile Stream Listeleme

```python
def get_all_stream_notes(client, entity_type, entity_id, batch_size=50):
    """Tüm stream note'ları pagination ile getirir."""
    all_notes = []
    offset = 0
    
    while True:
        batch = client.stream.list_entity_stream(
            entity_type=entity_type,
            entity_id=entity_id,
            offset=offset,
            max_size=batch_size
        )
        
        if not batch:
            break
            
        all_notes.extend(batch)
        offset += batch_size
        
        # Güvenlik için maksimum limit
        if len(all_notes) >= 1000:
            break
    
    return all_notes
```

### Stream Note Analizi

```python
def analyze_stream_notes(stream_notes):
    """Stream note'ları analiz eder."""
    analysis = {
        "total": len(stream_notes),
        "by_type": {},
        "with_attachments": 0,
        "with_mentions": 0,
        "internal_notes": 0
    }
    
    for note in stream_notes:
        # Type analizi
        note_type = note.type.value
        analysis["by_type"][note_type] = analysis["by_type"].get(note_type, 0) + 1
        
        # Attachment analizi
        if note.has_attachments():
            analysis["with_attachments"] += 1
        
        # Mention analizi
        if note.has_mentions():
            analysis["with_mentions"] += 1
        
        # Internal note analizi
        if note.is_internal:
            analysis["internal_notes"] += 1
    
    return analysis

# Kullanım
stream_notes = client.stream.list_user_stream(max_size=100)
analysis = analyze_stream_notes(stream_notes)
print(f"Analiz sonuçları: {analysis}")
```

### Bulk Follow Operations

```python
def bulk_follow_entities(client, entity_list):
    """Çoklu entity'leri takip eder."""
    results = []
    
    for entity_type, entity_id in entity_list:
        try:
            success = client.stream.follow_entity(entity_type, entity_id)
            results.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "success": success
            })
        except Exception as e:
            results.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "success": False,
                "error": str(e)
            })
    
    return results

# Kullanım
entities_to_follow = [
    ("Account", "account_id_1"),
    ("Contact", "contact_id_1"),
    ("Opportunity", "opportunity_id_1")
]

results = bulk_follow_entities(client, entities_to_follow)
for result in results:
    if result["success"]:
        print(f"✅ {result['entity_type']} takip edildi")
    else:
        print(f"❌ {result['entity_type']} takip edilemedi: {result.get('error')}")
```

### Stream Note Yönetimi

```python
# Stream note getir
stream_note = client.stream.get_stream_note("note_id_here")

# Stream note sil (sadece kendi post'larınızı silebilirsiniz)
success = client.stream.delete_stream_note("note_id_here")
if success:
    print("Stream note silindi")

# Stream note bilgilerini göster
def display_stream_note(note):
    print(f"ID: {note.id}")
    print(f"Type: {note.type.value}")
    print(f"Created: {note.created_at}")
    print(f"Author: {note.created_by_name}")
    
    if note.is_post_type():
        print(f"Content: {note.get_display_text()}")
    else:
        print(f"Activity: {note.get_display_text()}")
    
    if note.has_attachments():
        print(f"Attachments: {note.get_attachment_count()}")
    
    if note.has_mentions():
        mentioned_users = note.get_mentioned_user_names()
        print(f"Mentions: {', '.join(mentioned_users)}")

# Kullanım
display_stream_note(stream_note)
```

## Örnek Kullanım Senaryoları

### 1. Müşteri Aktivite Takibi

```python
def track_customer_activity(client, account_id):
    """Müşteri aktivitelerini takip eder."""
    
    # Account'u takip et
    client.stream.follow_account(account_id)
    
    # Son aktiviteleri getir
    activities = client.stream.get_account_stream(
        account_id=account_id,
        max_size=20
    )
    
    print(f"Son {len(activities)} aktivite:")
    for activity in activities:
        print(f"- {activity.type.value}: {activity.get_display_text()}")
    
    # Önemli güncelleme post'u
    client.stream.post_to_account(
        account_id=account_id,
        post="Müşteri takip sistemi aktif edildi."
    )
```

### 2. Proje Durumu Güncelleme

```python
def update_project_status(client, opportunity_id, status_update):
    """Proje durumu günceller."""
    
    html_update = f"""
    <p><strong>Proje Durumu Güncellendi</strong></p>
    <p>{status_update}</p>
    <p><em>Güncelleme tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>
    """
    
    # Opportunity'ye post yap
    stream_note = client.stream.post_to_opportunity(
        opportunity_id=opportunity_id,
        post=html_update
    )
    
    print(f"Proje durumu güncellendi: {stream_note.id}")
    
    # Takım üyelerini bilgilendir
    # (Gerçek kullanımda mention özelliği kullanılabilir)
```

### 3. Aktivite Raporu

```python
def generate_activity_report(client, days=7):
    """Aktivite raporu oluşturur."""
    
    # Son N günün aktiviteleri
    since_date = (datetime.now() - timedelta(days=days)).isoformat()
    activities = client.stream.list_user_stream(
        after=since_date,
        max_size=200
    )
    
    # Analiz
    analysis = analyze_stream_notes(activities)
    
    # Rapor
    report = f"""
    📊 {days} Günlük Aktivite Raporu
    ================================
    
    Toplam Aktivite: {analysis['total']}
    
    Aktivite Türleri:
    """
    
    for note_type, count in analysis['by_type'].items():
        report += f"  - {note_type}: {count}\n"
    
    report += f"""
    
    Özel Durumlar:
    - Attachment'lı post'lar: {analysis['with_attachments']}
    - Mention'lı post'lar: {analysis['with_mentions']}
    - Internal note'lar: {analysis['internal_notes']}
    """
    
    return report

# Kullanım
report = generate_activity_report(client, days=7)
print(report)
```

Bu dokümantasyon EspoCRM Stream API'sinin tüm özelliklerini kapsamaktadır. Daha fazla bilgi için örnek dosyalara ve API referansına bakabilirsiniz.