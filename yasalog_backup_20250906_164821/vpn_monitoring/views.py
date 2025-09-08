"""
VPN Monitoring Views
5651log platformunda VPN bağlantılarını ve kullanıcı aktivitelerini görüntüler
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.core.paginator import Paginator
import json
import logging

from .models import VPNProject, VPNConnection, VPNUserActivity, VPNServerStatus

logger = logging.getLogger(__name__)

@login_required
def vpn_dashboard(request, company_slug):
    """VPN Dashboard - Genel VPN durumu ve istatistikler"""
    try:
        # Company bilgisini oluştur
        company = {
            'name': company_slug.title() + ' Company',
            'slug': company_slug
        }
        
        # Demo VPN projeleri
        demo_projects = [
            {
                'id': 1,
                'name': 'Ana Ofis VPN',
                'vpn_protocol': 'OpenVPN',
                'vpn_server_ip': '192.168.1.100',
                'status': 'online',
                'active_connections': 15,
                'cpu_usage': 25,
                'memory_usage': 40,
                'bandwidth_in': '2.5 GB',
                'bandwidth_out': '1.8 GB'
            },
            {
                'id': 2,
                'name': 'Şube VPN',
                'vpn_protocol': 'WireGuard',
                'vpn_server_ip': '192.168.1.101',
                'status': 'online',
                'active_connections': 8,
                'cpu_usage': 15,
                'memory_usage': 30,
                'bandwidth_in': '1.2 GB',
                'bandwidth_out': '800 MB'
            },
            {
                'id': 3,
                'name': 'Mobil VPN',
                'vpn_protocol': 'IPSec',
                'vpn_server_ip': '192.168.1.102',
                'status': 'maintenance',
                'active_connections': 0,
                'cpu_usage': 5,
                'memory_usage': 20,
                'bandwidth_in': '0 MB',
                'bandwidth_out': '0 MB'
            }
        ]
        
        # Demo aktif bağlantılar
        demo_connections = [
            {
                'id': 1,
                'user': 'ahmet.yilmaz',
                'project': 'Ana Ofis VPN',
                'vpn_ip': '10.0.1.10',
                'real_ip': '185.45.123.45',
                'status': 'connected',
                'connected_at': timezone.now(),
                'duration': '2 saat 15 dakika',
                'bandwidth_in': '150 MB',
                'bandwidth_out': '80 MB'
            },
            {
                'id': 2,
                'user': 'fatma.demir',
                'project': 'Ana Ofis VPN',
                'vpn_ip': '10.0.1.11',
                'real_ip': '78.123.45.67',
                'status': 'connected',
                'connected_at': timezone.now(),
                'duration': '1 saat 30 dakika',
                'bandwidth_in': '200 MB',
                'bandwidth_out': '120 MB'
            },
            {
                'id': 3,
                'user': 'mehmet.kaya',
                'project': 'Şube VPN',
                'vpn_ip': '10.0.2.5',
                'real_ip': '92.45.67.89',
                'status': 'connected',
                'connected_at': timezone.now(),
                'duration': '45 dakika',
                'bandwidth_in': '75 MB',
                'bandwidth_out': '40 MB'
            }
        ]
        
        # İstatistikler
        total_projects = len(demo_projects)
        total_connections = len(demo_connections)
        online_projects = len([p for p in demo_projects if p['status'] == 'online'])
        maintenance_projects = len([p for p in demo_projects if p['status'] == 'maintenance'])
        
        context = {
            'company': company,
            'projects': demo_projects,
            'connections': demo_connections,
            'total_projects': total_projects,
            'total_connections': total_connections,
            'online_projects': online_projects,
            'maintenance_projects': maintenance_projects,
        }
        
        return render(request, 'vpn_monitoring/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"VPN dashboard hatası: {e}")
        return render(request, 'vpn_monitoring/error.html', {'error': str(e)})

@login_required
def vpn_connections(request, company_slug):
    """VPN Bağlantıları listesi"""
    try:
        company = {
            'name': company_slug.title() + ' Company',
            'slug': company_slug
        }
        
        # Demo bağlantı listesi
        demo_connections = [
            {
                'id': 1,
                'user': 'ahmet.yilmaz',
                'project': 'Ana Ofis VPN',
                'vpn_ip': '10.0.1.10',
                'real_ip': '185.45.123.45',
                'status': 'connected',
                'connected_at': timezone.now(),
                'duration': '2 saat 15 dakika',
                'bandwidth_in': '150 MB',
                'bandwidth_out': '80 MB',
                'location': 'İstanbul, TR'
            },
            {
                'id': 2,
                'user': 'fatma.demir',
                'project': 'Ana Ofis VPN',
                'vpn_ip': '10.0.1.11',
                'real_ip': '78.123.45.67',
                'status': 'connected',
                'connected_at': timezone.now(),
                'duration': '1 saat 30 dakika',
                'bandwidth_in': '200 MB',
                'bandwidth_out': '120 MB',
                'location': 'Ankara, TR'
            },
            {
                'id': 3,
                'user': 'mehmet.kaya',
                'project': 'Şube VPN',
                'vpn_ip': '10.0.2.5',
                'real_ip': '92.45.67.89',
                'status': 'connected',
                'connected_at': timezone.now(),
                'duration': '45 dakika',
                'bandwidth_in': '75 MB',
                'bandwidth_out': '40 MB',
                'location': 'İzmir, TR'
            },
            {
                'id': 4,
                'user': 'ayse.ozturk',
                'project': 'Ana Ofis VPN',
                'vpn_ip': '10.0.1.12',
                'real_ip': '45.67.89.12',
                'status': 'disconnected',
                'connected_at': timezone.now(),
                'duration': '0 dakika',
                'bandwidth_in': '0 MB',
                'bandwidth_out': '0 MB',
                'location': 'Bursa, TR'
            }
        ]
        
        # Filtreleme
        status_filter = request.GET.get('status', '')
        project_filter = request.GET.get('project', '')
        
        if status_filter:
            demo_connections = [c for c in demo_connections if c['status'] == status_filter]
        
        if project_filter:
            demo_connections = [c for c in demo_connections if project_filter in c['project']]
        
        # Pagination
        paginator = Paginator(demo_connections, 20)
        page = request.GET.get('page', 1)
        connections_page = paginator.get_page(page)
        
        context = {
            'company': company,
            'connections': connections_page,
            'total_connections': len(demo_connections),
            'status_filter': status_filter,
            'project_filter': project_filter,
        }
        
        return render(request, 'vpn_monitoring/connections.html', context)
        
    except Exception as e:
        logger.error(f"VPN connections hatası: {e}")
        return render(request, 'vpn_monitoring/error.html', {'error': str(e)})

@login_required
def vpn_user_activity(request, company_slug):
    """VPN Kullanıcı aktivite log'ları"""
    try:
        company = {
            'name': company_slug.title() + ' Company',
            'slug': company_slug
        }
        
        # Demo aktivite log'ları
        demo_activities = [
            {
                'id': 1,
                'user': 'ahmet.yilmaz',
                'project': 'Ana Ofis VPN',
                'activity_type': 'login',
                'description': 'VPN bağlantısı başlatıldı',
                'ip_address': '185.45.123.45',
                'timestamp': timezone.now(),
                'status': 'success'
            },
            {
                'id': 2,
                'user': 'fatma.demir',
                'project': 'Ana Ofis VPN',
                'activity_type': 'reconnect',
                'description': 'VPN bağlantısı yeniden kuruldu',
                'ip_address': '78.123.45.67',
                'timestamp': timezone.now(),
                'status': 'success'
            },
            {
                'id': 3,
                'user': 'mehmet.kaya',
                'project': 'Şube VPN',
                'activity_type': 'logout',
                'description': 'VPN bağlantısı sonlandırıldı',
                'ip_address': '92.45.67.89',
                'timestamp': timezone.now(),
                'status': 'success'
            },
            {
                'id': 4,
                'user': 'ayse.ozturk',
                'project': 'Ana Ofis VPN',
                'activity_type': 'error',
                'description': 'VPN bağlantı hatası: Timeout',
                'ip_address': '45.67.89.12',
                'timestamp': timezone.now(),
                'status': 'error'
            }
        ]
        
        # Filtreleme
        user_filter = request.GET.get('user', '')
        activity_filter = request.GET.get('activity', '')
        
        if user_filter:
            demo_activities = [a for a in demo_activities if user_filter.lower() in a['user'].lower()]
        
        if activity_filter:
            demo_activities = [a for a in demo_activities if a['activity_type'] == activity_filter]
        
        # Pagination
        paginator = Paginator(demo_activities, 20)
        page = request.GET.get('page', 1)
        activities_page = paginator.get_page(page)
        
        context = {
            'company': company,
            'activities': activities_page,
            'total_activities': len(demo_activities),
            'user_filter': user_filter,
            'activity_filter': activity_filter,
        }
        
        return render(request, 'vpn_monitoring/user_activity.html', context)
        
    except Exception as e:
        logger.error(f"VPN user activity hatası: {e}")
        return render(request, 'vpn_monitoring/error.html', {'error': str(e)})

