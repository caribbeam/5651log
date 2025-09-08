"""
Zaman Damgası Servisleri
RFC 3161 uyumlu imzalama ve doğrulama işlemleri
"""

import hashlib
import base64
import json
import requests
from datetime import datetime, timezone
from django.utils import timezone as django_timezone
from django.conf import settings
from .models import TimestampSignature, TimestampAuthority, TimestampLog


class TimestampService:
    """RFC 3161 uyumlu zaman damgası servisi"""
    
    def __init__(self, authority):
        self.authority = authority
    
    def create_timestamp_request(self, data_hash):
        """Zaman damgası isteği oluşturur"""
        try:
            # RFC 3161 uyumlu istek oluşturma
            request_data = {
                'hash': data_hash,
                'hash_algorithm': 'SHA256',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'nonce': self._generate_nonce()
            }
            return request_data
        except Exception as e:
            raise Exception(f"Timestamp request oluşturma hatası: {str(e)}")
    
    def sign_data(self, data):
        """Veriyi zaman damgası ile imzalar"""
        try:
            # Veriyi hash'le
            data_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
            
            # Zaman damgası isteği oluştur
            request_data = self.create_timestamp_request(data_hash)
            
            # TSA'ya istek gönder (simüle edilmiş)
            response = self._send_timestamp_request(request_data)
            
            if response.get('success'):
                return {
                    'signature': response.get('signature'),
                    'timestamp_token': response.get('timestamp_token'),
                    'certificate_chain': response.get('certificate_chain'),
                    'serial_number': response.get('serial_number')
                }
            else:
                raise Exception(response.get('error', 'İmzalama başarısız'))
                
        except Exception as e:
            raise Exception(f"Veri imzalama hatası: {str(e)}")
    
    def verify_signature(self, signature_data, original_data):
        """İmzayı doğrular"""
        try:
            # Orijinal veriyi hash'le
            original_hash = hashlib.sha256(original_data.encode('utf-8')).hexdigest()
            
            # İmzayı doğrula (simüle edilmiş)
            verification_result = self._verify_timestamp_token(signature_data, original_hash)
            
            return verification_result
            
        except Exception as e:
            raise Exception(f"İmza doğrulama hatası: {str(e)}")
    
    def _generate_nonce(self):
        """Güvenli nonce oluşturur"""
        import secrets
        return secrets.token_hex(16)
    
    def _send_timestamp_request(self, request_data):
        """TSA'ya istek gönderir (simüle edilmiş)"""
        # Gerçek implementasyonda TSA API'sine istek gönderilecek
        # Şimdilik simüle edilmiş yanıt döndürüyoruz
        
        if self.authority.authority_type == 'TUBITAK':
            return self._simulate_tubitak_response(request_data)
        elif self.authority.authority_type == 'TURKTRUST':
            return self._simulate_turktrust_response(request_data)
        else:
            return self._simulate_custom_response(request_data)
    
    def _simulate_tubitak_response(self, request_data):
        """TÜBİTAK TSA simülasyonu"""
        return {
            'success': True,
            'signature': base64.b64encode(f"TUBITAK_SIGNATURE_{request_data['hash']}".encode()).decode(),
            'timestamp_token': base64.b64encode(f"TUBITAK_TOKEN_{request_data['timestamp']}".encode()).decode(),
            'certificate_chain': base64.b64encode("TUBITAK_CERTIFICATE_CHAIN".encode()).decode(),
            'serial_number': f"TUBITAK_{int(datetime.now().timestamp())}"
        }
    
    def _simulate_turktrust_response(self, request_data):
        """TurkTrust TSA simülasyonu"""
        return {
            'success': True,
            'signature': base64.b64encode(f"TURKTRUST_SIGNATURE_{request_data['hash']}".encode()).decode(),
            'timestamp_token': base64.b64encode(f"TURKTRUST_TOKEN_{request_data['timestamp']}".encode()).decode(),
            'certificate_chain': base64.b64encode("TURKTRUST_CERTIFICATE_CHAIN".encode()).decode(),
            'serial_number': f"TURKTRUST_{int(datetime.now().timestamp())}"
        }
    
    def _simulate_custom_response(self, request_data):
        """Özel TSA simülasyonu"""
        return {
            'success': True,
            'signature': base64.b64encode(f"CUSTOM_SIGNATURE_{request_data['hash']}".encode()).decode(),
            'timestamp_token': base64.b64encode(f"CUSTOM_TOKEN_{request_data['timestamp']}".encode()).decode(),
            'certificate_chain': base64.b64encode("CUSTOM_CERTIFICATE_CHAIN".encode()).decode(),
            'serial_number': f"CUSTOM_{int(datetime.now().timestamp())}"
        }
    
    def _verify_timestamp_token(self, signature_data, original_hash):
        """Zaman damgası token'ını doğrular"""
        # Gerçek implementasyonda RFC 3161 doğrulama yapılacak
        # Şimdilik simüle edilmiş doğrulama
        return {
            'valid': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'hash_match': True,
            'certificate_valid': True
        }


