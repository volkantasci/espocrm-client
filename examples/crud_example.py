"""EspoCRM CRUD operasyonları örnek kullanımı.

Bu örnek EspoCRM Python API istemcisinin CRUD operasyonlarını
ve arama özelliklerini nasıl kullanacağınızı gösterir.
"""

import os
from datetime import datetime, date
from typing import List

# EspoCRM client ve modelleri import et
from espocrm import (
    EspoCRMClient,
    ClientConfig,
    APIKeyAuth,
    SearchParams,
    Account,
    Contact,
    Lead,
    Opportunity,
    equals,
    contains,
    greater_than,
    in_list,
    today,
    create_search_params,
    get_logger
)


def main():
    """Ana örnek fonksiyon."""
    
    # Logger'ı ayarla
    logger = get_logger("crud_example")
    
    # Konfigürasyon oluştur
    config = ClientConfig(
        base_url=os.getenv("ESPOCRM_URL", "https://your-espocrm.com"),
        timeout=30,
        max_retries=3,
        debug=True
    )
    
    # Authentication oluştur
    auth = APIKeyAuth(api_key=os.getenv("ESPOCRM_API_KEY", "your-api-key"))
    
    # Client oluştur
    with EspoCRMClient(config.base_url, auth, config) as client:
        logger.info("EspoCRM client başlatıldı")
        
        # Bağlantıyı test et
        try:
            if client.test_connection():
                logger.info("Bağlantı başarılı!")
            else:
                logger.error("Bağlantı başarısız!")
                return
        except Exception as e:
            logger.error(f"Bağlantı hatası: {e}")
            return
        
        # CRUD operasyonları örnekleri
        crud_examples(client)
        
        # Arama örnekleri
        search_examples(client)
        
        # Bulk operasyon örnekleri
        bulk_examples(client)
        
        # Entity-specific örnekler
        entity_specific_examples(client)


def crud_examples(client: EspoCRMClient):
    """Temel CRUD operasyonları örnekleri."""
    
    logger = get_logger("crud_examples")
    logger.info("=== CRUD Operasyonları Örnekleri ===")
    
    try:
        # 1. CREATE - Yeni Account oluştur
        logger.info("1. Account oluşturuluyor...")
        
        account_data = {
            "name": "Test Şirketi",
            "website": "https://test-sirketi.com",
            "phoneNumber": "+90 212 555 0123",
            "emailAddress": "info@test-sirketi.com",
            "type": "Customer",
            "industry": "Technology",
            "billingAddressCity": "İstanbul",
            "billingAddressCountry": "Türkiye"
        }
        
        # Ana client üzerinden
        account_response = client.create_entity("Account", account_data)
        account_id = account_response.get_id()
        logger.info(f"Account oluşturuldu: {account_id}")
        
        # CRUD client üzerinden de yapılabilir
        # account_response = client.crud.create("Account", account_data)
        
        # 2. READ - Account'u oku
        logger.info("2. Account okunuyor...")
        
        account_response = client.get_entity("Account", account_id)
        account = account_response.get_entity(Account)
        logger.info(f"Account okundu: {account.name} - {account.website}")
        
        # Sadece belirli field'ları seç
        account_response = client.get_entity("Account", account_id, select=["name", "website", "phoneNumber"])
        logger.info("Account seçili field'larla okundu")
        
        # 3. UPDATE - Account'u güncelle
        logger.info("3. Account güncelleniyor...")
        
        update_data = {
            "website": "https://yeni-test-sirketi.com",
            "description": "Güncellenmiş açıklama"
        }
        
        updated_response = client.update_entity("Account", account_id, update_data)
        updated_account = updated_response.get_entity(Account)
        logger.info(f"Account güncellendi: {updated_account.website}")
        
        # 4. LIST - Account listesi
        logger.info("4. Account listesi getiriliyor...")
        
        list_response = client.list_entities("Account", max_size=5)
        logger.info(f"Toplam Account sayısı: {list_response.total}")
        logger.info(f"Getirilen Account sayısı: {len(list_response.list)}")
        
        accounts = list_response.get_entities(Account)
        for acc in accounts[:3]:  # İlk 3'ünü göster
            logger.info(f"  - {acc.name} ({acc.id})")
        
        # 5. DELETE - Account'u sil
        logger.info("5. Account siliniyor...")
        
        success = client.delete_entity("Account", account_id)
        if success:
            logger.info("Account başarıyla silindi")
        else:
            logger.error("Account silinemedi")
        
    except Exception as e:
        logger.error(f"CRUD operasyonu hatası: {e}")