@login_required
def vpn_project_detail(request, company_slug, project_id):
    """VPN Proje detay sayfası"""
    try:
        company = {
            'name': company_slug.title() + ' Company',
            'slug': company_slug
        }
        
        # Demo proje detayı
        demo_project = {
            'id': project_id,
            'name': 'Ana Ofis VPN',
            'description': 'Ana ofis çalışanları için OpenVPN sunucusu',
            'vpn_protocol': 'OpenVPN',
            'vpn_server_ip': '192.168.1.100',
            'vpn_server_port': 1194,
            'status': 'online',
            'created_at': timezone.now(),
            'active_connections': 15,
            'total_users': 45,
            'cpu_usage': 25,
            'memory_usage': 40,
            'disk_usage': 30,
            'bandwidth_in': '2.5 GB',
            'bandwidth_out': '1.8 GB'
        }
        
        # Proje bağlantıları
        demo_connections = [
            {
                'user': 'ahmet.yilmaz',
                'vpn_ip': '10.0.1.10',
                'real_ip': '185.45.123.45',
                'status': 'connected',
                'connected_at': timezone.now(),
                'duration': '2 saat 15 dakika',
                'bandwidth_in': '150 MB',
                'bandwidth_out': '80 MB'
            },
            {
                'user': 'fatma.demir',
                'vpn_ip': '10.0.1.11',
                'real_ip': '78.123.45.67',
                'status': 'connected',
                'connected_at': timezone.now(),
                'duration': '1 saat 30 dakika',
                'bandwidth_in': '200 MB',
                'bandwidth_out': '120 MB'
            }
        ]
        
        context = {
            'company': company,
            'project': demo_project,
            'connections': demo_connections,
        }
        
        return render(request, 'vpn_monitoring/project_detail.html', context)
        
    except Exception as e:
        logger.error(f"VPN project detail hatası: {e}")
        return render(request, 'vpn_monitoring/error.html', {'error': str(e)})