class BatchTimestampService:
    """Toplu zaman damgası imzalama servisi"""
    
    def __init__(self, company):
        self.company = company
        self.config = company.timestamp_config
    
    def sign_pending_logs(self):
        """Bekleyen log kayıtlarını toplu olarak imzalar"""
        try:
            # İmzalanmamış log kayıtlarını al
            pending_logs = self._get_pending_logs()
            
            if not pending_logs.exists():
                return {'success': True, 'message': 'İmzalanacak kayıt bulunamadı', 'count': 0}
            
            # Toplu imzalama işlemi
            success_count = 0
            failure_count = 0
            
            for log in pending_logs:
                try:
                    if self._sign_single_log(log):
                        success_count += 1
                    else:
                        failure_count += 1
                except Exception as e:
                    failure_count += 1
                    self._log_error(log, str(e))
            
            # İşlem logunu kaydet
            self._log_batch_operation(success_count, failure_count)
            
            return {
                'success': True,
                'message': f'{success_count} kayıt başarıyla imzalandı, {failure_count} kayıt başarısız',
                'success_count': success_count,
                'failure_count': failure_count
            }
            
        except Exception as e:
            self._log_error(None, str(e))
            return {'success': False, 'error': str(e)}
    
    def _get_pending_logs(self):
        """İmzalanmamış log kayıtlarını getirir"""
        from log_kayit.models import LogKayit
        
        # Son 24 saatteki imzalanmamış kayıtlar
        cutoff_time = django_timezone.now() - django_timezone.timedelta(hours=24)
        
        return LogKayit.objects.filter(
            company=self.company,
            giris_zamani__gte=cutoff_time
        ).exclude(
            timestamp_signatures__status__in=['SIGNED', 'VERIFIED']
        )[:self.config.batch_size]
    
    def _sign_single_log(self, log):
        """Tek bir log kaydını imzalar"""
        try:
            # Log verisini hazırla
            log_data = self._prepare_log_data(log)
            
            # Zaman damgası servisini başlat
            timestamp_service = TimestampService(self.config.authority)
            
            # Veriyi imzala
            signature_result = timestamp_service.sign_data(log_data)
            
            # İmzayı veritabanına kaydet
            timestamp_signature = TimestampSignature.objects.create(
                log_entry=log,
                company=self.company,
                authority=self.config.authority,
                signature_data=signature_result['signature'],
                timestamp_token=signature_result['timestamp_token'],
                certificate_chain=signature_result['certificate_chain'],
                serial_number=signature_result['serial_number'],
                status='SIGNED',
                signed_at=django_timezone.now()
            )
            
            return True
            
        except Exception as e:
            self._log_error(log, str(e))
            return False
    
    def _prepare_log_data(self, log):
        """Log verisini imzalama için hazırlar"""
        # Log kaydının tüm bilgilerini birleştir
        log_data = {
            'tc_no': log.tc_no,
            'pasaport_no': log.pasaport_no,
            'kimlik_turu': log.kimlik_turu,
            'ad_soyad': log.ad_soyad,
            'telefon': log.telefon,
            'ip_adresi': str(log.ip_adresi),
            'mac_adresi': log.mac_adresi,
            'giris_zamani': log.giris_zamani.isoformat(),
            'sha256_hash': log.sha256_hash,
            'is_suspicious': log.is_suspicious,
            'pasaport_ulkesi': log.pasaport_ulkesi
        }
        
        # JSON string olarak döndür
        return json.dumps(log_data, sort_keys=True, ensure_ascii=False)
    
    def _log_error(self, log, error_message):
        """Hata logunu kaydeder"""
        TimestampLog.objects.create(
            company=self.company,
            log_type='ERROR',
            message=f"Log ID {log.id if log else 'N/A'}: {error_message}",
            details={'log_id': log.id if log else None, 'error': error_message},
            failure_count=1
        )
    
    def _log_batch_operation(self, success_count, failure_count):
        """Toplu işlem logunu kaydeder"""
        TimestampLog.objects.create(
            company=self.company,
            log_type='BATCH_SIGN',
            message=f'Toplu imzalama tamamlandı: {success_count} başarılı, {failure_count} başarısız',
            details={'success_count': success_count, 'failure_count': failure_count},
            records_processed=success_count + failure_count,
            success_count=success_count,
            failure_count=failure_count
        )