def search_examples(client: EspoCRMClient):
    """Arama operasyonları örnekleri."""
    
    logger = get_logger("search_examples")
    logger.info("=== Arama Operasyonları Örnekleri ===")
    
    try:
        # 1. Basit arama - SearchParams ile
        logger.info("1. Basit arama yapılıyor...")
        
        search = SearchParams()
        search.add_contains("name", "Test")
        search.set_pagination(0, 10)
        search.set_order("createdAt", "desc")
        
        results = client.search_entities("Account", search)
        logger.info(f"'Test' içeren Account sayısı: {results.total}")
        
        # 2. Karmaşık arama - Multiple where clauses
        logger.info("2. Karmaşık arama yapılıyor...")
        
        search = SearchParams()
        search.add_equals("type", "Customer")
        search.add_not_equals("industry", "")
        search.add_is_not_null("emailAddress")
        search.set_select(["name", "website", "emailAddress", "type", "industry"])
        
        results = client.search_entities("Account", search)
        logger.info(f"Customer type Account sayısı: {results.total}")
        
        # 3. Convenience functions ile arama
        logger.info("3. Convenience functions ile arama...")
        
        search = create_search_params(max_size=20)
        search.add_where_clause(equals("type", "Customer"))
        search.add_where_clause(contains("name", "Tech"))
        search.add_where_clause(is_not_null("website"))
        
        results = client.search_entities("Account", search)
        logger.info(f"Tech içeren Customer Account sayısı: {results.total}")
        
        # 4. Tarih bazlı arama
        logger.info("4. Tarih bazlı arama yapılıyor...")
        
        search = SearchParams()
        search.add_today("createdAt")  # Bugün oluşturulanlar
        search.set_order("createdAt", "desc")
        
        results = client.search_entities("Account", search)
        logger.info(f"Bugün oluşturulan Account sayısı: {results.total}")
        
        # 5. Liste bazlı arama
        logger.info("5. Liste bazlı arama yapılıyor...")
        
        search = SearchParams()
        search.add_in("type", ["Customer", "Partner", "Vendor"])
        search.add_not_in("industry", [""])
        
        results = client.search_entities("Account", search)
        logger.info(f"Belirli type'lardaki Account sayısı: {results.total}")
        
        # 6. Sayısal arama
        logger.info("6. Sayısal arama yapılıyor (Opportunity)...")
        
        search = SearchParams()
        search.add_greater_than("amount", 10000)
        search.add_equals("stage", "Proposal")
        search.set_order("amount", "desc")
        
        results = client.search_entities("Opportunity", search)
        logger.info(f"10.000'den büyük Proposal Opportunity sayısı: {results.total}")
        
    except Exception as e:
        logger.error(f"Arama operasyonu hatası: {e}")


def bulk_examples(client: EspoCRMClient):
    """Bulk operasyon örnekleri."""
    
    logger = get_logger("bulk_examples")
    logger.info("=== Bulk Operasyon Örnekleri ===")
    
    try:
        # 1. Bulk Create
        logger.info("1. Bulk Account oluşturuluyor...")
        
        accounts_data = [
            {
                "name": f"Bulk Test Şirketi {i}",
                "website": f"https://bulk-test-{i}.com",
                "type": "Customer",
                "industry": "Technology"
            }
            for i in range(1, 4)
        ]
        
        bulk_result = client.crud.bulk_create("Account", accounts_data)
        logger.info(f"Bulk create sonucu: {bulk_result.successful}/{bulk_result.total} başarılı")
        
        if bulk_result.successful > 0:
            created_ids = bulk_result.get_successful_ids()
            logger.info(f"Oluşturulan ID'ler: {created_ids}")
            
            # 2. Bulk Update
            logger.info("2. Bulk Account güncelleniyor...")
            
            updates = [
                {
                    "id": account_id,
                    "description": f"Bulk güncellenmiş açıklama - {datetime.now()}"
                }
                for account_id in created_ids
            ]
            
            bulk_update_result = client.crud.bulk_update("Account", updates)
            logger.info(f"Bulk update sonucu: {bulk_update_result.successful}/{bulk_update_result.total} başarılı")
            
            # 3. Bulk Delete
            logger.info("3. Bulk Account siliniyor...")
            
            bulk_delete_result = client.crud.bulk_delete("Account", created_ids)
            logger.info(f"Bulk delete sonucu: {bulk_delete_result.successful}/{bulk_delete_result.total} başarılı")
        
    except Exception as e:
        logger.error(f"Bulk operasyon hatası: {e}")