# AJAX endpoint'leri
@login_required
def get_vpn_status(request, company_slug):
    """VPN durum bilgilerini AJAX ile çeker"""
    try:
        # Demo VPN durum bilgileri
        vpn_status = {
            'total_projects': 3,
            'online_projects': 2,
            'maintenance_projects': 1,
            'total_connections': 15,
            'active_connections': 12,
            'total_bandwidth': '3.7 GB',
            'server_health': 'good'
        }
        
        return JsonResponse({
            'success': True,
            'data': vpn_status
        })
        
    except Exception as e:
        logger.error(f"VPN status hatası: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_active_connections(request, company_slug):
    """Aktif VPN bağlantılarını AJAX ile çeker"""
    try:
        # Demo aktif bağlantılar
        active_connections = [
            {
                'user': 'ahmet.yilmaz',
                'project': 'Ana Ofis VPN',
                'vpn_ip': '10.0.1.10',
                'real_ip': '185.45.123.45',
                'duration': '2 saat 15 dakika',
                'bandwidth_in': '150 MB',
                'bandwidth_out': '80 MB'
            },
            {
                'user': 'fatma.demir',
                'project': 'Ana Ofis VPN',
                'vpn_ip': '10.0.1.11',
                'real_ip': '78.123.45.67',
                'duration': '1 saat 30 dakika',
                'bandwidth_in': '200 MB',
                'bandwidth_out': '120 MB'
            }
        ]
        
        return JsonResponse({
            'success': True,
            'data': active_connections
        })
        
    except Exception as e:
        logger.error(f"Active connections hatası: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
