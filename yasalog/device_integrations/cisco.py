"""
Cisco Cihaz Entegrasyonu
Cisco ASA, IOS, NX-OS cihazlarıyla iletişim kurar
"""

import requests
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from netmiko import ConnectHandler
from netmiko import NetMikoTimeoutException, NetMikoAuthenticationException

logger = logging.getLogger(__name__)

@dataclass
class CiscoDevice:
    """Cisco cihaz bilgileri"""
    name: str
    host: str
    username: str
    password: str
    device_type: str = "cisco_asa"  # cisco_asa, cisco_ios, cisco_nxos
    port: int = 22
    secret: str = ""
    verify_ssl: bool = False

@dataclass
class FirewallRule:
    """Firewall kural bilgileri"""
    rule_id: str
    action: str
    protocol: str
    source: str
    destination: str
    source_port: str
    destination_port: str
    description: str
    enabled: bool

@dataclass
class InterfaceStatus:
    """Interface durum bilgileri"""
    name: str
    status: str
    ip_address: str
    subnet_mask: str
    speed: str
    duplex: str
    description: str

class CiscoIntegration:
    """Cisco cihaz API ve SSH entegrasyonu"""
    
    def __init__(self, device: CiscoDevice):
        self.device = device
        self.session = None
        self.connection = None
        
    def connect_ssh(self) -> bool:
        """SSH ile cihaza bağlanır"""
        try:
            device_config = {
                'device_type': self.device.device_type,
                'host': self.device.host,
                'username': self.device.username,
                'password': self.device.password,
                'port': self.device.port,
                'secret': self.device.secret,
                'timeout': 20,
                'global_delay_factor': 2
            }
            
            self.connection = ConnectHandler(**device_config)
            
            if self.device.secret:
                self.connection.enable()
            
            logger.info(f"Cisco SSH bağlantısı başarılı: {self.device.host}")
            return True
            
        except NetMikoTimeoutException:
            logger.error(f"Cisco SSH timeout: {self.device.host}")
            return False
        except NetMikoAuthenticationException:
            logger.error(f"Cisco SSH authentication hatası: {self.device.host}")
            return False
        except Exception as e:
            logger.error(f"Cisco SSH bağlantı hatası: {e}")
            return False
    
    def disconnect_ssh(self):
        """SSH bağlantısını kapatır"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
    
    def execute_command(self, command: str) -> str:
        """SSH üzerinden komut çalıştırır"""
        try:
            if not self.connection and not self.connect_ssh():
                return ""
            
            output = self.connection.send_command(command)
            return output
            
        except Exception as e:
            logger.error(f"Komut çalıştırma hatası: {e}")
            return ""
    
    def get_interfaces(self) -> List[InterfaceStatus]:
        """Interface durumlarını çeker"""
        try:
            if self.device.device_type == "cisco_asa":
                return self._get_asa_interfaces()
            elif self.device.device_type == "cisco_ios":
                return self._get_ios_interfaces()
            else:
                return self._get_generic_interfaces()
                
        except Exception as e:
            logger.error(f"Interface bilgisi çekme hatası: {e}")
            return []
    
    def _get_asa_interfaces(self) -> List[InterfaceStatus]:
        """ASA interface bilgilerini çeker"""
        try:
            output = self.execute_command("show interface")
            interfaces = []
            
            # ASA interface parsing
            lines = output.split('\n')
            current_interface = None
            
            for line in lines:
                if line.startswith('Interface '):
                    if current_interface:
                        interfaces.append(current_interface)
                    
                    interface_name = line.split()[1]
                    current_interface = InterfaceStatus(
                        name=interface_name,
                        status="unknown",
                        ip_address="",
                        subnet_mask="",
                        speed="",
                        duplex="",
                        description=""
                    )
                
                elif current_interface:
                    if "line protocol is" in line:
                        current_interface.status = "up" if "up" in line else "down"
                    elif "Internet address is" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            current_interface.ip_address = parts[2]
                            current_interface.subnet_mask = parts[3]
                    elif "BW" in line and "Kbps" in line:
                        current_interface.speed = line.strip()
            
            if current_interface:
                interfaces.append(current_interface)
            
            return interfaces
            
        except Exception as e:
            logger.error(f"ASA interface parsing hatası: {e}")
            return []
    
    def _get_ios_interfaces(self) -> List[InterfaceStatus]:
        """IOS interface bilgilerini çeker"""
        try:
            output = self.execute_command("show interfaces")
            interfaces = []
            
            # IOS interface parsing
            lines = output.split('\n')
            current_interface = None
            
            for line in lines:
                if line.startswith('Interface '):
                    if current_interface:
                        interfaces.append(current_interface)
                    
                    interface_name = line.split()[1]
                    current_interface = InterfaceStatus(
                        name=interface_name,
                        status="unknown",
                        ip_address="",
                        subnet_mask="",
                        speed="",
                        duplex="",
                        description=""
                    )
                
                elif current_interface:
                    if "line protocol is" in line:
                        current_interface.status = "up" if "up" in line else "down"
                    elif "Internet address is" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            current_interface.ip_address = parts[2]
                            current_interface.subnet_mask = parts[3]
                    elif "BW" in line and "Kbps" in line:
                        current_interface.speed = line.strip()
                    elif "duplex" in line:
                        current_interface.duplex = line.strip()
            
            if current_interface:
                interfaces.append(current_interface)
            
            return interfaces
            
        except Exception as e:
            logger.error(f"IOS interface parsing hatası: {e}")
            return []
    
    def _get_generic_interfaces(self) -> List[InterfaceStatus]:
        """Genel interface bilgilerini çeker"""
        try:
            output = self.execute_command("show interface brief")
            interfaces = []
            
            lines = output.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('Interface'):
                    parts = line.split()
                    if len(parts) >= 4:
                        interface = InterfaceStatus(
                            name=parts[0],
                            status=parts[1],
                            ip_address=parts[2] if len(parts) > 2 else "",
                            subnet_mask=parts[3] if len(parts) > 3 else "",
                            speed="",
                            duplex="",
                            description=""
                        )
                        interfaces.append(interface)
            
            return interfaces
            
        except Exception as e:
            logger.error(f"Genel interface parsing hatası: {e}")
            return []
    
    def get_firewall_rules(self) -> List[FirewallRule]:
        """Firewall kurallarını çeker"""
        try:
            if self.device.device_type == "cisco_asa":
                return self._get_asa_rules()
            else:
                return self._get_ios_rules()
                
        except Exception as e:
            logger.error(f"Firewall kuralları çekme hatası: {e}")
            return []
    
    def _get_asa_rules(self) -> List[FirewallRule]:
        """ASA access-list kurallarını çeker"""
        try:
            output = self.execute_command("show access-list")
            rules = []
            
            lines = output.split('\n')
            current_rule = None
            
            for line in lines:
                if line.strip() and not line.startswith('access-list'):
                    if current_rule:
                        rules.append(current_rule)
                    
                    parts = line.split()
                    if len(parts) >= 3:
                        rule = FirewallRule(
                            rule_id=parts[1],
                            action="permit" if "permit" in line else "deny",
                            protocol=parts[2] if len(parts) > 2 else "any",
                            source=parts[3] if len(parts) > 3 else "any",
                            destination=parts[4] if len(parts) > 4 else "any",
                            source_port="",
                            destination_port="",
                            description="",
                            enabled=True
                        )
                        current_rule = rule
            
            if current_rule:
                rules.append(current_rule)
            
            return rules
            
        except Exception as e:
            logger.error(f"ASA rule parsing hatası: {e}")
            return []
    
    def _get_ios_rules(self) -> List[FirewallRule]:
        """IOS access-list kurallarını çeker"""
        try:
            output = self.execute_command("show access-lists")
            rules = []
            
            lines = output.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('Standard IP access list'):
                    parts = line.split()
                    if len(parts) >= 3:
                        rule = FirewallRule(
                            rule_id=parts[1],
                            action="permit" if "permit" in line else "deny",
                            protocol="ip",
                            source=parts[2] if len(parts) > 2 else "any",
                            destination="any",
                            source_port="",
                            destination_port="",
                            description="",
                            enabled=True
                        )
                        rules.append(rule)
            
            return rules
            
        except Exception as e:
            logger.error(f"IOS rule parsing hatası: {e}")
            return []
    
    def create_firewall_rule(self, rule_data: Dict) -> bool:
        """Yeni firewall kuralı oluşturur"""
        try:
            if self.device.device_type == "cisco_asa":
                return self._create_asa_rule(rule_data)
            else:
                return self._create_ios_rule(rule_data)
                
        except Exception as e:
            logger.error(f"Firewall kuralı oluşturma hatası: {e}")
            return False
    
    def _create_asa_rule(self, rule_data: Dict) -> bool:
        """ASA'da yeni kural oluşturur"""
        try:
            command = f"access-list {rule_data['rule_id']} {rule_data['action']} {rule_data['protocol']} {rule_data['source']} {rule_data['destination']}"
            
            if rule_data.get('source_port'):
                command += f" eq {rule_data['source_port']}"
            if rule_data.get('destination_port'):
                command += f" eq {rule_data['destination_port']}"
            
            output = self.execute_command(command)
            return "access-list" in output.lower()
            
        except Exception as e:
            logger.error(f"ASA kural oluşturma hatası: {e}")
            return False
    
    def _create_ios_rule(self, rule_data: Dict) -> bool:
        """IOS'ta yeni kural oluşturur"""
        try:
            command = f"access-list {rule_data['rule_id']} {rule_data['action']} {rule_data['source']}"
            
            if rule_data.get('source_port'):
                command += f" eq {rule_data['source_port']}"
            
            output = self.execute_command(command)
            return "access-list" in output.lower()
            
        except Exception as e:
            logger.error(f"IOS kural oluşturma hatası: {e}")
            return False
    
    def get_running_config(self) -> str:
        """Çalışan konfigürasyonu çeker"""
        try:
            if self.device.device_type == "cisco_asa":
                return self.execute_command("show running-config")
            else:
                return self.execute_command("show running-config")
                
        except Exception as e:
            logger.error(f"Konfigürasyon çekme hatası: {e}")
            return ""
    
    def get_startup_config(self) -> str:
        """Başlangıç konfigürasyonunu çeker"""
        try:
            if self.device.device_type == "cisco_asa":
                return self.execute_command("show startup-config")
            else:
                return self.execute_command("show startup-config")
                
        except Exception as e:
            logger.error(f"Startup konfigürasyon çekme hatası: {e}")
            return ""
    
    def save_config(self) -> bool:
        """Konfigürasyonu kaydeder"""
        try:
            if self.device.device_type == "cisco_asa":
                output = self.execute_command("write memory")
            else:
                output = self.execute_command("copy running-config startup-config")
            
            return "successful" in output.lower() or "copied" in output.lower()
            
        except Exception as e:
            logger.error(f"Konfigürasyon kaydetme hatası: {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """Sistem bilgilerini çeker"""
        try:
            info = {}
            
            # Version bilgisi
            version_output = self.execute_command("show version")
            info['version'] = version_output
            
            # Uptime bilgisi
            uptime_output = self.execute_command("show version | include uptime")
            info['uptime'] = uptime_output
            
            # CPU kullanımı
            if self.device.device_type == "cisco_asa":
                cpu_output = self.execute_command("show cpu usage")
            else:
                cpu_output = self.execute_command("show processes cpu")
            info['cpu'] = cpu_output
            
            # Memory kullanımı
            if self.device.device_type == "cisco_asa":
                memory_output = self.execute_command("show memory")
            else:
                memory_output = self.execute_command("show memory statistics")
            info['memory'] = memory_output
            
            return info
            
        except Exception as e:
            logger.error(f"Sistem bilgisi çekme hatası: {e}")
            return {}
    
    def get_arp_table(self) -> List[Dict]:
        """ARP tablosunu çeker"""
        try:
            output = self.execute_command("show arp")
            arp_entries = []
            
            lines = output.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('Protocol'):
                    parts = line.split()
                    if len(parts) >= 4:
                        arp_entry = {
                            'protocol': parts[0],
                            'address': parts[1],
                            'age': parts[2],
                            'hardware_addr': parts[3],
                            'type': parts[4] if len(parts) > 4 else "",
                            'interface': parts[5] if len(parts) > 5 else ""
                        }
                        arp_entries.append(arp_entry)
            
            return arp_entries
            
        except Exception as e:
            logger.error(f"ARP tablosu çekme hatası: {e}")
            return []
    
    def get_routing_table(self) -> List[Dict]:
        """Routing tablosunu çeker"""
        try:
            output = self.execute_command("show route")
            routes = []
            
            lines = output.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('Gateway'):
                    parts = line.split()
                    if len(parts) >= 3:
                        route = {
                            'network': parts[0],
                            'mask': parts[1],
                            'gateway': parts[2],
                            'interface': parts[3] if len(parts) > 3 else "",
                            'metric': parts[4] if len(parts) > 4 else ""
                        }
                        routes.append(route)
            
            return routes
            
        except Exception as e:
            logger.error(f"Routing tablosu çekme hatası: {e}")
            return []
    
    def ping(self, destination: str, count: int = 4) -> Dict:
        """Ping testi yapar"""
        try:
            command = f"ping {destination} repeat {count}"
            output = self.execute_command(command)
            
            # Ping sonuçlarını parse et
            success_rate = 0
            if "Success rate is" in output:
                try:
                    success_line = [line for line in output.split('\n') if "Success rate is" in line][0]
                    success_rate = int(success_line.split('%')[0].split()[-1])
                except:
                    pass
            
            return {
                'destination': destination,
                'count': count,
                'success_rate': success_rate,
                'output': output
            }
            
        except Exception as e:
            logger.error(f"Ping hatası: {e}")
            return {'error': str(e)}
    
    def traceroute(self, destination: str) -> Dict:
        """Traceroute yapar"""
        try:
            command = f"traceroute {destination}"
            output = self.execute_command(command)
            
            return {
                'destination': destination,
                'output': output
            }
            
        except Exception as e:
            logger.error(f"Traceroute hatası: {e}")
            return {'error': str(e)}
