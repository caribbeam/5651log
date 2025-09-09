"""
TSA Konfigürasyon Dosyası
Gerçek TSA servisleri için ayarlar
"""

import os
from django.conf import settings

# TSA Konfigürasyonları
TSA_CONFIGS = {
    'TUBITAK': {
        'enabled': False,  # Gerçek kullanım için True yapın
        'api_endpoint': 'https://tsa.tubitak.gov.tr/api/timestamp',
        'api_key': os.getenv('TUBITAK_TSA_API_KEY', ''),
        'username': os.getenv('TUBITAK_TSA_USERNAME', ''),
        'password': os.getenv('TUBITAK_TSA_PASSWORD', ''),
        'cert_path': os.path.join(settings.BASE_DIR, 'certs', 'tubitak_tsa.crt'),
        'key_path': os.path.join(settings.BASE_DIR, 'certs', 'tubitak_tsa.key'),
        'ca_cert_path': os.path.join(settings.BASE_DIR, 'certs', 'tubitak_ca.crt'),
        'timeout': 30,
        'retry_count': 3,
        'description': 'TÜBİTAK TSA Servisi'
    },
    
    'TURKTRUST': {
        'enabled': False,  # Gerçek kullanım için True yapın
        'api_endpoint': 'https://tsa.turktrust.com.tr/api/timestamp',
        'api_key': os.getenv('TURKTRUST_TSA_API_KEY', ''),
        'username': os.getenv('TURKTRUST_TSA_USERNAME', ''),
        'password': os.getenv('TURKTRUST_TSA_PASSWORD', ''),
        'cert_path': os.path.join(settings.BASE_DIR, 'certs', 'turktrust_tsa.crt'),
        'key_path': os.path.join(settings.BASE_DIR, 'certs', 'turktrust_tsa.key'),
        'ca_cert_path': os.path.join(settings.BASE_DIR, 'certs', 'turktrust_ca.crt'),
        'timeout': 30,
        'retry_count': 3,
        'description': 'TurkTrust TSA Servisi'
    },
    
    'CUSTOM': {
        'enabled': True,  # Local test için aktif
        'api_endpoint': 'http://localhost:8000/timestamp/api/timestamp/',
        'api_key': 'test-key-123',
        'username': 'test-user',
        'password': 'test-pass',
        'timeout': 10,
        'retry_count': 1,
        'description': 'Local Test TSA Servisi'
    }
}

# Varsayılan TSA seçimi
DEFAULT_TSA = 'CUSTOM'  # Gerçek kullanım için 'TUBITAK' veya 'TURKTRUST'

# TSA Seçim kriterleri
TSA_SELECTION_CRITERIA = {
    'priority': ['TUBITAK', 'TURKTRUST', 'CUSTOM'],  # Öncelik sırası
    'fallback_enabled': True,  # Fallback mekanizması
    'load_balancing': False,  # Yük dengeleme
    'health_check_interval': 300,  # Sağlık kontrolü (saniye)
}

# Loglama ayarları
TSA_LOGGING = {
    'enabled': True,
    'level': 'INFO',
    'log_requests': True,
    'log_responses': True,
    'log_errors': True,
    'max_log_size': 1024 * 1024,  # 1MB
}

# Güvenlik ayarları
TSA_SECURITY = {
    'verify_ssl': True,
    'cert_validation': True,
    'signature_validation': True,
    'timestamp_validation': True,
    'nonce_validation': True,
}

# Performans ayarları
TSA_PERFORMANCE = {
    'connection_pool_size': 10,
    'max_retries': 3,
    'timeout': 30,
    'cache_enabled': True,
    'cache_ttl': 3600,  # 1 saat
}
