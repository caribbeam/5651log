#!/usr/bin/env python
"""
Gerçek Cihaz Entegrasyon Test Scripti
5651log platformunun gerçek cihazlarla entegrasyonunu test eder
"""

import os
import sys
import django
import json
from datetime import datetime

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yasalog.settings')
django.setup()

from device_integrations.mikrotik import MikroTikIntegration, MikroTikDevice
from device_integrations.vmware import VMwareIntegration, VMwareDevice
from device_integrations.proxmox import ProxmoxIntegration, ProxmoxDevice
from device_integrations.cisco import CiscoIntegration, CiscoDevice

def test_mikrotik_integration():
    """MikroTik entegrasyonunu test eder"""
    print("🔧 MikroTik Entegrasyon Testi")
    print("=" * 50)
    
    # Test cihaz bilgileri (gerçek bilgilerle değiştirin)
    device = MikroTikDevice(
        name="Test Router",
        ip_address="192.168.1.1",
        username="admin",
        password="password",
        port=443,
        verify_ssl=False
    )
    
    try:
        integration = MikroTikIntegration(device)
        
        # Bağlantı testi
        print("📡 Bağlantı testi...")
        if integration.test_connection():
            print("✅ Bağlantı başarılı!")
            
            # Sistem bilgileri
            print("\n💻 Sistem bilgileri...")
            system_info = integration.get_system_info()
            if system_info:
                print(f"   CPU: {system_info.get('cpu-load', 'N/A')}%")
                print(f"   Memory: {system_info.get('free-memory', 'N/A')} bytes")
                print(f"   Uptime: {system_info.get('uptime', 'N/A')}")
            else:
                print("   ❌ Sistem bilgisi alınamadı")
            
            # Interface durumları
            print("\n🌐 Interface durumları...")
            interfaces = integration.get_interfaces()
            for iface in interfaces[:3]:  # İlk 3 interface
                print(f"   {iface.name}: {iface.status} - {iface.speed}")
            
            # Firewall kuralları
            print("\n🛡️ Firewall kuralları...")
            rules = integration.get_firewall_rules()
            print(f"   Toplam {len(rules)} kural bulundu")
            
        else:
            print("❌ Bağlantı başarısız!")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
    
    print()

def test_vmware_integration():
    """VMware entegrasyonunu test eder"""
    print("🖥️ VMware Entegrasyon Testi")
    print("=" * 50)
    
    # Test cihaz bilgileri (gerçek bilgilerle değiştirin)
    device = VMwareDevice(
        name="Test vCenter",
        host="192.168.1.10",
        username="administrator@vsphere.local",
        password="password",
        port=443,
        verify_ssl=False
    )
    
    try:
        integration = VMwareIntegration(device)
        
        # Bağlantı testi
        print("📡 Bağlantı testi...")
        if integration.connect():
            print("✅ Bağlantı başarılı!")
            
            # Host bilgileri
            print("\n🖥️ ESXi Host'ları...")
            hosts = integration.get_hosts()
            for host in hosts[:3]:  # İlk 3 host
                print(f"   {host.name}: {host.power_state} - {host.cpu_count} CPU")
            
            # VM bilgileri
            print("\n💻 Sanal Makineler...")
            vms = integration.get_vms(hosts[0].name if hosts else "localhost")
            for vm in vms[:3]:  # İlk 3 VM
                print(f"   {vm.name}: {vm.power_state} - {vm.cpu_count} CPU, {vm.memory_mb} MB RAM")
            
            # Datastore bilgileri
            print("\n💾 Datastore'lar...")
            datastores = integration.get_datastores()
            for ds in datastores[:3]:  # İlk 3 datastore
                free_gb = ds.free_space_mb // 1024
                total_gb = ds.capacity_mb // 1024
                print(f"   {ds.name}: {free_gb} GB / {total_gb} GB boş")
            
            integration.disconnect()
            
        else:
            print("❌ Bağlantı başarısız!")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
    
    print()

