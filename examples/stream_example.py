"""
EspoCRM Stream API Kullanım Örneği

Bu örnek EspoCRM Stream operasyonlarının nasıl kullanılacağını gösterir:
- User stream listeleme
- Entity stream listeleme
- Stream'e post yapma
- Entity follow/unfollow
- Stream filtering
"""

import asyncio
from datetime import datetime, timedelta
from typing import List

from espocrm import EspoCRMClient, ClientConfig
from espocrm.auth import APIKeyAuth
from espocrm.models.stream import StreamNote, StreamNoteType
from espocrm.exceptions import EspoCRMError


def main():
    """Ana örnek fonksiyon."""
    
    # Client konfigürasyonu
    config = ClientConfig(
        base_url="https://your-espocrm.com",
        timeout=30,
        max_retries=3,
        log_level="INFO"
    )
    
    # Authentication
    auth = APIKeyAuth(api_key="your-api-key")
    
    # Client oluştur
    with EspoCRMClient(config.base_url, auth, config) as client:
        print("🚀 EspoCRM Stream API Örneği")
        print("=" * 50)
        
        # Bağlantı testi
        try:
            if client.test_connection():
                print("✅ EspoCRM bağlantısı başarılı")
            else:
                print("❌ EspoCRM bağlantısı başarısız")
                return
        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            return
        
        # Stream örnekleri
        try:
            # 1. User Stream Listeleme
            print("\n📋 User Stream Listeleme")
            print("-" * 30)
            user_stream_example(client)
            
            # 2. Entity Stream Listeleme
            print("\n📋 Entity Stream Listeleme")
            print("-" * 30)
            entity_stream_example(client)
            
            # 3. Stream'e Post Yapma
            print("\n✍️ Stream'e Post Yapma")
            print("-" * 30)
            post_to_stream_example(client)
            
            # 4. Entity Follow/Unfollow
            print("\n👥 Entity Follow/Unfollow")
            print("-" * 30)
            follow_unfollow_example(client)
            
            # 5. Stream Filtering
            print("\n🔍 Stream Filtering")
            print("-" * 30)
            stream_filtering_example(client)
            
            # 6. Attachment ile Post
            print("\n📎 Attachment ile Post")
            print("-" * 30)
            post_with_attachments_example(client)
            
            # 7. Entity Helper Methods
            print("\n🔧 Entity Helper Methods")
            print("-" * 30)
            entity_helper_methods_example(client)
            
        except EspoCRMError as e:
            print(f"❌ EspoCRM API Hatası: {e}")
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}")


def user_stream_example(client: EspoCRMClient):
    """User stream listeleme örneği."""
    
    try:
        # Basit user stream
        print("📋 Kullanıcı stream'i getiriliyor...")
        stream_notes = client.stream.list_user_stream(
            max_size=10
        )
        
        print(f"✅ {len(stream_notes)} stream note bulundu")
        
        # Stream note'ları göster
        for i, note in enumerate(stream_notes[:3], 1):
            print(f"  {i}. {note.type.value} - {note.get_display_text()[:50]}...")
            if note.created_at:
                print(f"     📅 {note.created_at.strftime('%Y-%m-%d %H:%M')}")
            if note.created_by_name:
                print(f"     👤 {note.created_by_name}")
        
        # Pagination örneği
        print("\n📋 Pagination ile stream getiriliyor...")
        paginated_stream = client.stream.list_user_stream(
            offset=10,
            max_size=5
        )
        print(f"✅ Sayfa 2: {len(paginated_stream)} stream note")
        
    except Exception as e:
        print(f"❌ User stream hatası: {e}")


def entity_stream_example(client: EspoCRMClient):
    """Entity stream listeleme örneği."""
    
    try:
        # Önce bir Account bulalım
        accounts = client.crud.list("Account", max_size=1)
        if not accounts:
            print("⚠️ Test için Account bulunamadı")
            return
        
        account = accounts[0]
        print(f"📋 Account stream'i getiriliyor: {account.get('name', 'N/A')}")
        
        # Account stream'ini getir
        stream_notes = client.stream.list_entity_stream(
            entity_type="Account",
            entity_id=account["id"],
            max_size=5
        )
        
        print(f"✅ {len(stream_notes)} stream note bulundu")
        
        # Stream note'ları göster
        for i, note in enumerate(stream_notes, 1):
            print(f"  {i}. {note.type.value}")
            if note.is_post_type():
                print(f"     💬 {note.get_display_text()[:50]}...")
            else:
                print(f"     🔄 {note.get_display_text()}")
            
            if note.has_attachments():
                print(f"     📎 {note.get_attachment_count()} attachment")
        
        # Convenience method kullanımı
        print("\n📋 Convenience method ile Account stream...")
        convenience_stream = client.stream.get_account_stream(
            account_id=account["id"],
            max_size=3
        )
        print(f"✅ Convenience method: {len(convenience_stream)} note")
        
    except Exception as e:
        print(f"❌ Entity stream hatası: {e}")


