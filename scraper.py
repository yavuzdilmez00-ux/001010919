import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
import math

BASE_URL = "https://muhaddis.org/cgi-bin/dbman/db.cgi?db=ks&uid=default&view_records=1&SNo=*&nh={}"

all_hadiths = []

print("Sistem başlatılıyor... Toplam veri sayısı analiz ediliyor.")

# 1. ADIM: Toplam sayfa sayısını dinamik olarak bul
try:
    first_response = requests.get(BASE_URL.format(1), timeout=15)
    first_response.encoding = 'iso-8859-9'
    soup = BeautifulSoup(first_response.text, 'html.parser')
    
    # Sitedeki "5972 kayıt bulundu" metnini bulup rakamı çekiyoruz
    kayit_metni = soup.find(string=re.compile("kayıt bulundu"))
    
    if kayit_metni:
        # Metnin içindeki tüm rakamları birleştir (örn: 5.972 -> 5972)
        rakam = re.search(r'(\d+)', kayit_metni.parent.text.replace('.', ''))
        total_records = int(rakam.group(1)) if rakam else 5972
    else:
        total_records = 5972 # Bulamazsa senin attığın HTML'deki sayıyı baz al
        
except Exception as e:
    print(f"Bağlantı hatası, varsayılan kayıt sayısı kullanılacak: {e}")
    total_records = 5972

# Her sayfada 10 hadis var, yukarı yuvarlayarak tam sayfa sayısını buluyoruz
total_pages = math.ceil(total_records / 10)
print(f"Sistemde toplam {total_records} hadis ve {total_pages} sayfa tespit edildi.")
print("Tüm sayfaları eksiksiz çekme işlemi başlıyor...\n")

# 2. ADIM: Sayfaları tek tek ve garantili şekilde gez
for page in range(1, total_pages + 1):
    url = BASE_URL.format(page)
    basari = False
    deneme_sayisi = 0
    
    # Sunucu yanıt vermezse diye 3 defa tekrar deneme (Retry) mekanizması
    while not basari and deneme_sayisi < 3:
        try:
            response = requests.get(url, timeout=20)
            response.encoding = 'iso-8859-9'
            
            page_soup = BeautifulSoup(response.text, 'html.parser')
            tables = page_soup.find_all('table', attrs={'bgcolor': '#550000'})
            
            for table in tables:
                hadith_data = {}
                rows = table.find_all('tr')
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        key = cols[0].text.strip().replace(':', '')
                        value = cols[1].text.strip()
                        
                        # Kayıt numarasının yanındaki e-mail buton kodlarını temizle
                        if key == "Kayıt No.":
                            value = value.split('[')[0].replace('&nbsp;', '').strip()
                        
                        if key and key != "":
                            hadith_data[key] = value
                
                if hadith_data:
                    all_hadiths.append(hadith_data)
            
            print(f"Sayfa {page}/{total_pages} çekildi. (Şu anki toplam kayıt: {len(all_hadiths)})")
            basari = True
            
        except Exception as e:
            deneme_sayisi += 1
            print(f"Sayfa {page} çekilemedi, tekrar deneniyor ({deneme_sayisi}/3)... Hata: {e}")
            time.sleep(2)
            
    # Sitenin koruma sistemine (Anti-DDoS) takılmamak için her sayfada 1 saniye bekle
    time.sleep(1)

print(f"\nVeri çekme işlemi bitti! Toplam {len(all_hadiths)} kayıt hafızaya alındı.")

# 3. ADIM: JSON formatında kaydetme (Senin istediğin 4 farklı dosyaya bölerek)
os.makedirs('data', exist_ok=True)

# Hiç dokunulmamış, tüm verilerin olduğu ham liste
with open('data/tum_hadisler.json', 'w', encoding='utf-8') as f:
    json.dump(all_hadiths, f, ensure_ascii=False, indent=2)

def verileri_grupla(anahtar_kelime, dosya_adi):
    gruplu_veri = {}
    for h in all_hadiths:
        kategori = h.get(anahtar_kelime, 'Belirtilmemiş')
        if kategori not in gruplu_veri:
            gruplu_veri[kategori] = []
        gruplu_veri[kategori].append(h)
    
    with open(f'data/{dosya_adi}', 'w', encoding='utf-8') as f:
        json.dump(gruplu_veri, f, ensure_ascii=False, indent=2)

verileri_grupla('Ravi (r.a.)', 'raviye_gore.json')
verileri_grupla('Konu', 'konuya_gore.json')
verileri_grupla('Fasıl', 'fasila_gore.json')

print("Bütün veriler JSON formatında başarıyla depolandı.")
