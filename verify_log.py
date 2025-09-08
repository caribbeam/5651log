import os
import django
import sys
from datetime import datetime
import hashlib

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yasalog.settings')
django.setup()

from log_kayit.models import LogKayit

def generate_log_hash(tc_no, ad_soyad, telefon, ip_adresi, mac_adresi, timestamp):
    hash_input = f"{tc_no}{ad_soyad}{telefon}{ip_adresi}{mac_adresi}{timestamp}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

def main():
    print("Log imzaları doğrulanıyor...")
    total = 0
    errors = 0
    for log in LogKayit.objects.all():
        hash_val = generate_log_hash(
            log.tc_no,
            log.ad_soyad,
            log.telefon,
            log.ip_adresi,
            log.mac_adresi,
            log.giris_zamani,
        )
        total += 1
        if log.sha256_hash != hash_val:
            print(f"HATALI: ID={log.id}, TC={log.tc_no}, Ad={log.ad_soyad}, Zaman={log.giris_zamani}, DB Hash={log.sha256_hash}, Hesaplanan={hash_val}")
            errors += 1
    print(f"\nToplam log: {total}")
    if errors == 0:
        print("Tüm log imzaları DOĞRU.")
    else:
        print(f"{errors} adet log imzası HATALI!")

if __name__ == "__main__":
    main() 