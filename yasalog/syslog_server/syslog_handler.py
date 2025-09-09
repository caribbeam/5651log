"""
Syslog Server Handler
UDP/TCP/TLS protokolleri ile syslog mesajlarını işler
"""

import socket
import threading
import ssl
import json
import re
import time
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from .models import SyslogServer, SyslogMessage, SyslogClient, SyslogFilter, SyslogAlert
import logging

logger = logging.getLogger(__name__)


class SyslogHandler:
    """Syslog mesaj işleyici"""
    
    def __init__(self, server_config):
        self.server_config = server_config
        self.running = False
        self.socket = None
        self.threads = []
        
    def start(self):
        """Syslog server'ı başlatır"""
        try:
            if self.server_config.protocol == 'UDP':
                self._start_udp_server()
            elif self.server_config.protocol == 'TCP':
                self._start_tcp_server()
            elif self.server_config.protocol == 'TLS':
                self._start_tls_server()
            else:
                raise Exception(f"Desteklenmeyen protokol: {self.server_config.protocol}")
            
            self.running = True
            logger.info(f"Syslog server başlatıldı: {self.server_config.name}")
            
        except Exception as e:
            logger.error(f"Syslog server başlatma hatası: {str(e)}")
            raise
    
    def stop(self):
        """Syslog server'ı durdurur"""
        self.running = False
        if self.socket:
            self.socket.close()
        
        # Thread'leri bekle
        for thread in self.threads:
            thread.join(timeout=5)
        
        logger.info(f"Syslog server durduruldu: {self.server_config.name}")
    
    def _start_udp_server(self):
        """UDP server başlatır"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.server_config.host, self.server_config.port))
        
        # UDP için tek thread yeterli
        thread = threading.Thread(target=self._udp_listener)
        thread.daemon = True
        thread.start()
        self.threads.append(thread)
    
    def _start_tcp_server(self):
        """TCP server başlatır"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.server_config.host, self.server_config.port))
        self.socket.listen(10)
        
        # TCP için ana thread
        thread = threading.Thread(target=self._tcp_listener)
        thread.daemon = True
        thread.start()
        self.threads.append(thread)
    
    def _start_tls_server(self):
        """TLS server başlatır"""
        # Önce TCP socket oluştur
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind((self.server_config.host, self.server_config.port))
        tcp_socket.listen(10)
        
        # TLS context oluştur
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if self.server_config.certificate_path:
            context.load_cert_chain(
                self.server_config.certificate_path,
                self.server_config.private_key_path
            )
        
        self.socket = context.wrap_socket(tcp_socket, server_side=True)
        
        # TLS için ana thread
        thread = threading.Thread(target=self._tls_listener)
        thread.daemon = True
        thread.start()
        self.threads.append(thread)
    
    def _udp_listener(self):
        """UDP mesaj dinleyicisi"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore')
                self._process_message(message, addr[0])
            except Exception as e:
                if self.running:
                    logger.error(f"UDP listener hatası: {str(e)}")
    
    def _tcp_listener(self):
        """TCP mesaj dinleyicisi"""
        while self.running:
            try:
                client_socket, addr = self.socket.accept()
                thread = threading.Thread(
                    target=self._handle_tcp_client,
                    args=(client_socket, addr[0])
                )
                thread.daemon = True
                thread.start()
                self.threads.append(thread)
            except Exception as e:
                if self.running:
                    logger.error(f"TCP listener hatası: {str(e)}")
    
    def _tls_listener(self):
        """TLS mesaj dinleyicisi"""
        while self.running:
            try:
                client_socket, addr = self.socket.accept()
                thread = threading.Thread(
                    target=self._handle_tls_client,
                    args=(client_socket, addr[0])
                )
                thread.daemon = True
                thread.start()
                self.threads.append(thread)
            except Exception as e:
                if self.running:
                    logger.error(f"TLS listener hatası: {str(e)}")
    
    def _handle_tcp_client(self, client_socket, client_ip):
        """TCP client'ı işler"""
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                message = data.decode('utf-8', errors='ignore')
                self._process_message(message, client_ip)
        except Exception as e:
            logger.error(f"TCP client işleme hatası: {str(e)}")
        finally:
            client_socket.close()
    
    def _handle_tls_client(self, client_socket, client_ip):
        """TLS client'ı işler"""
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                message = data.decode('utf-8', errors='ignore')
                self._process_message(message, client_ip)
        except Exception as e:
            logger.error(f"TLS client işleme hatası: {str(e)}")
        finally:
            client_socket.close()
    
    def _process_message(self, message, client_ip):
        """Syslog mesajını işler"""
        try:
            # Mesajı parse et
            parsed_message = self._parse_syslog_message(message)
            
            # Client'ı bul veya oluştur
            client, created = SyslogClient.objects.get_or_create(
                server=self.server_config,
                ip_address=client_ip,
                defaults={
                    'name': f"Client-{client_ip}",
                    'is_active': True
                }
            )
            
            # Mesajı kaydet
            syslog_message = SyslogMessage.objects.create(
                server=self.server_config,
                client=client,
                raw_message=message,
                parsed_message=parsed_message,
                facility=parsed_message.get('facility', 0),
                severity=parsed_message.get('severity', 0),
                timestamp=parsed_message.get('timestamp', timezone.now()),
                hostname=parsed_message.get('hostname', ''),
                tag=parsed_message.get('tag', ''),
                content=parsed_message.get('content', ''),
                source_ip=client_ip
            )
            
            # Filtreleri kontrol et
            self._check_filters(syslog_message)
            
            # İstatistikleri güncelle
            self._update_statistics(client)
            
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {str(e)}")
    
    def _parse_syslog_message(self, message):
        """Syslog mesajını parse eder"""
        # RFC 3164 format: <priority>timestamp hostname tag: content
        # RFC 5424 format: <priority>version timestamp hostname app-name procid msgid structured-data msg
        
        parsed = {
            'facility': 0,
            'severity': 0,
            'timestamp': timezone.now(),
            'hostname': '',
            'tag': '',
            'content': message,
            'priority': 0
        }
        
        try:
            # Priority kısmını parse et
            priority_match = re.match(r'<(\d+)>', message)
            if priority_match:
                priority = int(priority_match.group(1))
                parsed['priority'] = priority
                parsed['facility'] = priority >> 3
                parsed['severity'] = priority & 7
                
                # Priority kısmını çıkar
                message = message[priority_match.end():]
            
            # Timestamp parse et (basit)
            timestamp_patterns = [
                r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',  # RFC 3164
                r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # RFC 5424
            ]
            
            for pattern in timestamp_patterns:
                match = re.search(pattern, message)
                if match:
                    try:
                        timestamp_str = match.group(1)
                        # Basit timestamp parse
                        parsed['timestamp'] = timezone.now()
                        message = message.replace(timestamp_str, '', 1).strip()
                        break
                    except:
                        pass
            
            # Hostname parse et
            hostname_match = re.match(r'(\S+)\s+', message)
            if hostname_match:
                parsed['hostname'] = hostname_match.group(1)
                message = message[hostname_match.end():]
            
            # Tag ve content parse et
            if ':' in message:
                tag, content = message.split(':', 1)
                parsed['tag'] = tag.strip()
                parsed['content'] = content.strip()
            else:
                parsed['content'] = message.strip()
            
        except Exception as e:
            logger.error(f"Syslog parse hatası: {str(e)}")
        
        return parsed
    
    def _check_filters(self, message):
        """Aktif filtreleri kontrol eder"""
        try:
            filters = SyslogFilter.objects.filter(
                server=self.server_config,
                is_active=True
            )
            
            for filter_obj in filters:
                if self._matches_filter(message, filter_obj):
                    self._trigger_alert(message, filter_obj)
                    
        except Exception as e:
            logger.error(f"Filter kontrol hatası: {str(e)}")
    
    def _matches_filter(self, message, filter_obj):
        """Mesajın filtreye uyup uymadığını kontrol eder"""
        try:
            # Facility kontrolü
            if filter_obj.facility and message.facility != filter_obj.facility:
                return False
            
            # Severity kontrolü
            if filter_obj.severity and message.severity != filter_obj.severity:
                return False
            
            # Hostname kontrolü
            if filter_obj.hostname_pattern and not re.search(
                filter_obj.hostname_pattern, message.hostname
            ):
                return False
            
            # Tag kontrolü
            if filter_obj.tag_pattern and not re.search(
                filter_obj.tag_pattern, message.tag
            ):
                return False
            
            # Content kontrolü
            if filter_obj.content_pattern and not re.search(
                filter_obj.content_pattern, message.content
            ):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Filter match hatası: {str(e)}")
            return False
    
    def _trigger_alert(self, message, filter_obj):
        """Uyarı tetikler"""
        try:
            SyslogAlert.objects.create(
                server=self.server_config,
                filter_obj=filter_obj,
                message=message,
                severity=filter_obj.alert_severity,
                description=f"Filter match: {filter_obj.name}",
                is_resolved=False
            )
            
        except Exception as e:
            logger.error(f"Alert tetikleme hatası: {str(e)}")
    
    def _update_statistics(self, client):
        """İstatistikleri güncelle"""
        try:
            from .models import SyslogStatistics
            
            stats, created = SyslogStatistics.objects.get_or_create(
                server=self.server_config,
                client=client,
                date=timezone.now().date(),
                defaults={
                    'message_count': 0,
                    'error_count': 0,
                    'warning_count': 0,
                    'info_count': 0
                }
            )
            
            stats.message_count += 1
            
            # Son mesajın severity'sine göre sayacı artır
            last_message = SyslogMessage.objects.filter(
                server=self.server_config,
                client=client
            ).order_by('-timestamp').first()
            
            if last_message:
                if last_message.severity <= 3:  # Error
                    stats.error_count += 1
                elif last_message.severity <= 4:  # Warning
                    stats.warning_count += 1
                else:  # Info
                    stats.info_count += 1
            
            stats.save()
            
        except Exception as e:
            logger.error(f"İstatistik güncelleme hatası: {str(e)}")
