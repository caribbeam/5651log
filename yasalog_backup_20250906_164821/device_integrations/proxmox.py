"""
Proxmox VE Entegrasyonu
Proxmox Virtual Environment sunucularıyla iletişim kurar
"""

import requests
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

@dataclass
class ProxmoxDevice:
    """Proxmox cihaz bilgileri"""
    name: str
    host: str
    username: str
    password: str
    port: int = 8006
    realm: str = "pam"
    verify_ssl: bool = False

@dataclass
class ProxmoxVM:
    """Proxmox sanal makine bilgileri"""
    vmid: int
    name: str
    status: str
    cpu: float
    memory: int
    disk: int
    uptime: int
    template: bool
    node: str

@dataclass
class ProxmoxContainer:
    """Proxmox container bilgileri"""
    vmid: int
    name: str
    status: str
    cpu: float
    memory: int
    disk: int
    uptime: int
    template: bool
    node: str
    ostype: str

@dataclass
class ProxmoxNode:
    """Proxmox node bilgileri"""
    node_id: str
    name: str
    status: str
    cpu_count: int
    memory_total: int
    memory_used: int
    disk_total: int
    disk_used: int
    uptime: int

class ProxmoxIntegration:
    """Proxmox VE API entegrasyonu"""
    
    def __init__(self, device: ProxmoxDevice):
        self.device = device
        self.base_url = f"https://{device.host}:{device.port}/api2/json"
        self.session = requests.Session()
        self.session.verify = device.verify_ssl
        self.session.timeout = 10  # 10 saniye timeout
        self.auth_token = None
        
    def authenticate(self) -> bool:
        """Proxmox sunucusunda kimlik doğrulaması yapar"""
        try:
            auth_url = f"{self.base_url}/access/ticket"
            auth_data = {
                'username': f"{self.device.username}@{self.device.realm}",
                'password': self.device.password
            }
            
            response = self.session.post(auth_url, data=auth_data)
            if response.status_code == 200:
                auth_result = response.json()
                if auth_result['data']:
                    self.auth_token = auth_result['data']['ticket']
                    csrf_token = auth_result['data']['CSRFPreventionToken']
                    
                    # Session'a token'ları ekle
                    self.session.headers.update({
                        'Cookie': f'PVEAuthCookie={self.auth_token}',
                        'CSRFPreventionToken': csrf_token
                    })
                    
                    logger.info(f"Proxmox kimlik doğrulaması başarılı: {self.device.host}")
                    return True
            
            logger.error(f"Proxmox kimlik doğrulaması başarısız: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Proxmox kimlik doğrulama hatası: {e}")
            return False
    
    def get_nodes(self) -> List[ProxmoxNode]:
        """Tüm node'ları listeler"""
        try:
            if not self.auth_token and not self.authenticate():
                return []
            
            response = self.session.get(f"{self.base_url}/nodes")
            if response.status_code == 200:
                nodes = []
                for node_data in response.json()['data']:
                    node = ProxmoxNode(
                        node_id=node_data['node'],
                        name=node_data['node'],
                        status=node_data.get('status', 'unknown'),
                        cpu_count=node_data.get('maxcpu', 0),
                        memory_total=node_data.get('maxmem', 0),
                        memory_used=node_data.get('mem', 0),
                        disk_total=node_data.get('maxdisk', 0),
                        disk_used=node_data.get('disk', 0),
                        uptime=node_data.get('uptime', 0)
                    )
                    nodes.append(node)
                return nodes
            
            return []
            
        except Exception as e:
            logger.error(f"Node listesi çekme hatası: {e}")
            return []
    
    def get_vms(self, node: str) -> List[ProxmoxVM]:
        """Belirli node'daki tüm VM'leri listeler"""
        try:
            if not self.auth_token and not self.authenticate():
                return []
            
            response = self.session.get(f"{self.base_url}/nodes/{node}/qemu")
            if response.status_code == 200:
                vms = []
                for vm_data in response.json()['data']:
                    vm = ProxmoxVM(
                        vmid=vm_data['vmid'],
                        name=vm_data['name'],
                        status=vm_data['status'],
                        cpu=vm_data.get('cpu', 0.0),
                        memory=vm_data.get('mem', 0),
                        disk=vm_data.get('disk', 0),
                        uptime=vm_data.get('uptime', 0),
                        template=vm_data.get('template', False),
                        node=node
                    )
                    vms.append(vm)
                return vms
            
            return []
            
        except Exception as e:
            logger.error(f"VM listesi çekme hatası: {e}")
            return []
    
    def get_containers(self, node: str) -> List[ProxmoxContainer]:
        """Belirli node'daki tüm container'ları listeler"""
        try:
            if not self.auth_token and not self.authenticate():
                return []
            
            response = self.session.get(f"{self.base_url}/nodes/{node}/lxc")
            if response.status_code == 200:
                containers = []
                for container_data in response.json()['data']:
                    container = ProxmoxContainer(
                        vmid=container_data['vmid'],
                        name=container_data['name'],
                        status=container_data['status'],
                        cpu=container_data.get('cpu', 0.0),
                        memory=container_data.get('mem', 0),
                        disk=container_data.get('disk', 0),
                        uptime=container_data.get('uptime', 0),
                        template=container_data.get('template', False),
                        node=node,
                        ostype=container_data.get('ostype', 'unknown')
                    )
                    containers.append(container)
                return containers
            
            return []
            
        except Exception as e:
            logger.error(f"Container listesi çekme hatası: {e}")
            return []
    
    def start_vm(self, node: str, vmid: int) -> bool:
        """VM'i başlatır"""
        try:
            if not self.auth_token and not self.authenticate():
                return False
            
            response = self.session.post(f"{self.base_url}/nodes/{node}/qemu/{vmid}/status/start")
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"VM başlatma hatası: {e}")
            return False
    
    def stop_vm(self, node: str, vmid: int) -> bool:
        """VM'i durdurur"""
        try:
            if not self.auth_token and not self.authenticate():
                return False
            
            response = self.session.post(f"{self.base_url}/nodes/{node}/qemu/{vmid}/status/stop")
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"VM durdurma hatası: {e}")
            return False
    
    def restart_vm(self, node: str, vmid: int) -> bool:
        """VM'i yeniden başlatır"""
        try:
            if not self.auth_token and not self.authenticate():
                return False
            
            response = self.session.post(f"{self.base_url}/nodes/{node}/qemu/{vmid}/status/reset")
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"VM restart hatası: {e}")
            return False
    
    def start_container(self, node: str, vmid: int) -> bool:
        """Container'ı başlatır"""
        try:
            if not self.auth_token and not self.authenticate():
                return False
            
            response = self.session.post(f"{self.base_url}/nodes/{node}/lxc/{vmid}/status/start")
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Container başlatma hatası: {e}")
            return False
    
    def stop_container(self, node: str, vmid: int) -> bool:
        """Container'ı durdurur"""
        try:
            if not self.auth_token and not self.authenticate():
                return False
            
            response = self.session.post(f"{self.base_url}/nodes/{node}/lxc/{vmid}/status/stop")
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Container durdurma hatası: {e}")
            return False
    
    def get_vm_config(self, node: str, vmid: int) -> Dict:
        """VM konfigürasyonunu çeker"""
        try:
            if not self.auth_token and not self.authenticate():
                return {}
            
            response = self.session.get(f"{self.base_url}/nodes/{node}/qemu/{vmid}/config")
            if response.status_code == 200:
                return response.json()['data']
            
            return {}
            
        except Exception as e:
            logger.error(f"VM konfigürasyon çekme hatası: {e}")
            return {}
    
    def get_container_config(self, node: str, vmid: int) -> Dict:
        """Container konfigürasyonunu çeker"""
        try:
            if not self.auth_token and not self.authenticate():
                return {}
            
            response = self.session.get(f"{self.base_url}/nodes/{node}/lxc/{vmid}/config")
            if response.status_code == 200:
                return response.json()['data']
            
            return {}
            
        except Exception as e:
            logger.error(f"Container konfigürasyon çekme hatası: {e}")
            return {}
    
    def create_vm_snapshot(self, node: str, vmid: int, snapshot_name: str, description: str = "") -> bool:
        """VM için snapshot oluşturur"""
        try:
            if not self.auth_token and not self.authenticate():
                return False
            
            snapshot_data = {
                'snapname': snapshot_name,
                'description': description
            }
            
            response = self.session.post(
                f"{self.base_url}/nodes/{node}/qemu/{vmid}/snapshot",
                data=snapshot_data
            )
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"VM snapshot oluşturma hatası: {e}")
            return False
    
    def get_vm_snapshots(self, node: str, vmid: int) -> List[Dict]:
        """VM snapshot'larını listeler"""
        try:
            if not self.auth_token and not self.authenticate():
                return []
            
            response = self.session.get(f"{self.base_url}/nodes/{node}/qemu/{vmid}/snapshot")
            if response.status_code == 200:
                return response.json()['data']
            
            return []
            
        except Exception as e:
            logger.error(f"VM snapshot listesi çekme hatası: {e}")
            return []
    
    def get_storage_info(self, node: str) -> List[Dict]:
        """Node'daki storage bilgilerini çeker"""
        try:
            if not self.auth_token and not self.authenticate():
                return []
            
            response = self.session.get(f"{self.base_url}/nodes/{node}/storage")
            if response.status_code == 200:
                return response.json()['data']
            
            return []
            
        except Exception as e:
            logger.error(f"Storage bilgisi çekme hatası: {e}")
            return []
    
    def get_network_info(self, node: str) -> List[Dict]:
        """Node'daki network bilgilerini çeker"""
        try:
            if not self.auth_token and not self.authenticate():
                return []
            
            response = self.session.get(f"{self.base_url}/nodes/{node}/network")
            if response.status_code == 200:
                return response.json()['data']
            
            return []
            
        except Exception as e:
            logger.error(f"Network bilgisi çekme hatası: {e}")
            return []
    
    def get_node_status(self, node: str) -> Dict:
        """Node durum bilgilerini çeker"""
        try:
            if not self.auth_token and not self.authenticate():
                return {}
            
            response = self.session.get(f"{self.base_url}/nodes/{node}/status")
            if response.status_code == 200:
                return response.json()['data']
            
            return {}
            
        except Exception as e:
            logger.error(f"Node durum bilgisi çekme hatası: {e}")
            return {}
    
    def get_task_log(self, node: str, task_id: str) -> Dict:
        """Task log bilgilerini çeker"""
        try:
            if not self.auth_token and not self.authenticate():
                return {}
            
            response = self.session.get(f"{self.base_url}/nodes/{node}/tasks/{task_id}/log")
            if response.status_code == 200:
                return response.json()['data']
            
            return {}
            
        except Exception as e:
            logger.error(f"Task log çekme hatası: {e}")
            return {}
    
    def backup_vm(self, node: str, vmid: int, storage: str, compress: bool = True) -> bool:
        """VM yedeği alır"""
        try:
            if not self.auth_token and not self.authenticate():
                return False
            
            backup_data = {
                'storage': storage,
                'compress': '1' if compress else '0'
            }
            
            response = self.session.post(
                f"{self.base_url}/nodes/{node}/qemu/{vmid}/vzdump",
                data=backup_data
            )
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"VM yedekleme hatası: {e}")
            return False
    
    def migrate_vm(self, node: str, vmid: int, target_node: str, target_storage: str = None) -> bool:
        """VM'i başka node'a taşır"""
        try:
            if not self.auth_token and not self.authenticate():
                return False
            
            migrate_data = {
                'target': target_node
            }
            
            if target_storage:
                migrate_data['storage'] = target_storage
            
            response = self.session.post(
                f"{self.base_url}/nodes/{node}/qemu/{vmid}/migrate",
                data=migrate_data
            )
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"VM migration hatası: {e}")
            return False
