"""EspoCRM Relationship operasyonları örneği.

Bu örnek EspoCRM Python client'ının relationship yönetimi
özelliklerini gösterir.
"""

import asyncio
from typing import List

from espocrm import EspoCRMClient, ClientConfig
from espocrm.auth import APIKeyAuth
from espocrm.models import SearchParams, equals, contains
from espocrm.models.requests import create_link_request, create_unlink_request


def main():
    """Ana örnek fonksiyonu."""
    
    # Client konfigürasyonu
    config = ClientConfig(
        base_url="https://your-espocrm.com",
        timeout=30,
        max_retries=3,
        debug=True
    )
    
    # Authentication
    auth = APIKeyAuth(api_key="your-api-key-here")
    
    # Client oluştur
    with EspoCRMClient(config.base_url, auth, config) as client:
        
        print("=== EspoCRM Relationship Operasyonları Örneği ===\n")
        
        # 1. İlişkili kayıtları listeleme
        print("1. Account'un Contact'larını listeleme:")
        try:
            account_id = "507f1f77bcf86cd799439011"  # Örnek Account ID
            
            # Account'un tüm Contact'larını listele
            contacts_response = client.relationships.list_related(
                entity_type="Account",
                entity_id=account_id,
                link="contacts",
                max_size=10,
                order_by="name"
            )
            
            print(f"Toplam Contact sayısı: {contacts_response.total}")
            contacts = contacts_response.get_entities()
            
            for contact in contacts:
                print(f"  - {contact.get_display_name()} (ID: {contact.id})")
            
        except Exception as e:
            print(f"Hata: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 2. Tek kayıt ilişkilendirme
        print("2. Account'a yeni Contact ilişkilendirme:")
        try:
            account_id = "507f1f77bcf86cd799439011"
            contact_id = "507f1f77bcf86cd799439012"
            
            # Tek Contact'ı Account'a ilişkilendir
            result = client.relationships.link_single(
                entity_type="Account",
                entity_id=account_id,
                link="contacts",
                target_id=contact_id
            )
            
            print(f"İlişkilendirme sonucu: {result.get_summary()}")
            
            if result.success:
                print("✅ Contact başarıyla Account'a ilişkilendirildi")
            else:
                print("❌ İlişkilendirme başarısız")
                for error in result.errors:
                    print(f"  Hata: {error}")
            
        except Exception as e:
            print(f"Hata: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 3. Çoklu kayıt ilişkilendirme
        print("3. Account'a birden fazla Contact ilişkilendirme:")
        try:
            account_id = "507f1f77bcf86cd799439011"
            contact_ids = [
                "507f1f77bcf86cd799439013",
                "507f1f77bcf86cd799439014",
                "507f1f77bcf86cd799439015"
            ]
            
            # Çoklu Contact'ları Account'a ilişkilendir
            result = client.relationships.link_multiple(
                entity_type="Account",
                entity_id=account_id,
                link="contacts",
                target_ids=contact_ids
            )
            
            print(f"Çoklu ilişkilendirme sonucu: {result.get_summary()}")
            print(f"Başarı oranı: {result.get_success_rate():.1f}%")
            
        except Exception as e:
            print(f"Hata: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 4. Mass relate operasyonu
        print("4. Mass relate operasyonu:")
        try:
            account_id = "507f1f77bcf86cd799439011"
            
            # Belirli kriterlere uyan tüm Contact'ları ilişkilendir
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
                entity_id=account_id,
                link="contacts",
                where=where_criteria
            )
            
            print(f"Mass relate sonucu: {result.get_summary()}")
            print(f"Etkilenen kayıt sayısı: {result.successful_count}")
            
        except Exception as e:
            print(f"Hata: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 5. İlişki kontrolü
        print("5. İlişki varlığını kontrol etme:")
        try:
            account_id = "507f1f77bcf86cd799439011"
            contact_id = "507f1f77bcf86cd799439012"
            
            # İlişkinin var olup olmadığını kontrol et
            exists = client.relationships.check_relationship_exists(
                entity_type="Account",
                entity_id=account_id,
                link="contacts",
                target_id=contact_id
            )
            
            if exists:
                print("✅ İlişki mevcut")
            else:
                print("❌ İlişki mevcut değil")
            
        except Exception as e:
            print(f"Hata: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 6. İlişki kaldırma
        print("6. İlişki kaldırma:")
        try:
            account_id = "507f1f77bcf86cd799439011"
            contact_id = "507f1f77bcf86cd799439012"
            
            # Tek Contact ilişkisini kaldır
            result = client.relationships.unlink_single(
                entity_type="Account",
                entity_id=account_id,
                link="contacts",
                target_id=contact_id
            )
            
            print(f"İlişki kaldırma sonucu: {result.get_summary()}")
            
            if result.success:
                print("✅ İlişki başarıyla kaldırıldı")
            else:
                print("❌ İlişki kaldırma başarısız")
            
        except Exception as e:
            print(f"Hata: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 7. Convenience methods kullanımı
        print("7. Convenience methods kullanımı:")
        try:
            account_id = "507f1f77bcf86cd799439011"
            
            # Ana client'ın convenience method'larını kullan
            contacts_response = client.list_related_entities(
                entity_type="Account",
                entity_id=account_id,
                link="contacts",
                max_size=5
            )
            
            print(f"Convenience method ile Contact sayısı: {contacts_response.total}")
            
            # Entity'leri ilişkilendir
            contact_ids = ["507f1f77bcf86cd799439016", "507f1f77bcf86cd799439017"]
            result = client.link_entities(
                entity_type="Account",
                entity_id=account_id,
                link="contacts",
                target_ids=contact_ids
            )
            
            print(f"Convenience method ile ilişkilendirme: {result.get_summary()}")
            
        except Exception as e:
            print(f"Hata: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 8. Entity helper methods kullanımı
        print("8. Entity helper methods kullanımı:")
        try:
            # Account entity'si oluştur (örnek veri ile)
            from espocrm.models import Account
            
            account_data = {
                "id": "507f1f77bcf86cd799439011",
                "name": "Test Company",
                "contacts": [
                    {"id": "507f1f77bcf86cd799439012", "name": "John Doe"},
                    {"id": "507f1f77bcf86cd799439013", "name": "Jane Smith"}
                ],
                "opportunities": [
                    {"id": "507f1f77bcf86cd799439020", "name": "Big Deal"}
                ]
            }
            
            account = Account.create_from_dict(account_data)
            
            # Relationship helper methods kullan
            print(f"Account Contact ID'leri: {account.get_contact_ids()}")
            print(f"Account Contact isimleri: {account.get_contact_names()}")
            print(f"Account Opportunity sayısı: {len(account.get_opportunity_ids())}")
            
            # Belirli Contact'ın var olup olmadığını kontrol et
            has_contact = account.has_contact("507f1f77bcf86cd799439012")
            print(f"John Doe Contact'ı var mı: {has_contact}")
            
        except Exception as e:
            print(f"Hata: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # 9. Relationship metadata alma
        print("9. Relationship metadata alma:")
        try:
            # Account entity'sinin tüm relationship'lerini al
            metadata = client.relationships.get_relationship_metadata(
                entity_type="Account"
            )
            
            print("Account relationship'leri:")
            if isinstance(metadata, dict):
                for link_name, link_info in metadata.items():
                    link_type = link_info.get("type", "unknown")
                    entity_type = link_info.get("entity", "unknown")
                    print(f"  - {link_name}: {link_type} -> {entity_type}")
            
        except Exception as e:
            print(f"Hata: {e}")
        
        print("\n=== Örnek Tamamlandı ===")


def demonstrate_request_models():
    """Request model'larının kullanımını gösterir."""
    
    print("\n=== Request Model Örnekleri ===\n")
    
    # 1. LinkRequest oluşturma
    print("1. LinkRequest oluşturma:")
    
    # Tek kayıt için
    single_link_request = create_link_request(
        entity_type="Account",
        entity_id="507f1f77bcf86cd799439011",
        link="contacts",
        target_id="507f1f77bcf86cd799439012"
    )
    
    print(f"Tek kayıt link request endpoint: {single_link_request.get_endpoint()}")
    print(f"Link türü: {single_link_request.get_link_type()}")
    print(f"API data: {single_link_request.to_api_dict()}")
    
    # Çoklu kayıt için
    multiple_link_request = create_link_request(
        entity_type="Account",
        entity_id="507f1f77bcf86cd799439011",
        link="contacts",
        target_ids=["507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"]
    )
    
    print(f"\nÇoklu kayıt link request hedef sayısı: {multiple_link_request.get_target_count()}")
    
    # Mass relate için
    mass_link_request = create_link_request(
        entity_type="Account",
        entity_id="507f1f77bcf86cd799439011",
        link="contacts",
        mass_relate=True,
        where=[{"type": "equals", "attribute": "accountId", "value": None}]
    )
    
    print(f"Mass relate link request türü: {mass_link_request.get_link_type()}")
    
    print("\n" + "="*50 + "\n")
    
    # 2. UnlinkRequest oluşturma
    print("2. UnlinkRequest oluşturma:")
    
    unlink_request = create_unlink_request(
        entity_type="Account",
        entity_id="507f1f77bcf86cd799439011",
        link="contacts",
        target_id="507f1f77bcf86cd799439012"
    )
    
    print(f"Unlink request türü: {unlink_request.get_unlink_type()}")
    print(f"Unlink endpoint: {unlink_request.get_endpoint()}")
    
    print("\n=== Request Model Örnekleri Tamamlandı ===")


if __name__ == "__main__":
    # Ana örneği çalıştır
    main()
    
    # Request model örneklerini göster
    demonstrate_request_models()