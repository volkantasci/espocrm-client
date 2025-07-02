"""
EspoCRM Python Client - Temel Kullanım Örneği

Bu örnek, EspoCRM Python Client'ın temel kullanımını gösterir.
"""

from espocrm import EspoCRMClient
from espocrm.auth import APIKeyAuth

def main():
    """Temel kullanım örneği"""
    # Client'ı başlat
    auth = APIKeyAuth("your-api-key-here")
    client = EspoCRMClient("https://your-espocrm.com", auth)
    
    # Yeni Lead oluştur
    lead_data = {
        "firstName": "John",
        "lastName": "Doe",
        "emailAddress": "john.doe@example.com",
        "phoneNumber": "+1234567890",
        "status": "New"
    }
    
    print("Yeni Lead oluşturuluyor...")
    lead = client.crud.create("Lead", lead_data)
    print(f"Lead oluşturuldu: {lead.id}")
    
    # Lead'i oku
    print(f"Lead okunuyor: {lead.id}")
    retrieved_lead = client.crud.get("Lead", lead.id)
    print(f"Lead adı: {retrieved_lead.firstName} {retrieved_lead.lastName}")
    
    # Lead'i güncelle
    print("Lead güncelleniyor...")
    client.crud.update("Lead", lead.id, {"status": "Qualified"})
    print("Lead güncellendi")
    
    # Lead'leri listele
    print("Lead'ler listeleniyor...")
    leads = client.crud.list("Lead", limit=10)
    print(f"Toplam {len(leads.records)} Lead bulundu")
    
    for lead in leads.records:
        print(f"- {lead.firstName} {lead.lastName} ({lead.status})")

if __name__ == "__main__":
    main()