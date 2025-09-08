"""
VMware vSphere Entegrasyonu
VMware ESXi ve vCenter sunucularıyla iletişim kurar
"""

import ssl
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

logger = logging.getLogger(__name__)

@dataclass
class VMwareDevice:
    """VMware cihaz bilgileri"""
    name: str
    host: str
    username: str
    password: str
    port: int = 443
    verify_ssl: bool = False

@dataclass
class VMInfo:
    """Sanal makine bilgileri"""
    vm_id: str
    name: str
    power_state: str
    cpu_count: int
    memory_mb: int
    guest_os: str
    ip_address: str
    tools_status: str
    folder: str
    resource_pool: str
    datastore: str

@dataclass
class HostInfo:
    """ESXi host bilgileri"""
    host_id: str
    name: str
    power_state: str
    cpu_model: str
    cpu_count: int
    memory_mb: int
    connection_state: str
    maintenance_mode: bool

@dataclass
class DatastoreInfo:
    """Datastore bilgileri"""
    datastore_id: str
    name: str
    capacity_mb: int
    free_space_mb: int
    type: str
    url: str

class VMwareIntegration:
    """VMware vSphere API entegrasyonu"""
    
    def __init__(self, device: VMwareDevice):
        self.device = device
        self.service_instance = None
        self.content = None
        
    def connect(self) -> bool:
        """VMware sunucusuna bağlanır"""
        try:
            # SSL sertifika doğrulamasını kapat
            if not self.device.verify_ssl:
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                ssl_context.verify_mode = ssl.CERT_NONE
            else:
                ssl_context = None
            
            # Bağlantı kur
            self.service_instance = SmartConnect(
                host=self.device.host,
                user=self.device.username,
                pwd=self.device.password,
                port=self.device.port,
                sslContext=ssl_context
            )
            
            self.content = self.service_instance.RetrieveContent()
            logger.info(f"VMware bağlantısı başarılı: {self.device.host}")
            return True
            
        except Exception as e:
            logger.error(f"VMware bağlantı hatası: {e}")
            return False
    
    def disconnect(self):
        """VMware bağlantısını kapatır"""
        if self.service_instance:
            Disconnect(self.service_instance)
            self.service_instance = None
            self.content = None
    
    def get_vms(self) -> List[VMInfo]:
        """Tüm sanal makineleri listeler"""
        try:
            if not self.content:
                if not self.connect():
                    return []
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.VirtualMachine], True
            )
            
            vms = []
            for vm in container.view:
                vm_info = VMInfo(
                    vm_id=vm._moId,
                    name=vm.name,
                    power_state=vm.runtime.powerState,
                    cpu_count=vm.config.hardware.numCPU,
                    memory_mb=vm.config.hardware.memoryMB,
                    guest_os=vm.config.guestFullName or "Unknown",
                    ip_address=vm.guest.ipAddress or "N/A",
                    tools_status=vm.guest.toolsStatus or "Unknown",
                    folder=vm.parent.name if vm.parent else "N/A",
                    resource_pool=vm.resourcePool.name if vm.resourcePool else "N/A",
                    datastore=", ".join([ds.name for ds in vm.datastore]) if vm.datastore else "N/A"
                )
                vms.append(vm_info)
            
            container.Destroy()
            return vms
            
        except Exception as e:
            logger.error(f"VM listesi çekme hatası: {e}")
            return []
    
    def get_hosts(self) -> List[HostInfo]:
        """Tüm ESXi host'ları listeler"""
        try:
            if not self.content:
                if not self.connect():
                    return []
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.HostSystem], True
            )
            
            hosts = []
            for host in container.view:
                host_info = HostInfo(
                    host_id=host._moId,
                    name=host.name,
                    power_state=host.runtime.powerState,
                    cpu_model=host.hardware.cpuInfo.cpuModel[0] if host.hardware.cpuInfo.cpuModel else "Unknown",
                    cpu_count=host.hardware.cpuInfo.numCpuCores,
                    memory_mb=host.hardware.memorySize // (1024 * 1024),
                    connection_state=host.runtime.connectionState,
                    maintenance_mode=host.runtime.inMaintenanceMode
                )
                hosts.append(host_info)
            
            container.Destroy()
            return hosts
            
        except Exception as e:
            logger.error(f"Host listesi çekme hatası: {e}")
            return []
    
    def get_datastores(self) -> List[DatastoreInfo]:
        """Tüm datastore'ları listeler"""
        try:
            if not self.content:
                if not self.connect():
                    return []
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.Datastore], True
            )
            
            datastores = []
            for ds in container.view:
                ds_info = DatastoreInfo(
                    datastore_id=ds._moId,
                    name=ds.name,
                    capacity_mb=ds.summary.capacity // (1024 * 1024),
                    free_space_mb=ds.summary.freeSpace // (1024 * 1024),
                    type=ds.summary.type,
                    url=ds.summary.url
                )
                datastores.append(ds_info)
            
            container.Destroy()
            return datastores
            
        except Exception as e:
            logger.error(f"Datastore listesi çekme hatası: {e}")
            return []
    
    def power_on_vm(self, vm_name: str) -> bool:
        """Sanal makineyi açar"""
        try:
            if not self.content:
                if not self.connect():
                    return False
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.VirtualMachine], True
            )
            
            for vm in container.view:
                if vm.name == vm_name:
                    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                        task = vm.PowerOn()
                        # Task'ın tamamlanmasını bekle
                        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                            pass
                        
                        if task.info.state == vim.TaskInfo.State.success:
                            logger.info(f"VM açıldı: {vm_name}")
                            container.Destroy()
                            return True
                        else:
                            logger.error(f"VM açma hatası: {task.info.error}")
                            container.Destroy()
                            return False
            
            container.Destroy()
            logger.warning(f"VM bulunamadı: {vm_name}")
            return False
            
        except Exception as e:
            logger.error(f"VM açma hatası: {e}")
            return False
    
    def power_off_vm(self, vm_name: str) -> bool:
        """Sanal makineyi kapatır"""
        try:
            if not self.content:
                if not self.connect():
                    return False
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.VirtualMachine], True
            )
            
            for vm in container.view:
                if vm.name == vm_name:
                    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                        task = vm.PowerOff()
                        # Task'ın tamamlanmasını bekle
                        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                            pass
                        
                        if task.info.state == vim.TaskInfo.State.success:
                            logger.info(f"VM kapatıldı: {vm_name}")
                            container.Destroy()
                            return True
                        else:
                            logger.error(f"VM kapatma hatası: {task.info.error}")
                            container.Destroy()
                            return False
            
            container.Destroy()
            logger.warning(f"VM bulunamadı: {vm_name}")
            return False
            
        except Exception as e:
            logger.error(f"VM kapatma hatası: {e}")
            return False
    
    def restart_vm(self, vm_name: str) -> bool:
        """Sanal makineyi yeniden başlatır"""
        try:
            if not self.content:
                if not self.connect():
                    return False
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.VirtualMachine], True
            )
            
            for vm in container.view:
                if vm.name == vm_name:
                    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                        task = vm.Reset()
                        # Task'ın tamamlanmasını bekle
                        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                            pass
                        
                        if task.info.state == vim.TaskInfo.State.success:
                            logger.info(f"VM yeniden başlatıldı: {vm_name}")
                            container.Destroy()
                            return True
                        else:
                            logger.error(f"VM restart hatası: {task.info.error}")
                            container.Destroy()
                            return False
            
            container.Destroy()
            logger.warning(f"VM bulunamadı: {vm_name}")
            return False
            
        except Exception as e:
            logger.error(f"VM restart hatası: {e}")
            return False
    
    def get_vm_performance(self, vm_name: str, metric: str = "cpu") -> Dict:
        """Sanal makine performans metriklerini çeker"""
        try:
            if not self.content:
                if not self.connect():
                    return {}
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.VirtualMachine], True
            )
            
            for vm in container.view:
                if vm.name == vm_name:
                    # Performans metriklerini çek
                    perf_manager = self.content.perfManager
                    metric_ids = []
                    
                    if metric == "cpu":
                        metric_ids.append(vim.PerformanceManager.MetricId(counterId=6, instance="*"))
                    elif metric == "memory":
                        metric_ids.append(vim.PerformanceManager.MetricId(counterId=24, instance="*"))
                    elif metric == "network":
                        metric_ids.append(vim.PerformanceManager.MetricId(counterId=32, instance="*"))
                    
                    if metric_ids:
                        query = vim.PerformanceManager.QuerySpec(
                            entity=vm,
                            metricId=metric_ids,
                            startTime=None,
                            endTime=None,
                            maxSample=10
                        )
                        
                        result = perf_manager.QueryPerf(querySpec=[query])
                        if result:
                            return {
                                'vm_name': vm_name,
                                'metric': metric,
                                'samples': len(result[0].value),
                                'data': result[0].value
                            }
            
            container.Destroy()
            return {}
            
        except Exception as e:
            logger.error(f"Performans metrik çekme hatası: {e}")
            return {}
    
    def create_snapshot(self, vm_name: str, snapshot_name: str, description: str = "") -> bool:
        """Sanal makine için snapshot oluşturur"""
        try:
            if not self.content:
                if not self.connect():
                    return False
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.VirtualMachine], True
            )
            
            for vm in container.view:
                if vm.name == vm_name:
                    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                        task = vm.CreateSnapshot(
                            name=snapshot_name,
                            description=description,
                            memory=True,
                            quiesce=True
                        )
                        
                        # Task'ın tamamlanmasını bekle
                        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                            pass
                        
                        if task.info.state == vim.TaskInfo.State.success:
                            logger.info(f"Snapshot oluşturuldu: {vm_name} - {snapshot_name}")
                            container.Destroy()
                            return True
                        else:
                            logger.error(f"Snapshot oluşturma hatası: {task.info.error}")
                            container.Destroy()
                            return False
            
            container.Destroy()
            logger.warning(f"VM bulunamadı: {vm_name}")
            return False
            
        except Exception as e:
            logger.error(f"Snapshot oluşturma hatası: {e}")
            return False
    
    def get_snapshots(self, vm_name: str) -> List[Dict]:
        """Sanal makine snapshot'larını listeler"""
        try:
            if not self.content:
                if not self.connect():
                    return []
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.VirtualMachine], True
            )
            
            for vm in container.view:
                if vm.name == vm_name:
                    snapshots = []
                    if vm.snapshot:
                        for snapshot in vm.snapshot.rootSnapshotList:
                            snapshots.append({
                                'name': snapshot.name,
                                'description': snapshot.description or "",
                                'create_time': snapshot.createTime.isoformat(),
                                'power_state': snapshot.state
                            })
                    
                    container.Destroy()
                    return snapshots
            
            container.Destroy()
            return []
            
        except Exception as e:
            logger.error(f"Snapshot listesi çekme hatası: {e}")
            return []
    
    def get_clusters(self) -> List[Dict]:
        """Cluster bilgilerini çeker"""
        try:
            if not self.content:
                if not self.connect():
                    return []
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.ClusterComputeResource], True
            )
            
            clusters = []
            for cluster in container.view:
                cluster_info = {
                    'cluster_id': cluster._moId,
                    'name': cluster.name,
                    'host_count': len(cluster.host),
                    'vm_count': len(cluster.vm),
                    'drs_enabled': cluster.configuration.drsConfig.enabled,
                    'ha_enabled': cluster.configuration.dasConfig.enabled
                }
                clusters.append(cluster_info)
            
            container.Destroy()
            return clusters
            
        except Exception as e:
            logger.error(f"Cluster listesi çekme hatası: {e}")
            return []
    
    def get_resource_pools(self) -> List[Dict]:
        """Resource pool bilgilerini çeker"""
        try:
            if not self.content:
                if not self.connect():
                    return []
            
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.ResourcePool], True
            )
            
            resource_pools = []
            for rp in container.view:
                rp_info = {
                    'pool_id': rp._moId,
                    'name': rp.name,
                    'cpu_limit': rp.runtime.cpu.maxUsage,
                    'memory_limit': rp.runtime.memory.maxUsage,
                    'cpu_used': rp.runtime.cpu.overallUsage,
                    'memory_used': rp.runtime.memory.overallUsage
                }
                resource_pools.append(rp_info)
            
            container.Destroy()
            return resource_pools
            
        except Exception as e:
            logger.error(f"Resource pool listesi çekme hatası: {e}")
            return []
