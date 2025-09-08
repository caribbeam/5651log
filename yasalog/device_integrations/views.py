"""
Gerçek Cihaz Entegrasyon Dashboard View'ları
5651log platformunda cihaz durumlarını görüntüler
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count
import json
import logging

from .models import Device, DeviceType, DeviceStatus, DeviceLog
from .proxmox import ProxmoxIntegration, ProxmoxDevice
from .mikrotik import MikroTikIntegration, MikroTikDevice
from .vmware import VMwareIntegration, VMwareDevice
from .proxmox import ProxmoxIntegration, ProxmoxDevice
from .cisco import CiscoIntegration, CiscoDevice

# Company model'ini import et
from log_kayit.models import Company, CompanyUser

logger = logging.getLogger(__name__)

@login_required
def device_dashboard(request, company_slug):
    """Cihaz dashboard'u - tüm cihazların durumunu gösterir"""
    try:
        # Şirket bilgilerini al
        company = get_object_or_404(Company, slug=company_slug)
        
        # Kullanıcının bu şirkete erişim yetkisi var mı kontrol et
        if not request.user.is_superuser:
            company_user = CompanyUser.objects.filter(
                user=request.user, 
                company=company
            ).first()
            if not company_user:
                return HttpResponseForbidden("Bu şirkete erişim yetkiniz yok.")
        
        # Gerçek cihazları veritabanından çek
        devices = Device.objects.filter(company=company).order_by('-last_seen')
        
        # Eğer cihaz yoksa demo cihazlar oluştur
        if not devices.exists():
            # Demo cihazları oluştur
            demo_devices_data = [
                {
                    'name': 'Ana Router',
                    'description': 'Ana internet router\'ı',
                    'ip_address': '192.168.1.1',
                    'integration_type': 'mikrotik',
                    'status': 'online'
                },
                {
                    'name': 'vCenter Server',
                    'description': 'VMware vCenter sunucusu',
                    'ip_address': '192.168.1.10',
                    'integration_type': 'vmware',
                    'status': 'online'
                },
                {
                    'name': 'Proxmox Cluster',
                    'description': 'Proxmox VE cluster\'ı',
                    'ip_address': '192.168.1.20',
                    'integration_type': 'proxmox',
                    'status': 'online'
                },
                {
                    'name': 'Firewall ASA',
                    'description': 'Cisco ASA firewall',
                    'ip_address': '192.168.1.30',
                    'integration_type': 'cisco',
                    'status': 'online'
                }
            ]
            
            # Demo cihazları oluştur
            for device_data in demo_devices_data:
                device_type, created = DeviceType.objects.get_or_create(
                    name=device_data['name'],
                    defaults={
                        'vendor': device_data['integration_type'].title(),
                        'model': 'Demo Model',
                        'category': 'router' if device_data['integration_type'] == 'mikrotik' else 'server',
                        'description': device_data['description']
                    }
                )
                
                Device.objects.get_or_create(
                    name=device_data['name'],
                    company=company,
                    defaults={
                        'description': device_data['description'],
                        'device_type': device_type,
                        'ip_address': device_data['ip_address'],
                        'integration_type': device_data['integration_type'],
                        'status': device_data['status'],
                        'is_monitored': True
                    }
                )
            
            # Cihazları tekrar çek
            devices = Device.objects.filter(company=company).order_by('-last_seen')
        
        # İstatistikler
        total_devices = devices.count()
        online_devices = devices.filter(status='online').count()
        offline_devices = devices.filter(status='offline').count()
        maintenance_devices = devices.filter(status='maintenance').count()
        error_devices = devices.filter(status='error').count()
        
        # Cihaz tiplerine göre gruplama
        device_types = devices.values('integration_type').annotate(count=Count('id'))
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'devices': devices,
            'total_devices': total_devices,
            'online_devices': online_devices,
            'offline_devices': offline_devices,
            'maintenance_devices': maintenance_devices,
            'error_devices': error_devices,
            'device_types': device_types,
        }
        
        return render(request, 'device_integrations/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Device dashboard hatası: {e}")
        # Error template için company context'i ekle
        try:
            company = get_object_or_404(Company, slug=company_slug)
            context = {'error': str(e), 'company': company, 'company_slug': company_slug}
        except:
            context = {'error': str(e), 'company': None, 'company_slug': company_slug}
        return render(request, 'device_integrations/error.html', context)

@login_required
def device_detail(request, device_id):
    """Cihaz detay sayfası - belirli bir cihazın detaylı bilgilerini gösterir"""
    try:
        # Company bilgisini session'dan al
        company_slug = request.session.get('company_slug', 'site')
        if Company:
            company = get_object_or_404(Company, slug=company_slug)
        else:
            company = {
                'name': company_slug.title() + ' Company',
                'slug': company_slug
            }
        
        # Demo cihaz bilgileri (gerçek uygulamada veritabanından çekilir)
        demo_device = {
            'id': device_id,
            'name': 'Ana Router',
            'type': 'MikroTik',
            'ip_address': '192.168.1.1',
            'status': 'online',
            'last_seen': timezone.now(),
            'description': 'Ana internet router\'ı',
            'model': 'RB4011iGS+',
            'firmware': 'RouterOS v6.49.7',
            'uptime': '15 days, 3 hours',
            'cpu_usage': 15,
            'memory_usage': 45,
            'temperature': 42
        }
        
        context = {
            'company': company,
            'device': demo_device,
        }
        
        return render(request, 'device_integrations/device_detail.html', context)
        
    except Exception as e:
        logger.error(f"Device detail hatası: {e}")
        return render(request, 'device_integrations/error.html', {'error': str(e)})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def test_device_connection(request, company_slug, device_id):
    """Cihaz bağlantısını test eder"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # JSON verisini al
        data = json.loads(request.body)
        device_type = data.get('device_type')
        ip_address = data.get('ip_address')
        username = data.get('username')
        password = data.get('password')
        port = data.get('port', 22)
        
        if not all([device_type, ip_address, username, password]):
            return JsonResponse({
                'success': False,
                'error': 'Eksik parametreler'
            })
        
        # Cihaz tipine göre test et
        if device_type == 'mikrotik':
            device = MikroTikDevice(
                name="Test Device",
                ip_address=ip_address,
                username=username,
                password=password,
                port=port
            )
            integration = MikroTikIntegration(device)
            success = integration.test_connection()
            
        elif device_type == 'vmware':
            device = VMwareDevice(
                name="Test Device",
                host=ip_address,
                username=username,
                password=password,
                port=port
            )
            integration = VMwareIntegration(device)
            success = integration.connect()
            if success:
                integration.disconnect()
                
        elif device_type == 'proxmox':
            device = ProxmoxDevice(
                name="Test Device",
                host=ip_address,
                username=username,
                password=password,
                port=port
            )
            integration = ProxmoxIntegration(device)
            success = integration.authenticate()
            
        elif device_type == 'cisco':
            device = CiscoDevice(
                name="Test Device",
                host=ip_address,
                username=username,
                password=password,
                port=port,
                device_type="cisco_asa"
            )
            integration = CiscoIntegration(device)
            success = integration.connect_ssh()
            if success:
                integration.disconnect_ssh()
        else:
            return JsonResponse({
                'success': False,
                'error': 'Desteklenmeyen cihaz tipi'
            })
        
        return JsonResponse({
            'success': success,
            'message': 'Bağlantı başarılı!' if success else 'Bağlantı başarısız!'
        })
        
    except Exception as e:
        logger.error(f"Device connection test hatası: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_device_status(request, company_slug, device_id):
    """Cihaz durum bilgilerini AJAX ile çeker"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo cihaz durumu (gerçek uygulamada cihazdan çekilir)
        device_status = {
            'id': device_id,
            'status': 'online',
            'last_seen': timezone.now().isoformat(),
            'cpu_usage': 15,
            'memory_usage': 45,
            'temperature': 42,
            'uptime': '15 days, 3 hours',
            'interfaces': [
                {'name': 'ether1', 'status': 'up', 'speed': '1Gbps'},
                {'name': 'ether2', 'status': 'up', 'speed': '1Gbps'},
                {'name': 'wlan1', 'status': 'down', 'speed': 'N/A'}
            ]
        }
        
        return JsonResponse({
            'success': True,
            'data': device_status
        })
        
    except Exception as e:
        logger.error(f"Device status hatası: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_device_logs(request, company_slug, device_id):
    """Cihaz log'larını AJAX ile çeker"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo log verileri (gerçek uygulamada cihazdan çekilir)
        logs = [
            {
                'timestamp': timezone.now().isoformat(),
                'level': 'INFO',
                'message': 'Interface ether1 is up',
                'source': 'system'
            },
            {
                'timestamp': timezone.now().isoformat(),
                'level': 'WARNING',
                'message': 'High CPU usage detected',
                'source': 'monitoring'
            },
            {
                'timestamp': timezone.now().isoformat(),
                'level': 'ERROR',
                'message': 'Failed to connect to external service',
                'source': 'network'
            }
        ]
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(logs, 20)
        logs_page = paginator.get_page(page)
        
        return JsonResponse({
            'success': True,
            'data': {
                'logs': list(logs_page),
                'total_pages': paginator.num_pages,
                'current_page': int(page)
            }
        })
        
    except Exception as e:
        logger.error(f"Device logs hatası: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def device_configuration(request, company_slug, device_id):
    """Cihaz konfigürasyon sayfası"""
    try:
        # Company bilgisini oluştur
        company = {
            'name': company_slug.title() + ' Company',
            'slug': company_slug
        }
        
        # Demo cihaz konfigürasyonu
        device_config = {
            'id': device_id,
            'name': f'Cihaz {device_id}',
            'type': 'MikroTik',
            'ip_address': '192.168.1.1',
            'port': 22,
            'protocol': 'ssh',
            'integration_type': 'mikrotik',
            'api_endpoint': 'https://192.168.1.1/api',
            'is_monitored': True,
            'backup_enabled': True,
            'auto_update': False
        }
        
        context = {
            'company': company,
            'device_config': device_config,
        }
        
        return render(request, 'device_integrations/device_configuration.html', context)
        
    except Exception as e:
        logger.error(f"Device configuration hatası: {e}")
        return render(request, 'device_integrations/error.html', {'error': str(e)})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_device_config(request, company_slug, device_id):
    """Cihaz konfigürasyonunu günceller"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # JSON verisini al
        data = json.loads(request.body)
        config_type = data.get('config_type')
        config_data = data.get('config_data')
        
        if not all([config_type, config_data]):
            return JsonResponse({
                'success': False,
                'error': 'Eksik parametreler'
            })
        
        # Demo güncelleme (gerçek uygulamada cihaza gönderilir)
        logger.info(f"Config update: {config_type} - {config_data}")
        
        return JsonResponse({
            'success': True,
            'message': 'Konfigürasyon güncellendi!'
        })
        
    except Exception as e:
        logger.error(f"Device config update hatası: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def device_backup(request, company_slug, device_id):
    """Cihaz yedekleme sayfası"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo yedek verileri
        backups = [
            {
                'id': 1,
                'filename': 'router_backup_2024_01_15.rsc',
                'size': '2.5 MB',
                'created_at': timezone.now(),
                'type': 'Configuration'
            },
            {
                'id': 2,
                'filename': 'router_backup_2024_01_10.rsc',
                'size': '2.4 MB',
                'created_at': timezone.now(),
                'type': 'Configuration'
            }
        ]
        
        context = {
            'company': company,
            'device_id': device_id,
            'backups': backups,
        }
        
        return render(request, 'device_integrations/backup.html', context)
        
    except Exception as e:
        logger.error(f"Device backup hatası: {e}")
        return render(request, 'device_integrations/error.html', {'error': str(e)})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_device_backup(request, company_slug, device_id):
    """Cihaz yedeği oluşturur"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo yedek oluşturma (gerçek uygulamada cihazdan alınır)
        logger.info(f"Creating backup for device {device_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Yedek oluşturuldu!',
            'backup_id': 999
        })
        
    except Exception as e:
        logger.error(f"Device backup creation hatası: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def device_monitoring(request, company_slug, device_id):
    """Cihaz monitoring sayfası - gerçek zamanlı metrikler"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo monitoring verileri
        monitoring_data = {
            'id': device_id,
            'name': 'Ana Router',
            'metrics': {
                'cpu': [15, 18, 22, 19, 16, 14, 17, 20, 18, 16],
                'memory': [45, 47, 49, 48, 46, 44, 47, 50, 48, 45],
                'network_in': [100, 120, 80, 150, 90, 110, 130, 70, 100, 140],
                'network_out': [50, 60, 40, 75, 45, 55, 65, 35, 50, 70]
            },
            'alerts': [
                {'level': 'warning', 'message': 'High CPU usage', 'timestamp': timezone.now()},
                {'level': 'info', 'message': 'Interface ether1 up', 'timestamp': timezone.now()}
            ]
        }
        
        context = {
            'company': company,
            'monitoring': monitoring_data,
        }
        
        return render(request, 'device_integrations/monitoring.html', context)
        
    except Exception as e:
        logger.error(f"Device monitoring hatası: {e}")
        return render(request, 'device_integrations/error.html', {'error': str(e)})

@login_required
def device_analytics(request, company_slug, device_id):
    """Cihaz analitik sayfası - detaylı raporlar ve grafikler"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo analitik verileri
        analytics_data = {
            'id': device_id,
            'name': 'Ana Router',
            'period': '30 days',
            'traffic_summary': {
                'total_in': '2.5 TB',
                'total_out': '1.8 TB',
                'peak_hour': '14:00-15:00',
                'busy_day': 'Wednesday'
            },
            'top_applications': [
                {'name': 'HTTP/HTTPS', 'traffic': '45%', 'users': 150},
                {'name': 'FTP', 'traffic': '25%', 'users': 30},
                {'name': 'SSH', 'traffic': '15%', 'users': 5},
                {'name': 'Other', 'traffic': '15%', 'users': 25}
            ],
            'user_activity': [
                {'hour': '00:00', 'users': 5, 'traffic': '50 MB'},
                {'hour': '06:00', 'users': 25, 'traffic': '200 MB'},
                {'hour': '12:00', 'users': 80, 'traffic': '800 MB'},
                {'hour': '18:00', 'users': 120, 'traffic': '1.2 GB'},
                {'hour': '23:00', 'users': 15, 'traffic': '150 MB'}
            ]
        }
        
        context = {
            'company': company,
            'analytics': analytics_data,
        }
        
        return render(request, 'device_integrations/analytics.html', context)
        
    except Exception as e:
        logger.error(f"Device analytics hatası: {e}")
        return render(request, 'device_integrations/error.html', {'error': str(e)})

# Basit view'lar - company_slug olmadan
def device_dashboard_simple(request, company_slug='site'):
    """Basit cihaz dashboard'u - company_slug parametresi ile"""
    # Demo cihaz listesi
    demo_devices = [
        {
            'id': 1,
            'name': 'Ana Router',
            'type': 'MikroTik',
            'ip_address': '192.168.1.1',
            'status': 'online',
            'last_seen': timezone.now(),
            'description': 'Ana internet router\'ı'
        },
        {
            'id': 2,
            'name': 'vCenter Server',
            'type': 'VMware',
            'ip_address': '192.168.1.10',
            'status': 'online',
            'last_seen': timezone.now(),
            'description': 'VMware vCenter sunucusu'
        },
        {
            'id': 3,
            'name': 'Proxmox Cluster',
            'type': 'Proxmox',
            'ip_address': '192.168.1.20',
            'status': 'online',
            'last_seen': timezone.now(),
            'description': 'Proxmox VE cluster\'ı'
        },
        {
            'id': 4,
            'name': 'Firewall ASA',
            'type': 'Cisco',
            'ip_address': '192.168.1.30',
            'status': 'online',
            'last_seen': timezone.now(),
            'description': 'Cisco ASA firewall'
        }
    ]
    
    # Company bilgisini oluştur
    company = {
        'name': company_slug.title() + ' Company',
        'slug': company_slug
    }
    
    context = {
        'company': company,
        'devices': demo_devices,
        'total_devices': len(demo_devices),
        'online_devices': len([d for d in demo_devices if d['status'] == 'online']),
        'offline_devices': len([d for d in demo_devices if d['status'] == 'offline']),
    }
    
    return render(request, 'device_integrations/dashboard_simple.html', context)

def mikrotik_devices(request):
    """MikroTik cihazları listesi"""
    context = {
        'devices': [
            {'name': 'Router-1', 'ip': '192.168.1.1', 'status': 'online'},
            {'name': 'Router-2', 'ip': '192.168.1.2', 'status': 'offline'},
        ]
    }
    return render(request, 'device_integrations/mikrotik_devices.html', context)

def vmware_devices(request):
    """VMware cihazları listesi"""
    context = {
        'devices': [
            {'name': 'vCenter-1', 'ip': '192.168.1.10', 'status': 'online'},
            {'name': 'ESXi-1', 'ip': '192.168.1.11', 'status': 'online'},
        ]
    }
    return render(request, 'device_integrations/vmware_devices.html', context)

def proxmox_devices(request):
    """Proxmox cihazları listesi"""
    context = {
        'devices': [
            {'name': 'Proxmox-1', 'ip': '192.168.1.20', 'status': 'online'},
            {'name': 'Proxmox-2', 'ip': '192.168.1.21', 'status': 'online'},
        ]
    }
    return render(request, 'device_integrations/proxmox_devices.html', context)

def cisco_devices(request):
    """Cisco cihazları listesi"""
    context = {
        'devices': [
            {'name': 'ASA-1', 'ip': '192.168.1.30', 'status': 'online'},
            {'name': 'Switch-1', 'ip': '192.168.1.31', 'status': 'offline'},
        ]
    }
    return render(request, 'device_integrations/cisco_devices.html', context)

def test_integrations(request):
    """Entegrasyon test sayfası"""
    return render(request, 'device_integrations/test_integrations.html', {})

@login_required
def device_status(request, company_slug, device_id):
    """Cihaz durum sayfası"""
    try:
        # Company bilgisini oluştur
        company = {
            'name': company_slug.title() + ' Company',
            'slug': company_slug
        }
        
        # Demo cihaz durumu
        device_status_data = {
            'id': device_id,
            'name': f'Cihaz {device_id}',
            'status': 'online',
            'cpu_usage': 25.5,
            'memory_usage': 40.2,
            'disk_usage': 30.8,
            'bandwidth_in': '2.5 GB',
            'bandwidth_out': '1.8 GB',
            'active_connections': 15,
            'last_update': timezone.now(),
            'warnings': ['Yüksek CPU kullanımı'],
            'errors': [],
            'critical_alerts': []
        }
        
        context = {
            'company': company,
            'device_status': device_status_data,
        }
        
        return render(request, 'device_integrations/device_status.html', context)
        
    except Exception as e:
        logger.error(f"Device status hatası: {e}")
        return render(request, 'device_integrations/error.html', {'error': str(e)})

@login_required
def get_device_metrics(request, company_slug, device_id):
    """Cihaz metriklerini AJAX ile çeker"""
    try:
        # Demo cihaz metrikleri
        device_metrics = {
            'cpu_usage': 25.5,
            'memory_usage': 40.2,
            'disk_usage': 30.8,
            'bandwidth_in': 2684354560,  # 2.5 GB in bytes
            'bandwidth_out': 1932735283,  # 1.8 GB in bytes
            'active_connections': 15,
            'temperature': 45.2,
            'power_consumption': 120.5,
            'last_update': timezone.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'data': device_metrics
        })
        
    except Exception as e:
        logger.error(f"Device metrics hatası: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# YENİ CRUD VIEW'LARI
@login_required
def device_add(request, company_slug):
    """Cihaz ekleme - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        company_user = CompanyUser.objects.filter(user=request.user, company=company).first()
        if not company_user:
            return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        device_type_name = request.POST.get('device_type')
        ip_address = request.POST.get('ip_address')
        port = request.POST.get('port', 22)
        protocol = request.POST.get('protocol', 'ssh')
        integration_type = request.POST.get('integration_type')
        api_endpoint = request.POST.get('api_endpoint', '')
        api_key = request.POST.get('api_key', '')
        is_monitored = request.POST.get('is_monitored') == 'on'
        
        # DeviceType oluştur veya al
        device_type, created = DeviceType.objects.get_or_create(
            name=device_type_name,
            defaults={
                'vendor': integration_type.title(),
                'model': 'Unknown',
                'category': 'router' if integration_type == 'mikrotik' else 'server',
                'description': f'{integration_type.title()} device'
            }
        )
        
        # Cihaz oluştur
        device = Device.objects.create(
            company=company,
            name=name,
            description=description,
            device_type=device_type,
            ip_address=ip_address,
            port=int(port),
            protocol=protocol,
            integration_type=integration_type,
            api_endpoint=api_endpoint,
            api_key=api_key,
            is_monitored=is_monitored,
            status='unknown'
        )
        
        messages.success(request, f'Cihaz "{name}" başarıyla eklendi.')
        return redirect('device_integrations:device_dashboard', company_slug=company.slug)
    
    context = {
        'company': company,
        'company_slug': company_slug,
        'integration_choices': Device.INTEGRATION_CHOICES,
    }
    
    return render(request, 'device_integrations/device_add.html', context)

@login_required
def device_edit(request, company_slug, device_id):
    """Cihaz düzenleme - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    device = get_object_or_404(Device, id=device_id, company=company)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        company_user = CompanyUser.objects.filter(user=request.user, company=company).first()
        if not company_user:
            return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini al ve güncelle
        device.name = request.POST.get('name')
        device.description = request.POST.get('description', '')
        device.ip_address = request.POST.get('ip_address')
        device.port = int(request.POST.get('port', 22))
        device.protocol = request.POST.get('protocol', 'ssh')
        device.integration_type = request.POST.get('integration_type')
        device.api_endpoint = request.POST.get('api_endpoint', '')
        device.api_key = request.POST.get('api_key', '')
        device.is_monitored = request.POST.get('is_monitored') == 'on'
        device.save()
        
        messages.success(request, f'Cihaz "{device.name}" başarıyla güncellendi.')
        return redirect('device_integrations:device_dashboard', company_slug=company.slug)
    
    context = {
        'company': company,
        'company_slug': company_slug,
        'device': device,
        'integration_choices': Device.INTEGRATION_CHOICES,
    }
    
    return render(request, 'device_integrations/device_edit.html', context)

@login_required
def device_delete(request, company_slug, device_id):
    """Cihaz silme - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    device = get_object_or_404(Device, id=device_id, company=company)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        company_user = CompanyUser.objects.filter(user=request.user, company=company).first()
        if not company_user:
            return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        device_name = device.name
        device.delete()
        messages.success(request, f'Cihaz "{device_name}" başarıyla silindi.')
        return redirect('device_integrations:device_dashboard', company_slug=company.slug)
    
    context = {
        'company': company,
        'company_slug': company_slug,
        'device': device,
    }
    
    return render(request, 'device_integrations/device_delete.html', context)

@login_required
def device_refresh_status(request, company_slug, device_id):
    """Cihaz durumunu yenile - AJAX"""
    company = get_object_or_404(Company, slug=company_slug)
    device = get_object_or_404(Device, id=device_id, company=company)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        company_user = CompanyUser.objects.filter(user=request.user, company=company).first()
        if not company_user:
            return JsonResponse({'success': False, 'error': 'Yetkisiz erişim.'})
    
    try:
        # Ping testi yap
        import subprocess
        import platform
        
        # Ping komutu (Windows/Linux uyumlu)
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        result = subprocess.run(['ping', param, '1', device.ip_address], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            device.status = 'online'
            device.last_seen = timezone.now()
            device.save()
            
            return JsonResponse({
                'success': True, 
                'status': 'online',
                'message': 'Cihaz çevrimiçi'
            })
        else:
            device.status = 'offline'
            device.save()
            
            return JsonResponse({
                'success': True, 
                'status': 'offline',
                'message': 'Cihaz çevrimdışı'
            })
            
    except Exception as e:
        device.status = 'error'
        device.save()
        
        return JsonResponse({
            'success': False, 
            'status': 'error',
            'error': str(e)
        })

@login_required
def device_view(request, company_slug, device_id):
    """Cihaz detay görüntüleme"""
    company = get_object_or_404(Company, slug=company_slug)
    device = get_object_or_404(Device, id=device_id, company=company)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        company_user = CompanyUser.objects.filter(user=request.user, company=company).first()
        if not company_user:
            return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Cihaz logları
    device_logs = DeviceLog.objects.filter(device=device).order_by('-timestamp')[:50]
    
    # Performans metrikleri (demo)
    performance_data = {
        'cpu_usage': 45.2,
        'memory_usage': 67.8,
        'disk_usage': 23.1,
        'network_in': 125.5,
        'network_out': 89.3,
        'uptime': '15 gün, 3 saat, 45 dakika'
    }
    
    context = {
        'company': company,
        'company_slug': company_slug,
        'device': device,
        'device_logs': device_logs,
        'performance_data': performance_data,
    }
    
    return render(request, 'device_integrations/device_view.html', context)


@login_required
def proxmox_dashboard(request, company_slug):
    """Proxmox dashboard'u - Proxmox altyapısını gösterir"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Yetki kontrolü
        if not request.user.is_superuser:
            try:
                company_user = CompanyUser.objects.get(user=request.user, company=company)
                if company_user.role not in ['admin', 'staff']:
                    return render(request, 'device_integrations/error.html', {
                        'error': 'Bu sayfaya erişim yetkiniz yok',
                        'company': company,
                        'company_slug': company_slug
                    })
            except CompanyUser.DoesNotExist:
                return render(request, 'device_integrations/error.html', {
                    'error': 'Bu şirket için yetkiniz yok',
                    'company': company,
                    'company_slug': company_slug
                })
        
        # Proxmox cihazlarını bul
        proxmox_devices = Device.objects.filter(
            company=company,
            integration_type='proxmox'
        ).order_by('name')
        
        # Eğer Proxmox cihazı yoksa demo cihaz oluştur
        if not proxmox_devices.exists():
            device_type, created = DeviceType.objects.get_or_create(
                name='Proxmox VE',
                defaults={
                    'category': 'virtualization',
                    'description': 'Proxmox Virtual Environment'
                }
            )
            
            demo_proxmox = Device.objects.create(
                company=company,
                name='Proxmox-Main',
                device_type=device_type,
                ip_address='192.168.1.20',  # Gerçek Proxmox IP'nizi buraya yazın
                port=8006,
                protocol='https',
                integration_type='proxmox',
                description='Ana Proxmox sunucusu',
                api_endpoint='root',  # Proxmox kullanıcı adı
                api_key='password',   # Proxmox şifresi (gerçek uygulamada şifreli saklanmalı)
                is_monitored=True,
                status='offline'  # Bağlantı testi yapılana kadar offline
            )
            
            proxmox_devices = Device.objects.filter(
                company=company,
                integration_type='proxmox'
            ).order_by('name')
        
        proxmox_data = []
        
        for device in proxmox_devices:
            try:
                # Proxmox bağlantısı kur
                proxmox_device = ProxmoxDevice(
                    name=device.name,
                    host=device.ip_address,
                    username=device.api_key or 'root',
                    password=device.api_endpoint or 'password',  # Bu güvenlik açığı, gerçek uygulamada şifreli saklanmalı
                    port=8006  # Proxmox her zaman port 8006 kullanır
                )
                
                proxmox_integration = ProxmoxIntegration(proxmox_device)
                
                # Demo modunda çalış (gerçek bağlantı yoksa)
                if device.ip_address == '192.168.1.20':
                    # Demo Proxmox verileri
                    from .proxmox import ProxmoxNode, ProxmoxVM, ProxmoxContainer
                    
                    # Demo node'lar (esy1-esy8)
                    demo_nodes = []
                    for i in range(1, 9):
                        node = ProxmoxNode(
                            node_id=f'esy{i}',
                            name=f'esy{i}',
                            status='online',
                            cpu_count=8,
                            memory_total=16777216000,  # 16GB
                            memory_used=8388608000,    # 8GB
                            disk_total=500000000000,   # 500GB
                            disk_used=250000000000,    # 250GB
                            uptime=86400 * 30  # 30 gün
                        )
                        demo_nodes.append(node)
                    
                    # Demo VM'ler - görüntüdeki gibi
                    demo_vms = [
                        ProxmoxVM(321, 'SitePttINK', 'running', 15.2, 1073741824, 20000000000, 86400 * 10, False, 'esy3'),
                        ProxmoxVM(307, 'SiteTurksatPBX', 'running', 25.5, 2147483648, 50000000000, 86400 * 15, False, 'esy3'),
                        ProxmoxVM(308, 'SitePttSrv19', 'stopped', 0.0, 0, 0, 0, False, 'esy3'),
                        ProxmoxVM(302, 'SiteDeltaPBX', 'running', 45.2, 4294967296, 100000000000, 86400 * 20, False, 'esy4'),
                        ProxmoxVM(303, 'SiteMerkezPBX', 'running', 35.8, 3221225472, 75000000000, 86400 * 25, False, 'esy4'),
                        ProxmoxVM(304, 'SitePttPBX', 'stopped', 0.0, 0, 0, 0, False, 'esy4'),
                    ]
                    
                    # Demo Container'lar - görüntüdeki gibi
                    demo_containers = [
                        ProxmoxContainer(321, 'SitePttINK', 'running', 15.2, 1073741824, 20000000000, 86400 * 10, False, 'esy3', 'ubuntu'),
                    ]
                    
                    # Demo verileri organize et - tüm node'ları göster
                    node_data = []
                    total_vms = len(demo_vms)
                    total_containers = len(demo_containers)
                    running_vms = len([vm for vm in demo_vms if vm.status == 'running'])
                    running_containers = len([container for container in demo_containers if container.status == 'running'])
                    
                    # Tüm node'ları ekle (esy1-esy8)
                    for i, node in enumerate(demo_nodes):
                        node_id = f'esy{i+1}'
                        node_vms = [vm for vm in demo_vms if vm.node == node_id]
                        node_containers = [container for container in demo_containers if container.node == node_id]
                        
                        node_data.append({
                            'node': node,
                            'vms': node_vms,
                            'containers': node_containers,
                            'vm_count': len(node_vms),
                            'container_count': len(node_containers),
                            'running_vms': len([vm for vm in node_vms if vm.status == 'running']),
                            'running_containers': len([container for container in node_containers if container.status == 'running']),
                            'status': 'online'
                        })
                    
                    proxmox_data.append({
                        'device': device,
                        'nodes': node_data,
                        'total_vms': total_vms,
                        'total_containers': total_containers,
                        'running_vms': running_vms,
                        'running_containers': running_containers,
                        'total_nodes': len(demo_nodes),
                        'online_nodes': len(demo_nodes),
                        'status': 'connected'
                    })
                    
                elif proxmox_integration.authenticate():
                    # Gerçek Proxmox bağlantısı
                    nodes = proxmox_integration.get_nodes()
                    
                    node_data = []
                    total_vms = 0
                    total_containers = 0
                    running_vms = 0
                    running_containers = 0
                    
                    for node in nodes:
                        # VM'leri al
                        vms = proxmox_integration.get_vms(node.node_id)
                        containers = proxmox_integration.get_containers(node.node_id)
                        
                        # İstatistikleri hesapla
                        node_vms = len(vms)
                        node_containers = len(containers)
                        node_running_vms = len([vm for vm in vms if vm.status == 'running'])
                        node_running_containers = len([container for container in containers if container.status == 'running'])
                        
                        total_vms += node_vms
                        total_containers += node_containers
                        running_vms += node_running_vms
                        running_containers += node_running_containers
                        
                        node_data.append({
                            'node': node,
                            'vms': vms,
                            'containers': containers,
                            'vm_count': node_vms,
                            'container_count': node_containers,
                            'running_vms': node_running_vms,
                            'running_containers': node_running_containers,
                            'status': 'online' if node.status == 'online' else 'offline'
                        })
                    
                    proxmox_data.append({
                        'device': device,
                        'nodes': node_data,
                        'total_vms': total_vms,
                        'total_containers': total_containers,
                        'running_vms': running_vms,
                        'running_containers': running_containers,
                        'total_nodes': len(nodes),
                        'online_nodes': len([node for node in nodes if node.status == 'online']),
                        'status': 'connected'
                    })
                else:
                    proxmox_data.append({
                        'device': device,
                        'nodes': [],
                        'total_vms': 0,
                        'total_containers': 0,
                        'running_vms': 0,
                        'running_containers': 0,
                        'total_nodes': 0,
                        'online_nodes': 0,
                        'status': 'disconnected'
                    })
                    
            except Exception as e:
                logger.error(f"Proxmox bağlantı hatası {device.name}: {e}")
                proxmox_data.append({
                    'device': device,
                    'nodes': [],
                    'total_vms': 0,
                    'total_containers': 0,
                    'running_vms': 0,
                    'running_containers': 0,
                    'total_nodes': 0,
                    'online_nodes': 0,
                    'status': 'error'
                })
        
        # Genel istatistikler
        total_proxmox_devices = len(proxmox_data)
        connected_devices = len([d for d in proxmox_data if d['status'] == 'connected'])
        total_vms = sum([d['total_vms'] for d in proxmox_data])
        total_containers = sum([d['total_containers'] for d in proxmox_data])
        running_vms = sum([d['running_vms'] for d in proxmox_data])
        running_containers = sum([d['running_containers'] for d in proxmox_data])
        total_nodes = sum([d['total_nodes'] for d in proxmox_data])
        online_nodes = sum([d['online_nodes'] for d in proxmox_data])
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'proxmox_data': proxmox_data,
            'total_proxmox_devices': total_proxmox_devices,
            'connected_devices': connected_devices,
            'total_vms': total_vms,
            'total_containers': total_containers,
            'running_vms': running_vms,
            'running_containers': running_containers,
            'total_nodes': total_nodes,
            'online_nodes': online_nodes,
            'vm_usage_percent': (running_vms / total_vms * 100) if total_vms > 0 else 0,
            'container_usage_percent': (running_containers / total_containers * 100) if total_containers > 0 else 0,
            'node_usage_percent': (online_nodes / total_nodes * 100) if total_nodes > 0 else 0,
        }
        
        return render(request, 'device_integrations/proxmox_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Proxmox dashboard hatası: {e}")
        try:
            company = get_object_or_404(Company, slug=company_slug)
            context = {'error': str(e), 'company': company, 'company_slug': company_slug}
        except:
            context = {'error': str(e), 'company': None, 'company_slug': company_slug}
        return render(request, 'device_integrations/error.html', context)


@login_required
def mikrotik_dashboard(request, company_slug):
    """MikroTik dashboard'u - Firewall ve router'ları gösterir"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Yetki kontrolü
        if not request.user.is_superuser:
            try:
                company_user = CompanyUser.objects.get(user=request.user, company=company)
                if company_user.role not in ['admin', 'staff']:
                    return render(request, 'device_integrations/error.html', {
                        'error': 'Bu sayfaya erişim yetkiniz yok',
                        'company': company,
                        'company_slug': company_slug
                    })
            except CompanyUser.DoesNotExist:
                return render(request, 'device_integrations/error.html', {
                    'error': 'Bu şirket için yetkiniz yok',
                    'company': company,
                    'company_slug': company_slug
                })
        
        # MikroTik cihazlarını bul
        mikrotik_devices = Device.objects.filter(
            company=company,
            integration_type='mikrotik'
        ).order_by('name')
        
        # Eğer MikroTik cihazı yoksa demo cihaz oluştur
        if not mikrotik_devices.exists():
            device_type, created = DeviceType.objects.get_or_create(
                name='MikroTik RouterOS',
                defaults={
                    'category': 'firewall',
                    'description': 'MikroTik RouterOS Firewall'
                }
            )
            
            demo_mikrotik = Device.objects.create(
                company=company,
                name='MikroTik-Firewall-Main',
                device_type=device_type,
                ip_address='192.168.1.1',  # Gerçek MikroTik IP'nizi buraya yazın
                port=443,
                protocol='https',
                integration_type='mikrotik',
                description='Ana firewall - sunucu odası',
                api_endpoint='admin',  # MikroTik kullanıcı adı
                api_key='password',    # MikroTik şifresi (gerçek uygulamada şifreli saklanmalı)
                is_monitored=True,
                status='offline'  # Bağlantı testi yapılana kadar offline
            )
            
            mikrotik_devices = Device.objects.filter(
                company=company,
                integration_type='mikrotik'
            ).order_by('name')
        
        mikrotik_data = []
        
        for device in mikrotik_devices:
            try:
                # Demo modunda çalış (gerçek bağlantı yoksa)
                if device.ip_address == '192.168.1.1':
                    # Demo MikroTik verileri
                    from .mikrotik import MikroTikDevice, FirewallRule, InterfaceStatus
                    
                    # Demo firewall kuralları
                    demo_rules = [
                        FirewallRule('1', 'input', 'accept', 'tcp', '0.0.0.0/0', '192.168.1.0/24', '', '22', 'SSH Access', False, '2024-01-01'),
                        FirewallRule('2', 'input', 'accept', 'tcp', '0.0.0.0/0', '192.168.1.0/24', '', '80', 'HTTP Access', False, '2024-01-01'),
                        FirewallRule('3', 'input', 'accept', 'tcp', '0.0.0.0/0', '192.168.1.0/24', '', '443', 'HTTPS Access', False, '2024-01-01'),
                        FirewallRule('4', 'input', 'drop', 'tcp', '0.0.0.0/0', '192.168.1.0/24', '', '23', 'Block Telnet', False, '2024-01-01'),
                        FirewallRule('5', 'forward', 'accept', 'tcp', '192.168.1.0/24', '0.0.0.0/0', '', '80', 'Internet HTTP', False, '2024-01-01'),
                        FirewallRule('6', 'forward', 'accept', 'tcp', '192.168.1.0/24', '0.0.0.0/0', '', '443', 'Internet HTTPS', False, '2024-01-01'),
                    ]
                    
                    # Demo interface'ler
                    demo_interfaces = [
                        InterfaceStatus('ether1', 'ether', 'up', '1Gbps', 1024000000, 2048000000, 1500000, 3000000, 'WAN'),
                        InterfaceStatus('ether2', 'ether', 'up', '1Gbps', 512000000, 1024000000, 750000, 1500000, 'LAN'),
                        InterfaceStatus('ether3', 'ether', 'up', '1Gbps', 256000000, 512000000, 375000, 750000, 'Server Room'),
                        InterfaceStatus('ether4', 'ether', 'down', '1Gbps', 0, 0, 0, 0, 'Unused'),
                    ]
                    
                    # Demo VPN bağlantıları
                    demo_vpns = [
                        {'name': 'Site-to-Site VPN', 'status': 'connected', 'remote_ip': '10.0.1.1', 'local_ip': '192.168.1.1'},
                        {'name': 'Remote Access VPN', 'status': 'connected', 'remote_ip': '0.0.0.0', 'local_ip': '192.168.1.1'},
                    ]
                    
                    mikrotik_data.append({
                        'device': device,
                        'rules': demo_rules,
                        'interfaces': demo_interfaces,
                        'vpns': demo_vpns,
                        'total_rules': len(demo_rules),
                        'active_rules': len([r for r in demo_rules if not r.disabled]),
                        'total_interfaces': len(demo_interfaces),
                        'up_interfaces': len([i for i in demo_interfaces if i.status == 'up']),
                        'total_vpns': len(demo_vpns),
                        'connected_vpns': len([v for v in demo_vpns if v['status'] == 'connected']),
                        'status': 'connected'
                    })
                    
                else:
                    # Gerçek MikroTik bağlantısı (gelecekte implement edilecek)
                    mikrotik_data.append({
                        'device': device,
                        'rules': [],
                        'interfaces': [],
                        'vpns': [],
                        'total_rules': 0,
                        'active_rules': 0,
                        'total_interfaces': 0,
                        'up_interfaces': 0,
                        'total_vpns': 0,
                        'connected_vpns': 0,
                        'status': 'disconnected'
                    })
                    
            except Exception as e:
                logger.error(f"MikroTik bağlantı hatası {device.name}: {e}")
                mikrotik_data.append({
                    'device': device,
                    'rules': [],
                    'interfaces': [],
                    'vpns': [],
                    'total_rules': 0,
                    'active_rules': 0,
                    'total_interfaces': 0,
                    'up_interfaces': 0,
                    'total_vpns': 0,
                    'connected_vpns': 0,
                    'status': 'error'
                })
        
        # Genel istatistikler
        total_mikrotik_devices = len(mikrotik_data)
        connected_devices = len([d for d in mikrotik_data if d['status'] == 'connected'])
        total_rules = sum([d['total_rules'] for d in mikrotik_data])
        active_rules = sum([d['active_rules'] for d in mikrotik_data])
        total_interfaces = sum([d['total_interfaces'] for d in mikrotik_data])
        up_interfaces = sum([d['up_interfaces'] for d in mikrotik_data])
        total_vpns = sum([d['total_vpns'] for d in mikrotik_data])
        connected_vpns = sum([d['connected_vpns'] for d in mikrotik_data])
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'mikrotik_data': mikrotik_data,
            'total_mikrotik_devices': total_mikrotik_devices,
            'connected_devices': connected_devices,
            'total_rules': total_rules,
            'active_rules': active_rules,
            'total_interfaces': total_interfaces,
            'up_interfaces': up_interfaces,
            'total_vpns': total_vpns,
            'connected_vpns': connected_vpns,
            'rule_usage_percent': (active_rules / total_rules * 100) if total_rules > 0 else 0,
            'interface_usage_percent': (up_interfaces / total_interfaces * 100) if total_interfaces > 0 else 0,
            'vpn_usage_percent': (connected_vpns / total_vpns * 100) if total_vpns > 0 else 0,
        }
        
        return render(request, 'device_integrations/mikrotik_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"MikroTik dashboard hatası: {e}")
        try:
            company = get_object_or_404(Company, slug=company_slug)
            context = {'error': str(e), 'company': company, 'company_slug': company_slug}
        except:
            context = {'error': str(e), 'company': None, 'company_slug': company_slug}
        return render(request, 'device_integrations/error.html', context)