def post_to_stream_example(client: EspoCRMClient):
    """Stream'e post yapma örneği."""
    
    try:
        # Önce bir Account bulalım
        accounts = client.crud.list("Account", max_size=1)
        if not accounts:
            print("⚠️ Test için Account bulunamadı")
            return
        
        account = accounts[0]
        print(f"✍️ Account'a post yapılıyor: {account.get('name', 'N/A')}")
        
        # Basit post
        post_content = f"Test post - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        stream_note = client.stream.post_to_stream(
            parent_type="Account",
            parent_id=account["id"],
            post=post_content
        )
        
        print(f"✅ Post oluşturuldu: {stream_note.id}")
        print(f"   💬 İçerik: {stream_note.get_display_text()}")
        
        # HTML içerikli post
        html_content = """
        <p><strong>Önemli Güncelleme</strong></p>
        <ul>
            <li>Proje durumu güncellendi</li>
            <li>Yeni milestone eklendi</li>
            <li>Takım toplantısı planlandı</li>
        </ul>
        <p><em>Detaylar için lütfen iletişime geçin.</em></p>
        """
        
        html_note = client.stream.post_to_stream(
            parent_type="Account",
            parent_id=account["id"],
            post=html_content
        )
        
        print(f"✅ HTML post oluşturuldu: {html_note.id}")
        
        # Convenience method kullanımı
        convenience_note = client.stream.post_to_account(
            account_id=account["id"],
            post="Convenience method ile oluşturulan post"
        )
        
        print(f"✅ Convenience post: {convenience_note.id}")
        
    except Exception as e:
        print(f"❌ Post oluşturma hatası: {e}")


def follow_unfollow_example(client: EspoCRMClient):
    """Entity follow/unfollow örneği."""
    
    try:
        # Önce bir Account bulalım
        accounts = client.crud.list("Account", max_size=1)
        if not accounts:
            print("⚠️ Test için Account bulunamadı")
            return
        
        account = accounts[0]
        account_id = account["id"]
        account_name = account.get("name", "N/A")
        
        print(f"👥 Account follow/unfollow testi: {account_name}")
        
        # Mevcut follow durumunu kontrol et
        is_following = client.stream.is_following_entity("Account", account_id)
        print(f"📊 Mevcut durum: {'Takip ediliyor' if is_following else 'Takip edilmiyor'}")
        
        # Follow işlemi
        if not is_following:
            print("➕ Account takip ediliyor...")
            success = client.stream.follow_entity("Account", account_id)
            if success:
                print("✅ Account başarıyla takip edildi")
            else:
                print("❌ Account takip edilemedi")
        
        # Follow durumunu tekrar kontrol et
        is_following_after = client.stream.is_following_entity("Account", account_id)
        print(f"📊 Yeni durum: {'Takip ediliyor' if is_following_after else 'Takip edilmiyor'}")
        
        # Unfollow işlemi
        if is_following_after:
            print("➖ Account takibi bırakılıyor...")
            success = client.stream.unfollow_entity("Account", account_id)
            if success:
                print("✅ Account takibi başarıyla bırakıldı")
            else:
                print("❌ Account takibi bırakılamadı")
        
        # Final durum
        final_status = client.stream.is_following_entity("Account", account_id)
        print(f"📊 Final durum: {'Takip ediliyor' if final_status else 'Takip edilmiyor'}")
        
        # Convenience methods
        print("\n👥 Convenience methods ile follow/unfollow...")
        client.stream.follow_account(account_id)
        print("✅ Convenience follow")
        
        client.stream.unfollow_account(account_id)
        print("✅ Convenience unfollow")
        
    except Exception as e:
        print(f"❌ Follow/unfollow hatası: {e}")


