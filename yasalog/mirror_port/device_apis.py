"""
Cihaz API Entegrasyonları
Cisco, MikroTik, Fortinet gibi cihazlar için mirror port konfigürasyonu
"""

import requests
import json
import re
import time
from datetime import datetime
from django.utils import timezone
from .models import MirrorDevice, MirrorConfiguration, MirrorLog
import logging

# Opsiyonel imports
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

try:
    import telnetlib
    TELNET_AVAILABLE = True
except ImportError:
    TELNET_AVAILABLE = False

logger = logging.getLogger(__name__)


class DeviceAPI:
    """Cihaz API base sınıfı"""
    
    def __init__(self, device):
        self.device = device
        self.connection = None
    
    def connect(self):
        """Cihaza bağlanır"""
        raise NotImplementedError
    
    def disconnect(self):
        """Cihaz bağlantısını kapatır"""
        raise NotImplementedError
    
    def configure_mirror_port(self, config):
        """Mirror port konfigürasyonu yapar"""
        raise NotImplementedError
    
    def get_mirror_status(self):
        """Mirror port durumunu getirir"""
        raise NotImplementedError
    
    def test_connection(self):
        """Bağlantı testi yapar"""
        try:
            self.connect()
            result = self.get_mirror_status()
            self.disconnect()
            return {'success': True, 'status': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class CiscoAPI(DeviceAPI):
    """Cisco cihazları için API"""
    
    def connect(self):
        """SSH ile Cisco cihaza bağlanır"""
        if not PARAMIKO_AVAILABLE:
            raise Exception("Paramiko kütüphanesi yüklü değil. 'pip install paramiko' komutu ile yükleyin.")
        
        try:
            self.connection = paramiko.SSHClient()
            self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.connection.connect(
                hostname=self.device.ip_address,
                port=self.device.ssh_port or 22,
                username=self.device.username,
                password=self.device.password,
                timeout=30
            )
            
            # Enable mode'a geç
            shell = self.connection.invoke_shell()
            shell.send('enable\n')
            shell.send(f'{self.device.enable_password}\n')
            shell.send('terminal length 0\n')
            
            return shell
            
        except Exception as e:
            logger.error(f"Cisco bağlantı hatası: {str(e)}")
            raise Exception(f"Cisco bağlantı hatası: {str(e)}")
    
    def disconnect(self):
        """SSH bağlantısını kapatır"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def configure_mirror_port(self, config):
        """Cisco SPAN konfigürasyonu"""
        try:
            shell = self.connect()
            
            # Mevcut SPAN konfigürasyonlarını temizle
            shell.send('no monitor session 1\n')
            
            # Yeni SPAN konfigürasyonu
            commands = [
                f'monitor session 1 source interface {config.source_ports}',
                f'monitor session 1 destination interface {config.destination_port}',
                'monitor session 1 source vlan 1-4094',  # Tüm VLAN'lar
                'monitor session 1 filter vlan 1-4094',
                'monitor session 1 source direction both',
                'monitor session 1 destination encapsulation replicate',
                'monitor session 1 destination ingress vlan 1'
            ]
            
            for cmd in commands:
                shell.send(f'{cmd}\n')
                time.sleep(0.5)
            
            # Konfigürasyonu kaydet
            shell.send('write memory\n')
            shell.send('exit\n')
            
            self.disconnect()
            
            # Log kaydet
            MirrorLog.objects.create(
                device=self.device,
                configuration=config,
                action='CONFIGURE',
                message='Cisco SPAN konfigürasyonu başarılı',
                details={'commands': commands},
                success=True
            )
            
            return {'success': True, 'message': 'Cisco SPAN konfigürasyonu başarılı'}
            
        except Exception as e:
            logger.error(f"Cisco SPAN konfigürasyon hatası: {str(e)}")
            
            # Hata logu kaydet
            MirrorLog.objects.create(
                device=self.device,
                configuration=config,
                action='CONFIGURE',
                message=f'Cisco SPAN konfigürasyon hatası: {str(e)}',
                details={'error': str(e)},
                success=False
            )
            
            return {'success': False, 'error': str(e)}
    
    def get_mirror_status(self):
        """Cisco SPAN durumunu getirir"""
        try:
            shell = self.connect()
            
            # SPAN durumunu kontrol et
            shell.send('show monitor session 1\n')
            time.sleep(2)
            
            output = shell.recv(4096).decode('utf-8')
            self.disconnect()
            
            # Output'u parse et
            status = {
                'active': 'Session 1' in output,
                'source_ports': self._extract_source_ports(output),
                'destination_port': self._extract_destination_port(output),
                'status': 'Active' if 'Session 1' in output else 'Inactive'
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Cisco durum kontrol hatası: {str(e)}")
            return {'active': False, 'error': str(e)}
    
    def _extract_source_ports(self, output):
        """Source port'ları çıkarır"""
        match = re.search(r'source interface (\S+)', output)
        return match.group(1) if match else ''
    
    def _extract_destination_port(self, output):
        """Destination port'u çıkarır"""
        match = re.search(r'destination interface (\S+)', output)
        return match.group(1) if match else ''


class MikroTikAPI(DeviceAPI):
    """MikroTik cihazları için API"""
    
    def connect(self):
        """MikroTik API'ye bağlanır"""
        try:
            # MikroTik API endpoint
            api_url = f"http://{self.device.ip_address}/rest"
            
            # API token ile bağlantı
            headers = {
                'Authorization': f'Basic {self.device.api_token}',
                'Content-Type': 'application/json'
            }
            
            self.connection = {
                'url': api_url,
                'headers': headers
            }
            
            return self.connection
            
        except Exception as e:
            logger.error(f"MikroTik bağlantı hatası: {str(e)}")
            raise Exception(f"MikroTik bağlantı hatası: {str(e)}")
    
    def disconnect(self):
        """MikroTik bağlantısını kapatır"""
        self.connection = None
    
    def configure_mirror_port(self, config):
        """MikroTik mirror port konfigürasyonu"""
        try:
            conn = self.connect()
            
            # Mevcut mirror konfigürasyonlarını sil
            requests.delete(
                f"{conn['url']}/interface/mirror",
                headers=conn['headers']
            )
            
            # Yeni mirror konfigürasyonu
            mirror_config = {
                'name': 'mirror1',
                'mirror-to': config.destination_port,
                'disabled': False
            }
            
            # Mirror interface oluştur
            response = requests.put(
                f"{conn['url']}/interface/mirror",
                headers=conn['headers'],
                json=mirror_config
            )
            
            if response.status_code == 201:
                # Source port'ları mirror'a ekle
                for source_port in config.source_ports.split(','):
                    port_config = {
                        'interface': source_port.strip(),
                        'mirror': 'mirror1'
                    }
                    
                    requests.put(
                        f"{conn['url']}/interface/mirror/port",
                        headers=conn['headers'],
                        json=port_config
                    )
                
                self.disconnect()
                
                # Log kaydet
                MirrorLog.objects.create(
                    device=self.device,
                    configuration=config,
                    action='CONFIGURE',
                    message='MikroTik mirror konfigürasyonu başarılı',
                    details={'config': mirror_config},
                    success=True
                )
                
                return {'success': True, 'message': 'MikroTik mirror konfigürasyonu başarılı'}
            else:
                raise Exception(f"API hatası: {response.status_code}")
                
        except Exception as e:
            logger.error(f"MikroTik mirror konfigürasyon hatası: {str(e)}")
            
            # Hata logu kaydet
            MirrorLog.objects.create(
                device=self.device,
                configuration=config,
                action='CONFIGURE',
                message=f'MikroTik mirror konfigürasyon hatası: {str(e)}',
                details={'error': str(e)},
                success=False
            )
            
            return {'success': False, 'error': str(e)}
    
    def get_mirror_status(self):
        """MikroTik mirror durumunu getirir"""
        try:
            conn = self.connect()
            
            # Mirror durumunu kontrol et
            response = requests.get(
                f"{conn['url']}/interface/mirror",
                headers=conn['headers']
            )
            
            if response.status_code == 200:
                mirrors = response.json()
                
                status = {
                    'active': len(mirrors) > 0,
                    'mirror_count': len(mirrors),
                    'status': 'Active' if mirrors else 'Inactive',
                    'mirrors': mirrors
                }
                
                self.disconnect()
                return status
            else:
                raise Exception(f"API hatası: {response.status_code}")
                
        except Exception as e:
            logger.error(f"MikroTik durum kontrol hatası: {str(e)}")
            return {'active': False, 'error': str(e)}


class FortinetAPI(DeviceAPI):
    """Fortinet cihazları için API"""
    
    def connect(self):
        """Fortinet API'ye bağlanır"""
        try:
            # Fortinet API endpoint
            api_url = f"https://{self.device.ip_address}/api/v2"
            
            # API key ile bağlantı
            headers = {
                'Authorization': f'Bearer {self.device.api_token}',
                'Content-Type': 'application/json'
            }
            
            self.connection = {
                'url': api_url,
                'headers': headers
            }
            
            return self.connection
            
        except Exception as e:
            logger.error(f"Fortinet bağlantı hatası: {str(e)}")
            raise Exception(f"Fortinet bağlantı hatası: {str(e)}")
    
    def disconnect(self):
        """Fortinet bağlantısını kapatır"""
        self.connection = None
    
    def configure_mirror_port(self, config):
        """Fortinet port mirroring konfigürasyonu"""
        try:
            conn = self.connect()
            
            # Port mirroring konfigürasyonu
            mirror_config = {
                'name': 'port-mirror-1',
                'src-ingress': config.source_ports.split(','),
                'src-egress': config.source_ports.split(','),
                'dst': config.destination_port,
                'status': 'enable'
            }
            
            # Port mirroring oluştur
            response = requests.post(
                f"{conn['url']}/system/interface/port-mirror",
                headers=conn['headers'],
                json=mirror_config
            )
            
            if response.status_code == 200:
                self.disconnect()
                
                # Log kaydet
                MirrorLog.objects.create(
                    device=self.device,
                    configuration=config,
                    action='CONFIGURE',
                    message='Fortinet port mirroring konfigürasyonu başarılı',
                    details={'config': mirror_config},
                    success=True
                )
                
                return {'success': True, 'message': 'Fortinet port mirroring konfigürasyonu başarılı'}
            else:
                raise Exception(f"API hatası: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Fortinet port mirroring konfigürasyon hatası: {str(e)}")
            
            # Hata logu kaydet
            MirrorLog.objects.create(
                device=self.device,
                configuration=config,
                action='CONFIGURE',
                message=f'Fortinet port mirroring konfigürasyon hatası: {str(e)}',
                details={'error': str(e)},
                success=False
            )
            
            return {'success': False, 'error': str(e)}
    
    def get_mirror_status(self):
        """Fortinet port mirroring durumunu getirir"""
        try:
            conn = self.connect()
            
            # Port mirroring durumunu kontrol et
            response = requests.get(
                f"{conn['url']}/system/interface/port-mirror",
                headers=conn['headers']
            )
            
            if response.status_code == 200:
                mirrors = response.json()
                
                status = {
                    'active': len(mirrors.get('results', [])) > 0,
                    'mirror_count': len(mirrors.get('results', [])),
                    'status': 'Active' if mirrors.get('results') else 'Inactive',
                    'mirrors': mirrors.get('results', [])
                }
                
                self.disconnect()
                return status
            else:
                raise Exception(f"API hatası: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Fortinet durum kontrol hatası: {str(e)}")
            return {'active': False, 'error': str(e)}


class DeviceAPIFactory:
    """Cihaz API Factory"""
    
    @staticmethod
    def create_device_api(device):
        """Cihaz tipine göre API client oluşturur"""
        if device.device_type == 'CISCO':
            return CiscoAPI(device)
        elif device.device_type == 'MIKROTIK':
            return MikroTikAPI(device)
        elif device.device_type == 'FORTINET':
            return FortinetAPI(device)
        else:
            raise Exception(f"Desteklenmeyen cihaz tipi: {device.device_type}")


class MirrorPortManager:
    """Mirror port yöneticisi"""
    
    def __init__(self, configuration):
        self.configuration = configuration
        self.device_apis = {}
    
    def configure_all_devices(self):
        """Tüm cihazlarda mirror port konfigürasyonu yapar"""
        results = []
        
        for device in self.configuration.devices.all():
            try:
                api = DeviceAPIFactory.create_device_api(device)
                result = api.configure_mirror_port(self.configuration)
                results.append({
                    'device': device.name,
                    'success': result['success'],
                    'message': result.get('message', ''),
                    'error': result.get('error', '')
                })
            except Exception as e:
                results.append({
                    'device': device.name,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def get_all_status(self):
        """Tüm cihazların mirror port durumunu getirir"""
        statuses = []
        
        for device in self.configuration.devices.all():
            try:
                api = DeviceAPIFactory.create_device_api(device)
                status = api.get_mirror_status()
                statuses.append({
                    'device': device.name,
                    'status': status
                })
            except Exception as e:
                statuses.append({
                    'device': device.name,
                    'error': str(e)
                })
        
        return statuses
