from django.test import TestCase
from .services import generate_log_hash
from datetime import datetime
import hashlib

# Create your tests here.

class ServicesTestCase(TestCase):
    def test_generate_log_hash_consistency(self):
        """
        generate_log_hash fonksiyonunun aynı girdilerle her zaman aynı çıktıyı ürettiğini test eder.
        """
        timestamp_str = "2025-06-21 12:00:00"
        timestamp_obj = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

        tc_no = "12345678901"
        ad_soyad = "Test Kullanıcı"
        telefon = "5554443322"
        ip_adresi = "192.168.1.1"
        mac_adresi = "00:1A:2B:3C:4D:5E"

        # Fonksiyonu çağırırken doğru değişkenleri kullandığımızdan emin olalım.
        # Önceki denemede mac_adresi yerine yanlışlıkla ip_adresi iki kez gönderilmişti.
        generated_hash = generate_log_hash(
            tc_no, ad_soyad, telefon, ip_adresi, mac_adresi, timestamp_obj
        )

        # Beklenen hash'i doğru formatla hesapla
        formatted_timestamp = timestamp_obj.strftime('%Y-%m-%d %H:%M:%S')
        expected_input_str = f"{tc_no}{ad_soyad}{telefon}{ip_adresi}{mac_adresi}{formatted_timestamp}"
        expected_hash = hashlib.sha256(expected_input_str.encode('utf-8')).hexdigest()

        self.assertEqual(generated_hash, expected_hash)