def stream_filtering_example(client: EspoCRMClient):
    """Stream filtering örneği."""
    
    try:
        print("🔍 Stream filtering örnekleri...")
        
        # Sadece Post türündeki note'lar
        post_notes = client.stream.list_user_stream(
            note_types=[StreamNoteType.POST],
            max_size=5
        )
        print(f"✅ Post note'ları: {len(post_notes)}")
        
        # Sistem note'ları (Create, Update, etc.)
        system_notes = client.stream.list_user_stream(
            note_types=[
                StreamNoteType.CREATE,
                StreamNoteType.UPDATE,
                StreamNoteType.STATUS
            ],
            max_size=5
        )
        print(f"✅ Sistem note'ları: {len(system_notes)}")
        
        # Tarih filtresi - son 7 gün
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent_notes = client.stream.list_user_stream(
            after=week_ago,
            max_size=10
        )
        print(f"✅ Son 7 günün note'ları: {len(recent_notes)}")
        
        # Belirli bir kullanıcının aktiviteleri
        # (Bu örnek için user_id'yi dinamik olarak alamayız, 
        # gerçek kullanımda mevcut bir user_id kullanılmalı)
        # user_notes = client.stream.list_user_stream(
        #     user_id="actual_user_id_here",
        #     max_size=5
        # )
        # print(f"✅ Kullanıcı note'ları: {len(user_notes)}")
        
    except Exception as e:
        print(f"❌ Stream filtering hatası: {e}")


def post_with_attachments_example(client: EspoCRMClient):
    """Attachment ile post örneği."""
    
    try:
        # Önce bir Account bulalım
        accounts = client.crud.list("Account", max_size=1)
        if not accounts:
            print("⚠️ Test için Account bulunamadı")
            return
        
        account = accounts[0]
        print(f"📎 Attachment ile post: {account.get('name', 'N/A')}")
        
        # Not: Gerçek kullanımda önce attachment'ları upload etmeniz gerekir
        # Bu örnek attachment ID'lerinin mevcut olduğunu varsayar
        
        # Örnek attachment ID'leri (gerçek kullanımda upload edilmiş ID'ler)
        # attachment_ids = ["attachment_id_1", "attachment_id_2"]
        
        # Attachment olmadan örnek
        post_content = """
        <p><strong>Proje Raporu</strong></p>
        <p>Bu post'a normalde dosyalar eklenebilir:</p>
        <ul>
            <li>Proje planı (PDF)</li>
            <li>Bütçe tablosu (Excel)</li>
            <li>Sunum dosyası (PowerPoint)</li>
        </ul>
        <p><em>Attachment'lar için önce dosyaları upload etmeniz gerekir.</em></p>
        """
        
        stream_note = client.stream.post_to_stream(
            parent_type="Account",
            parent_id=account["id"],
            post=post_content,
            # attachments_ids=attachment_ids  # Gerçek attachment ID'leri
        )
        
        print(f"✅ Post oluşturuldu: {stream_note.id}")
        print(f"   📎 Attachment sayısı: {stream_note.get_attachment_count()}")
        
        # Team kısıtlaması ile post
        # team_restricted_note = client.stream.post_to_stream(
        #     parent_type="Account",
        #     parent_id=account["id"],
        #     post="Bu post sadece belirli team'lere görünür",
        #     teams_ids=["team_id_1", "team_id_2"]
        # )
        
        # Internal note
        internal_note = client.stream.post_to_stream(
            parent_type="Account",
            parent_id=account["id"],
            post="Bu bir internal note'dur",
            is_internal=True
        )
        
        print(f"✅ Internal note: {internal_note.id}")
        
    except Exception as e:
        print(f"❌ Attachment post hatası: {e}")


def entity_helper_methods_example(client: EspoCRMClient):
    """Entity helper methods örneği."""
    
    try:
        # Önce bir Account bulalım
        accounts = client.crud.list("Account", max_size=1)
        if not accounts:
            print("⚠️ Test için Account bulunamadı")
            return
        
        # Account entity'sini oluştur
        from espocrm.models.entities import Account
        account_entity = Account.from_api_response(accounts[0])
        
        print(f"🔧 Entity helper methods: {account_entity.get_display_name()}")
        
        # Entity stream'ini getir
        print("📋 Entity stream getiriliyor...")
        entity_stream = account_entity.get_stream(client, max_size=3)
        print(f"✅ {len(entity_stream)} stream note")
        
        # Entity'ye post yap
        print("✍️ Entity'ye post yapılıyor...")
        post_note = account_entity.post_to_stream(
            client,
            "Entity helper method ile oluşturulan post"
        )
        print(f"✅ Post oluşturuldu: {post_note.id}")
        
        # Entity'yi takip et
        print("👥 Entity takip ediliyor...")
        follow_result = account_entity.follow(client)
        print(f"✅ Follow sonucu: {follow_result}")
        
        # Follow durumunu kontrol et
        is_followed = account_entity.is_followed(client)
        print(f"📊 Follow durumu: {is_followed}")
        
        # Entity takibini bırak
        print("👥 Entity takibi bırakılıyor...")
        unfollow_result = account_entity.unfollow(client)
        print(f"✅ Unfollow sonucu: {unfollow_result}")
        
    except Exception as e:
        print(f"❌ Entity helper methods hatası: {e}")


if __name__ == "__main__":
    main()