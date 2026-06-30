import requests
from bs4 import BeautifulSoup
import json
import time
import os

# Sitenin sayfalama (pagination) mantığına uygun URL şablonu
BASE_URL = "https://muhaddis.org/cgi-bin/dbman/db.cgi?db=ks&uid=default&view_records=1&SNo=*&nh={}"

all_hadiths = []
page = 1

print("Veri çekme işlemi başlatılıyor...")

while True:
    url = BASE_URL.format(page)
    try:
        response = requests.get(url, timeout=15)
        # Sitenin HTML meta etiketindeki karakter seti
        response.encoding = 'iso-8859-9' 
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        break

    soup = BeautifulSoup(response.text, 'html.parser')

    # HTML örneğindeki gibi sadece verilerin olduğu tabloları seçiyoruz
    tables = soup.find_all('table', attrs={'bgcolor': '#550000'})

    # Eğer sayfada tablo yoksa, son sayfaya gelmişiz demektir, döngüyü kır
    if not tables:
        break

    for table in tables:
        hadith_data = {}
        rows = table.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                # Başlıkları (Fasıl, Konu vb.) temizle
                key = cols[0].text.strip().replace(':', '')
                # İçerikleri temizle
                value = cols[1].text.strip()

                # Kayıt No kısmında e-mail linki gibi gereksiz HTML kalıntıları varsa temizle
                if key == "Kayıt No.":
                    value = value.split('[')[0].replace('&nbsp;', '').strip()

                if key and key != "":
                    hadith_data[key] = value

        if hadith_data:
            all_hadiths.append(hadith_data)

    print(f"Sayfa {page} tamamlandı. Toplam çekilen kayıt: {len(all_hadiths)}")
    page += 1
    time.sleep(1) # Sunucuyu yormamak ve banlanmamak için 1 saniye bekle

print(f"İşlem bitti. Tam {len(all_hadiths)} kayıt başarıyla çekildi.")

# Verileri 'data' klasörüne kaydedelim
os.makedirs('data', exist_ok=True)

# 1. HAM LİSTE (Tüm Veriler)
with open('data/tum_hadisler.json', 'w', encoding='utf-8') as f:
    json.dump(all_hadiths, f, ensure_ascii=False, indent=2)

# Orijinal kaynak isimlerini koruyan gruplama fonksiyonu
def verileri_grupla(anahtar_kelime, dosya_adi):
    gruplu_veri = {}
    for h in all_hadiths:
        kategori = h.get(anahtar_kelime, 'Belirtilmemiş')
        if kategori not in gruplu_veri:
            gruplu_veri[kategori] = []
        gruplu_veri[kategori].append(h)

    with open(f'data/{dosya_adi}', 'w', encoding='utf-8') as f:
        json.dump(gruplu_veri, f, ensure_ascii=False, indent=2)

# 2. Raviye Göre (Örn: Ebu Hüreyre sözleri ayrı bir listede)
verileri_grupla('Ravi (r.a.)', 'raviye_gore.json')

# 3. Konuya Göre
verileri_grupla('Konu', 'konuya_gore.json')

# 4. Fasıla Göre (Ana Kategori)
verileri_grupla('Fasıl', 'fasila_gore.json')

print("Orijinal kategoriler bozulmadan tüm JSON dosyaları başarıyla oluşturuldu.")