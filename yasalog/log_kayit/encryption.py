"""
Veri şifreleme sistemi - Encryption at Rest
5651 Log Sistemi için hassas verilerin şifrelenmesi
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class EncryptionManager:
    """Veri şifreleme yöneticisi"""
    
    def __init__(self):
        self._fernet = None
        self._key = None
    
    def _get_encryption_key(self):
        """Şifreleme anahtarını al veya oluştur"""
        if self._key:
            return self._key
        
        # Environment'dan anahtar al
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        
        if not key:
            # Anahtar yoksa oluştur
            key = Fernet.generate_key()
            # Production'da bu anahtarı güvenli bir yerde saklamalısınız
            print(f"⚠️  YENİ ENCRYPTION KEY OLUŞTURULDU: {key.decode()}")
            print("⚠️  Bu anahtarı ENCRYPTION_KEY environment variable'ına ekleyin!")
        
        self._key = key
        return key
    
    def _get_fernet(self):
        """Fernet şifreleme objesi al"""
        if self._fernet:
            return self._fernet
        
        key = self._get_encryption_key()
        self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, data):
        """Veriyi şifrele"""
        if not data:
            return data
        
        try:
            # String'i bytes'a çevir
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(data)
            
            # Base64 encode et (database'de saklamak için)
            return base64.b64encode(encrypted_data).decode('utf-8')
        
        except Exception as e:
            print(f"Encryption error: {e}")
            return data
    
    def decrypt(self, encrypted_data):
        """Şifrelenmiş veriyi çöz"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            # Base64 decode et
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            fernet = self._get_fernet()
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            # Bytes'ı string'e çevir
            return decrypted_data.decode('utf-8')
        
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_data
    
    def encrypt_field(self, field_value):
        """Model field'ı için şifreleme"""
        return self.encrypt(field_value)
    
    def decrypt_field(self, encrypted_value):
        """Model field'ı için şifre çözme"""
        return self.decrypt(encrypted_value)


class FieldEncryption:
    """Django model field'ları için şifreleme mixin"""
    
    def __init__(self, *args, **kwargs):
        self.encryption_manager = EncryptionManager()
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        """Database'den okurken şifreyi çöz"""
        if value is None:
            return value
        
        try:
            return self.encryption_manager.decrypt(value)
        except:
            # Şifreli değilse olduğu gibi döndür (backward compatibility)
            return value
    
    def get_prep_value(self, value):
        """Database'e yazarken şifrele"""
        if value is None:
            return value
        
        return self.encryption_manager.encrypt(value)


class SensitiveDataEncryption:
    """Hassas veri şifreleme sınıfı"""
    
    def __init__(self):
        self.encryption_manager = EncryptionManager()
    
    def encrypt_tc_no(self, tc_no):
        """TC kimlik numarası şifreleme"""
        if not tc_no:
            return tc_no
        return self.encryption_manager.encrypt(tc_no)
    
    def decrypt_tc_no(self, encrypted_tc_no):
        """TC kimlik numarası şifre çözme"""
        if not encrypted_tc_no:
            return encrypted_tc_no
        return self.encryption_manager.decrypt(encrypted_tc_no)
    
    def encrypt_ip_address(self, ip_address):
        """IP adresi şifreleme"""
        if not ip_address:
            return ip_address
        return self.encryption_manager.encrypt(ip_address)
    
    def decrypt_ip_address(self, encrypted_ip):
        """IP adresi şifre çözme"""
        if not encrypted_ip:
            return encrypted_ip
        return self.encryption_manager.decrypt(encrypted_ip)
    
    def encrypt_mac_address(self, mac_address):
        """MAC adresi şifreleme"""
        if not mac_address:
            return mac_address
        return self.encryption_manager.encrypt(mac_address)
    
    def decrypt_mac_address(self, encrypted_mac):
        """MAC adresi şifre çözme"""
        if not encrypted_mac:
            return encrypted_mac
        return self.encryption_manager.decrypt(encrypted_mac)
    
    def encrypt_personal_data(self, data):
        """Kişisel veri şifreleme"""
        if not data:
            return data
        return self.encryption_manager.encrypt(data)
    
    def decrypt_personal_data(self, encrypted_data):
        """Kişisel veri şifre çözme"""
        if not encrypted_data:
            return encrypted_data
        return self.encryption_manager.decrypt(encrypted_data)


# Global encryption manager instance
encryption_manager = EncryptionManager()
sensitive_encryption = SensitiveDataEncryption()


def encrypt_data(data):
    """Veri şifreleme helper function"""
    return encryption_manager.encrypt(data)


def decrypt_data(encrypted_data):
    """Veri şifre çözme helper function"""
    return encryption_manager.decrypt(encrypted_data)


def encrypt_tc_no(tc_no):
    """TC kimlik numarası şifreleme helper"""
    return sensitive_encryption.encrypt_tc_no(tc_no)


def decrypt_tc_no(encrypted_tc_no):
    """TC kimlik numarası şifre çözme helper"""
    return sensitive_encryption.decrypt_tc_no(encrypted_tc_no)


def encrypt_ip_address(ip_address):
    """IP adresi şifreleme helper"""
    return sensitive_encryption.encrypt_ip_address(ip_address)


def decrypt_ip_address(encrypted_ip):
    """IP adresi şifre çözme helper"""
    return sensitive_encryption.decrypt_ip_address(encrypted_ip)


def encrypt_mac_address(mac_address):
    """MAC adresi şifreleme helper"""
    return sensitive_encryption.encrypt_mac_address(mac_address)


def decrypt_mac_address(encrypted_mac):
    """MAC adresi şifre çözme helper"""
    return sensitive_encryption.decrypt_mac_address(encrypted_mac)