def test_proxmox_integration():
    """Proxmox entegrasyonunu test eder"""
    print("🐧 Proxmox Entegrasyon Testi")
    print("=" * 50)
    
    # Test cihaz bilgileri (gerçek bilgilerle değiştirin)
    device = ProxmoxDevice(
        name="Test Proxmox",
        host="192.168.1.20",
        username="root",
        password="password",
        port=8006,
        realm="pam",
        verify_ssl=False
    )
    
    try:
        integration = ProxmoxIntegration(device)
        
        # Kimlik doğrulama testi
        print("🔐 Kimlik doğrulama testi...")
        if integration.authenticate():
            print("✅ Kimlik doğrulama başarılı!")
            
            # Node bilgileri
            print("\n🖥️ Node'lar...")
            nodes = integration.get_nodes()
            for node in nodes[:3]:  # İlk 3 node
                memory_gb = node.memory_total // (1024 * 1024)
                print(f"   {node.name}: {node.cpu_count} CPU, {memory_gb} GB RAM")
            
            # VM bilgileri
            if nodes:
                print("\n💻 Sanal Makineler...")
                vms = integration.get_vms(nodes[0].name)
                for vm in vms[:3]:  # İlk 3 VM
                    print(f"   {vm.name}: {vm.status} - {vm.cpu} CPU, {vm.memory} MB RAM")
                
                # Container bilgileri
                print("\n📦 Container'lar...")
                containers = integration.get_containers(nodes[0].name)
                for container in containers[:3]:  # İlk 3 container
                    print(f"   {container.name}: {container.status} - {container.ostype}")
            
        else:
            print("❌ Kimlik doğrulama başarısız!")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
    
    print()

def test_cisco_integration():
    """Cisco entegrasyonunu test eder"""
    print("🔴 Cisco Entegrasyon Testi")
    print("=" * 50)
    
    # Test cihaz bilgileri (gerçek bilgilerle değiştirin)
    device = CiscoDevice(
        name="Test ASA",
        host="192.168.1.30",
        username="admin",
        password="password",
        device_type="cisco_asa",
        port=22,
        secret="enable_password"
    )
    
    try:
        integration = CiscoIntegration(device)
        
        # SSH bağlantı testi
        print("📡 SSH bağlantı testi...")
        if integration.connect_ssh():
            print("✅ SSH bağlantısı başarılı!")
            
            # Interface durumları
            print("\n🌐 Interface durumları...")
            interfaces = integration.get_interfaces()
            for iface in interfaces[:3]:  # İlk 3 interface
                print(f"   {iface.name}: {iface.status} - {iface.ip_address}")
            
            # Firewall kuralları
            print("\n🛡️ Firewall kuralları...")
            rules = integration.get_firewall_rules()
            print(f"   Toplam {len(rules)} kural bulundu")
            
            # Sistem bilgileri
            print("\n💻 Sistem bilgileri...")
            system_info = integration.get_system_info()
            if system_info.get('version'):
                print("   ✅ Version bilgisi alındı")
            if system_info.get('cpu'):
                print("   ✅ CPU bilgisi alındı")
            
            integration.disconnect_ssh()
            
        else:
            print("❌ SSH bağlantısı başarısız!")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
    
    print()

def create_demo_devices():
    """Demo cihaz verileri oluşturur"""
    print("🎯 Demo Cihaz Verileri Oluşturuluyor")
    print("=" * 50)
    
    # Bu fonksiyon gerçek cihaz bilgilerini veritabanına kaydeder
    # Şimdilik sadece bilgi veriyoruz
    
    demo_devices = [
        {
            "type": "MikroTik",
            "name": "Ana Router",
            "ip": "192.168.1.1",
            "description": "Ana internet router'ı"
        },
        {
            "type": "VMware",
            "name": "vCenter Server",
            "ip": "192.168.1.10",
            "description": "VMware vCenter sunucusu"
        },
        {
            "type": "Proxmox",
            "name": "Proxmox Cluster",
            "ip": "192.168.1.20",
            "description": "Proxmox VE cluster'ı"
        },
        {
            "type": "Cisco",
            "name": "Firewall ASA",
            "ip": "192.168.1.30",
            "description": "Cisco ASA firewall"
        }
    ]
    
    print("📋 Demo cihaz listesi:")
    for device in demo_devices:
        print(f"   🔹 {device['type']}: {device['name']} ({device['ip']})")
        print(f"      {device['description']}")
    
    print("\n💡 Bu cihazları test etmek için:")
    print("   1. Gerçek IP adreslerini girin")
    print("   2. Kullanıcı adı ve şifreleri girin")
    print("   3. Test scriptini çalıştırın")
    
    print()

def main():
    """Ana test fonksiyonu"""
    print("🚀 5651log Gerçek Cihaz Entegrasyon Testi")
    print("=" * 60)
    print(f"📅 Test Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Demo cihaz bilgileri
    create_demo_devices()
    
    # Entegrasyon testleri
    test_mikrotik_integration()
    test_vmware_integration()
    test_proxmox_integration()
    test_cisco_integration()
    
    print("🎉 Test tamamlandı!")
    print("\n📝 Sonraki adımlar:")
    print("   1. Gerçek cihaz bilgilerini girin")
    print("   2. Cihaz modellerini settings.py'ye ekleyin")
    print("   3. Dashboard'da cihaz durumlarını görüntüleyin")
    print("   4. Otomatik monitoring'i aktifleştirin")

if __name__ == "__main__":
    main()
