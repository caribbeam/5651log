import hashlib
import os
import csv
from datetime import datetime

def check_tc_kimlik_no(tc):
    """TC Kimlik algoritması kontrolü"""
    if not tc or len(tc) != 11 or not tc.isdigit() or tc[0] == '0':
        return False
    d = [int(x) for x in tc]
    if (sum(d[:10]) % 10 != d[10]):
        return False
    if (((sum(d[0:10:2]) * 7) - sum(d[1:9:2])) % 10 != d[9]):
        return False
    return True

def generate_log_hash(tc_no, ad_soyad, telefon, ip_adresi, mac_adresi, timestamp):
    # Mikrosaniyeleri atlayarak zaman damgasını standart bir formata getir
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    hash_input = f"{tc_no}{ad_soyad}{telefon}{ip_adresi}{mac_adresi}{formatted_timestamp}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

def write_log_to_csv(log, logs_dir=None):
    if logs_dir is None:
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    log_filename = os.path.join(logs_dir, f"log_{log.giris_zamani.strftime('%Y-%m-%d')}.csv")
    write_header = not os.path.exists(log_filename)
    with open(log_filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(["TC No", "Ad Soyad", "Telefon", "IP", "MAC", "Giriş Zamanı", "SHA256 Hash"])
        writer.writerow([
            log.tc_no, log.ad_soyad, log.telefon, log.ip_adresi, log.mac_adresi, log.giris_zamani, log.sha256_hash
        ])