def entity_specific_examples(client: EspoCRMClient):
    """Entity-specific operasyon örnekleri."""
    
    logger = get_logger("entity_examples")
    logger.info("=== Entity-Specific Operasyon Örnekleri ===")
    
    try:
        # 1. Account operations
        logger.info("1. Account operasyonları...")
        
        # Account oluştur
        account_data = {
            "name": "Entity Test Şirketi",
            "website": "https://entity-test.com",
            "type": "Customer"
        }
        
        account_response = client.crud.create_account(account_data)
        account_id = account_response.get_id()
        logger.info(f"Account oluşturuldu: {account_id}")
        
        # Account listesi
        accounts_response = client.crud.list_accounts(
            search_params=create_search_params(max_size=5)
        )
        logger.info(f"Account listesi: {accounts_response.total} toplam")
        
        # 2. Contact operations
        logger.info("2. Contact operasyonları...")
        
        contact_data = {
            "firstName": "Ahmet",
            "lastName": "Yılmaz",
            "emailAddress": "ahmet.yilmaz@test.com",
            "accountId": account_id,  # Yukarıda oluşturulan account'a bağla
            "title": "Yazılım Geliştirici"
        }
        
        contact_response = client.crud.create_contact(contact_data)
        contact_id = contact_response.get_id()
        logger.info(f"Contact oluşturuldu: {contact_id}")
        
        # Contact'ı oku ve Account bilgisini kontrol et
        contact_response = client.crud.get_contact(contact_id)
        contact = contact_response.get_entity(Contact)
        logger.info(f"Contact: {contact.get_full_name()} - {contact.account_name}")
        
        # 3. Lead operations
        logger.info("3. Lead operasyonları...")
        
        lead_data = {
            "firstName": "Mehmet",
            "lastName": "Demir",
            "emailAddress": "mehmet.demir@lead.com",
            "accountName": "Lead Test Şirketi",
            "status": "New",
            "source": "Website"
        }
        
        lead_response = client.crud.create_lead(lead_data)
        lead_id = lead_response.get_id()
        logger.info(f"Lead oluşturuldu: {lead_id}")
        
        # Lead'i oku
        lead_response = client.crud.get_lead(lead_id)
        lead = lead_response.get_entity(Lead)
        logger.info(f"Lead: {lead.get_full_name()} - {lead.status}")
        
        # 4. Opportunity operations
        logger.info("4. Opportunity operasyonları...")
        
        opportunity_data = {
            "name": "Test Opportunity",
            "accountId": account_id,
            "stage": "Prospecting",
            "amount": 50000.0,
            "probability": 25,
            "closeDate": "2024-12-31"
        }
        
        opp_response = client.crud.create_opportunity(opportunity_data)
        opp_id = opp_response.get_id()
        logger.info(f"Opportunity oluşturuldu: {opp_id}")
        
        # Opportunity'yi oku
        opp_response = client.crud.get_opportunity(opp_id)
        opportunity = opp_response.get_entity(Opportunity)
        logger.info(f"Opportunity: {opportunity.name} - {opportunity.get_weighted_amount():.2f} TL")
        
        # 5. Utility operations
        logger.info("5. Utility operasyonları...")
        
        # Entity sayısı
        account_count = client.count_entities("Account")
        logger.info(f"Toplam Account sayısı: {account_count}")
        
        # Entity var mı kontrolü
        exists = client.entity_exists("Account", account_id)
        logger.info(f"Account {account_id} var mı: {exists}")
        
        # Cleanup - Oluşturulan entity'leri sil
        logger.info("6. Cleanup yapılıyor...")
        
        client.delete_entity("Opportunity", opp_id)
        client.delete_entity("Lead", lead_id)
        client.delete_entity("Contact", contact_id)
        client.delete_entity("Account", account_id)
        
        logger.info("Cleanup tamamlandı")
        
    except Exception as e:
        logger.error(f"Entity-specific operasyon hatası: {e}")


if __name__ == "__main__":
    # Environment variables ayarla (örnek)
    # os.environ["ESPOCRM_URL"] = "https://your-espocrm.com"
    # os.environ["ESPOCRM_API_KEY"] = "your-api-key"
    
    main()