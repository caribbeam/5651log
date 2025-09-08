"""
MikroTik RouterOS Entegrasyonu
Gerçek MikroTik cihazlarla iletişim kurar
"""

import requests
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MikroTikDevice:
    """MikroTik cihaz bilgileri"""
    name: str
    ip_address: str
    username: str
    password: str
    port: int = 443
    api_version: str = "v1"
    verify_ssl: bool = False

@dataclass
class FirewallRule:
    """Firewall kural bilgileri"""
    rule_id: str
    chain: str
    action: str
    protocol: str
    src_address: str
    dst_address: str
    src_port: str
    dst_port: str
    comment: str
    disabled: bool
    created_at: str

@dataclass
class InterfaceStatus:
    """Interface durum bilgileri"""
    name: str
    type: str
    status: str
    speed: str
    tx_byte: int
    rx_byte: int
    tx_packet: int
    rx_packet: int

class MikroTikIntegration:
    """MikroTik RouterOS API entegrasyonu"""
    
    def __init__(self, device: MikroTikDevice):
        self.device = device
        self.base_url = f"https://{device.ip_address}:{device.port}/rest"
        self.session = requests.Session()
        self.session.verify = device.verify_ssl
        self.session.auth = (device.username, device.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def test_connection(self) -> bool:
        """Cihaz bağlantısını test eder"""
        try:
            response = self.session.get(f"{self.base_url}/system/resource")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"MikroTik bağlantı hatası: {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """Sistem bilgilerini çeker"""
        try:
            response = self.session.get(f"{self.base_url}/system/resource")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Sistem bilgisi çekme hatası: {e}")
            return {}
    
    def get_firewall_rules(self) -> List[FirewallRule]:
        """Firewall kurallarını çeker"""
        try:
            response = self.session.get(f"{self.base_url}/ip/firewall/filter")
            if response.status_code == 200:
                rules = []
                for rule_data in response.json():
                    rule = FirewallRule(
                        rule_id=rule_data.get('id', ''),
                        chain=rule_data.get('chain', ''),
                        action=rule_data.get('action', ''),
                        protocol=rule_data.get('protocol', ''),
                        src_address=rule_data.get('src-address', ''),
                        dst_address=rule_data.get('dst-address', ''),
                        src_port=rule_data.get('src-port', ''),
                        dst_port=rule_data.get('dst-port', ''),
                        comment=rule_data.get('comment', ''),
                        disabled=rule_data.get('disabled', False),
                        created_at=rule_data.get('creation-time', '')
                    )
                    rules.append(rule)
                return rules
            return []
        except Exception as e:
            logger.error(f"Firewall kuralları çekme hatası: {e}")
            return []
    
    def create_firewall_rule(self, rule_data: Dict) -> bool:
        """Yeni firewall kuralı oluşturur"""
        try:
            response = self.session.post(
                f"{self.base_url}/ip/firewall/filter",
                json=rule_data
            )
            return response.status_code == 201
        except Exception as e:
            logger.error(f"Firewall kuralı oluşturma hatası: {e}")
            return False
    
    def update_firewall_rule(self, rule_id: str, rule_data: Dict) -> bool:
        """Firewall kuralını günceller"""
        try:
            response = self.session.patch(
                f"{self.base_url}/ip/firewall/filter/{rule_id}",
                json=rule_data
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Firewall kuralı güncelleme hatası: {e}")
            return False
    
    def delete_firewall_rule(self, rule_id: str) -> bool:
        """Firewall kuralını siler"""
        try:
            response = self.session.delete(
                f"{self.base_url}/ip/firewall/filter/{rule_id}"
            )
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Firewall kuralı silme hatası: {e}")
            return False
    
    def get_interfaces(self) -> List[InterfaceStatus]:
        """Interface durumlarını çeker"""
        try:
            response = self.session.get(f"{self.base_url}/interface")
            if response.status_code == 200:
                interfaces = []
                for iface_data in response.json():
                    interface = InterfaceStatus(
                        name=iface_data.get('name', ''),
                        type=iface_data.get('type', ''),
                        status=iface_data.get('running', False),
                        speed=iface_data.get('speed', ''),
                        tx_byte=iface_data.get('tx-byte', 0),
                        rx_byte=iface_data.get('rx-byte', 0),
                        tx_packet=iface_data.get('tx-packet', 0),
                        rx_packet=iface_data.get('rx-packet', 0)
                    )
                    interfaces.append(interface)
                return interfaces
            return []
        except Exception as e:
            logger.error(f"Interface bilgisi çekme hatası: {e}")
            return []
    
    def get_hotspot_users(self) -> List[Dict]:
        """Hotspot kullanıcılarını çeker"""
        try:
            response = self.session.get(f"{self.base_url}/ip/hotspot/user")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Hotspot kullanıcıları çekme hatası: {e}")
            return []
    
    def get_hotspot_active(self) -> List[Dict]:
        """Aktif hotspot oturumlarını çeker"""
        try:
            response = self.session.get(f"{self.base_url}/ip/hotspot/active")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Aktif hotspot oturumları çekme hatası: {e}")
            return []
    
    def get_dhcp_leases(self) -> List[Dict]:
        """DHCP lease bilgilerini çeker"""
        try:
            response = self.session.get(f"{self.base_url}/ip/dhcp-server/lease")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"DHCP lease bilgisi çekme hatası: {e}")
            return []
    
    def get_logs(self, limit: int = 100) -> List[Dict]:
        """Sistem loglarını çeker"""
        try:
            response = self.session.get(f"{self.base_url}/log", params={'limit': limit})
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Log çekme hatası: {e}")
            return []
    
    def execute_command(self, command: str) -> Dict:
        """Özel komut çalıştırır"""
        try:
            # MikroTik API'de komut çalıştırma
            response = self.session.post(
                f"{self.base_url}/system/script",
                json={'source': command}
            )
            return {'success': response.status_code == 200, 'response': response.text}
        except Exception as e:
            logger.error(f"Komut çalıştırma hatası: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_bandwidth_usage(self, interface: str, duration: str = "1h") -> Dict:
        """Interface bandwidth kullanımını çeker"""
        try:
            # MikroTik'te bandwidth monitoring
            response = self.session.get(
                f"{self.base_url}/interface/monitor-traffic",
                params={'interface': interface, 'once': ''}
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Bandwidth kullanımı çekme hatası: {e}")
            return {}
    
    def backup_configuration(self) -> str:
        """Konfigürasyon yedeği alır"""
        try:
            response = self.session.post(f"{self.base_url}/system/backup/save")
            if response.status_code == 200:
                return "Yedekleme başarılı"
            return "Yedekleme başarısız"
        except Exception as e:
            logger.error(f"Yedekleme hatası: {e}")
            return f"Yedekleme hatası: {e}"
    
    def restart_interface(self, interface: str) -> bool:
        """Interface'i yeniden başlatır"""
        try:
            response = self.session.post(
                f"{self.base_url}/interface/enable",
                json={'numbers': interface}
            )
            time.sleep(2)
            response = self.session.post(
                f"{self.base_url}/interface/disable",
                json={'numbers': interface}
            )
            time.sleep(2)
            response = self.session.post(
                f"{self.base_url}/interface/enable",
                json={'numbers': interface}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Interface restart hatası: {e}")
            return False
