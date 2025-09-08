"""
Alert System Views
5651log platformunda gerçek zamanlı uyarılar için view'lar
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json
import random

from log_kayit.models import Company


@login_required
def alert_dashboard(request, company_slug):
    """Ana uyarı dashboard'u"""
    try:
        # Company bilgisini veritabanından al
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo uyarı verileri
        alert_stats = {
            'total_alerts': 45,
            'new_alerts': 8,
            'acknowledged_alerts': 15,
            'resolved_alerts': 22,
            'critical_alerts': 3,
            'high_alerts': 12,
            'medium_alerts': 20,
            'low_alerts': 10
        }
        
        # Son uyarılar
        recent_alerts = [
            {
                'id': 1,
                'title': 'Yüksek CPU Kullanımı Tespit Edildi',
                'severity': 'high',
                'status': 'new',
                'type': 'performance',
                'timestamp': timezone.now() - timedelta(minutes=15),
                'description': 'Ana sunucuda CPU kullanımı %95\'in üzerine çıktı.',
                'device': 'Server-01',
                'acknowledged_by': None
            },
            {
                'id': 2,
                'title': 'Şüpheli Network Bağlantısı',
                'severity': 'critical',
                'status': 'new',
                'type': 'security',
                'timestamp': timezone.now() - timedelta(minutes=8),
                'description': 'Bilinmeyen IP adresinden şüpheli bağlantı denemesi.',
                'device': 'Firewall-01',
                'acknowledged_by': None
            },
            {
                'id': 3,
                'title': 'Disk Alanı Kritik Seviyede',
                'severity': 'high',
                'status': 'acknowledged',
                'type': 'performance',
                'timestamp': timezone.now() - timedelta(hours=2),
                'description': 'Storage sunucusunda disk alanı %98 doldu.',
                'device': 'Storage-01',
                'acknowledged_by': 'admin@company.com'
            },
            {
                'id': 4,
                'title': 'VPN Bağlantısı Kesildi',
                'severity': 'medium',
                'status': 'resolved',
                'type': 'network',
                'timestamp': timezone.now() - timedelta(hours=1),
                'description': 'VPN sunucusu bağlantısı 5 dakika kesildi.',
                'device': 'VPN-01',
                'acknowledged_by': 'admin@company.com'
            }
        ]
        
        # Uyarı kuralları
        alert_rules = [
            {
                'id': 1,
                'name': 'CPU Kullanım Uyarısı',
                'type': 'performance',
                'severity': 'high',
                'trigger_type': 'threshold',
                'threshold': 90,
                'is_active': True
            },
            {
                'id': 2,
                'name': 'Disk Alan Uyarısı',
                'type': 'performance',
                'severity': 'high',
                'trigger_type': 'threshold',
                'threshold': 95,
                'is_active': True
            },
            {
                'id': 3,
                'name': 'Şüpheli Bağlantı Uyarısı',
                'type': 'security',
                'severity': 'critical',
                'trigger_type': 'anomaly',
                'threshold': None,
                'is_active': True
            }
        ]
        
        context = {
            'company': company,
            'alert_stats': alert_stats,
            'recent_alerts': recent_alerts,
            'alert_rules': alert_rules,
        }
        
        return render(request, 'alert_system/dashboard.html', context)
        
    except Exception as e:
        return render(request, 'alert_system/error.html', {'error': str(e)})


@login_required
def alert_rules(request, company_slug):
    """Uyarı kuralları yönetimi"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo uyarı kuralları
        rules = [
            {
                'id': 1,
                'name': 'CPU Kullanım Uyarısı',
                'description': 'CPU kullanımı belirlenen eşik değerini aştığında uyarı verir.',
                'type': 'performance',
                'severity': 'high',
                'trigger_type': 'threshold',
                'threshold_value': 90.0,
                'is_active': True,
                'auto_resolve': True,
                'escalation_enabled': True,
                'created_at': timezone.now() - timedelta(days=5)
            },
            {
                'id': 2,
                'name': 'Disk Alan Uyarısı',
                'description': 'Disk alanı kritik seviyeye ulaştığında uyarı verir.',
                'type': 'performance',
                'severity': 'high',
                'trigger_type': 'threshold',
                'threshold_value': 95.0,
                'is_active': True,
                'auto_resolve': False,
                'escalation_enabled': True,
                'created_at': timezone.now() - timedelta(days=3)
            },
            {
                'id': 3,
                'name': 'Şüpheli Bağlantı Uyarısı',
                'description': 'Bilinmeyen IP adreslerinden gelen bağlantıları tespit eder.',
                'type': 'security',
                'severity': 'critical',
                'trigger_type': 'anomaly',
                'threshold_value': None,
                'is_active': True,
                'auto_resolve': False,
                'escalation_enabled': True,
                'created_at': timezone.now() - timedelta(days=7)
            },
            {
                'id': 4,
                'name': 'Memory Kullanım Uyarısı',
                'description': 'Memory kullanımı belirlenen eşik değerini aştığında uyarı verir.',
                'type': 'performance',
                'severity': 'medium',
                'trigger_type': 'threshold',
                'threshold_value': 85.0,
                'is_active': True,
                'auto_resolve': True,
                'escalation_enabled': False,
                'created_at': timezone.now() - timedelta(days=2)
            }
        ]
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'rules': rules,
        }
        
        return render(request, 'alert_system/alert_rules.html', context)
        
    except Exception as e:
        return render(request, 'alert_system/error.html', {'error': str(e)})


@login_required
def alert_history(request, company_slug):
    """Uyarı geçmişi"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # POST işlemleri (AJAX)
        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            action = data.get('action')
            alert_id = data.get('alert_id')
            
            # Session'da uyarı verilerini sakla (gerçek uygulamada veritabanında olur)
            if 'alerts_data' not in request.session:
                now = timezone.now()
                request.session['alerts_data'] = [
                    {
                        'id': 1,
                        'title': 'Yüksek CPU Kullanımı Tespit Edildi',
                        'severity': 'high',
                        'status': 'new',
                        'type': 'performance',
                        'triggered_at': (now - timedelta(hours=3)).isoformat(),
                        'resolved_at': None,
                        'resolved_by': None,
                        'device': 'Server-01',
                        'resolution_notes': None
                    },
                    {
                        'id': 2,
                        'title': 'Disk Alanı Kritik Seviyede',
                        'severity': 'high',
                        'status': 'acknowledged',
                        'type': 'performance',
                        'triggered_at': (now - timedelta(days=1)).isoformat(),
                        'resolved_at': None,
                        'resolved_by': None,
                        'device': 'Storage-01',
                        'resolution_notes': None
                    },
                    {
                        'id': 3,
                        'title': 'VPN Bağlantısı Kesildi',
                        'severity': 'medium',
                        'status': 'acknowledged',
                        'type': 'network',
                        'triggered_at': (now - timedelta(days=2)).isoformat(),
                        'resolved_at': None,
                        'resolved_by': None,
                        'device': 'VPN-01',
                        'resolution_notes': None
                    },
                    {
                        'id': 4,
                        'title': 'Şüpheli Login Denemesi',
                        'severity': 'critical',
                        'status': 'resolved',
                        'type': 'security',
                        'triggered_at': (now - timedelta(days=3)).isoformat(),
                        'resolved_at': (now - timedelta(days=3, hours=-2)).isoformat(),
                        'resolved_by': 'admin@company.com',
                        'device': 'Auth-01',
                        'resolution_notes': 'IP adresi firewall\'da engellendi, güvenlik güncellendi.'
                    }
                ]
            
            alerts_data = request.session['alerts_data']
            
            if action == 'resolve':
                # Uyarıyı çözüldü olarak işaretle
                for alert in alerts_data:
                    if alert['id'] == alert_id:
                        alert['status'] = 'resolved'
                        alert['resolved_at'] = timezone.now().isoformat()
                        alert['resolved_by'] = request.user.email or request.user.username
                        alert['resolution_notes'] = 'Uyarı çözüldü olarak işaretlendi.'
                        break
                request.session['alerts_data'] = alerts_data
                return JsonResponse({'success': True, 'message': 'Uyarı çözüldü olarak işaretlendi.'})
                
            elif action == 'acknowledge':
                # Uyarıyı kabul edildi olarak işaretle
                for alert in alerts_data:
                    if alert['id'] == alert_id:
                        alert['status'] = 'acknowledged'
                        break
                request.session['alerts_data'] = alerts_data
                return JsonResponse({'success': True, 'message': 'Uyarı kabul edildi olarak işaretlendi.'})
            else:
                return JsonResponse({'success': False, 'error': 'Geçersiz işlem.'})
        
        # Session'dan uyarı verilerini al veya varsayılan verileri oluştur
        if 'alerts_data' not in request.session:
            now = timezone.now()
            request.session['alerts_data'] = [
                {
                    'id': 1,
                    'title': 'Yüksek CPU Kullanımı Tespit Edildi',
                    'severity': 'high',
                    'status': 'new',
                    'type': 'performance',
                    'triggered_at': (now - timedelta(hours=3)).isoformat(),
                    'resolved_at': None,
                    'resolved_by': None,
                    'device': 'Server-01',
                    'resolution_notes': None
                },
                {
                    'id': 2,
                    'title': 'Disk Alanı Kritik Seviyede',
                    'severity': 'high',
                    'status': 'acknowledged',
                    'type': 'performance',
                    'triggered_at': (now - timedelta(days=1)).isoformat(),
                    'resolved_at': None,
                    'resolved_by': None,
                    'device': 'Storage-01',
                    'resolution_notes': None
                },
                {
                    'id': 3,
                    'title': 'VPN Bağlantısı Kesildi',
                    'severity': 'medium',
                    'status': 'acknowledged',
                    'type': 'network',
                    'triggered_at': (now - timedelta(days=2)).isoformat(),
                    'resolved_at': None,
                    'resolved_by': None,
                    'device': 'VPN-01',
                    'resolution_notes': None
                },
                {
                    'id': 4,
                    'title': 'Şüpheli Login Denemesi',
                    'severity': 'critical',
                    'status': 'resolved',
                    'type': 'security',
                    'triggered_at': (now - timedelta(days=3)).isoformat(),
                    'resolved_at': (now - timedelta(days=3, hours=-2)).isoformat(),
                    'resolved_by': 'admin@company.com',
                    'device': 'Auth-01',
                    'resolution_notes': 'IP adresi firewall\'da engellendi, güvenlik güncellendi.'
                }
            ]
        
        alerts_data = request.session['alerts_data']
        
        # ISO string'leri datetime objelerine çevir (template için)
        from datetime import datetime
        alerts = []
        for alert in alerts_data:
            alert_copy = alert.copy()
            if alert['triggered_at']:
                alert_copy['triggered_at'] = datetime.fromisoformat(alert['triggered_at'].replace('Z', '+00:00'))
            if alert['resolved_at']:
                alert_copy['resolved_at'] = datetime.fromisoformat(alert['resolved_at'].replace('Z', '+00:00'))
            alerts.append(alert_copy)
        
        # Filtreleme seçenekleri
        filters = {
            'statuses': ['new', 'acknowledged', 'in_progress', 'resolved', 'closed'],
            'severities': ['info', 'warning', 'error', 'critical'],
            'types': ['security', 'performance', 'network', 'device', 'user', 'system'],
            'date_range': 'last_7_days'
        }
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'alerts': alerts,
            'filters': filters,
        }
        
        return render(request, 'alert_system/alert_history.html', context)
        
    except Exception as e:
        return render(request, 'alert_system/error.html', {'error': str(e)})


@login_required
def alert_notifications(request, company_slug):
    """Uyarı bildirimleri yönetimi"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo bildirim ayarları
        notification_settings = {
            'email_enabled': True,
            'email_recipients': ['admin@company.com', 'tech@company.com'],
            'sms_enabled': False,
            'sms_recipients': [],
            'push_enabled': True,
            'slack_enabled': True,
            'slack_webhook': 'https://hooks.slack.com/services/...',
            'teams_enabled': False,
            'webhook_enabled': True,
            'webhook_url': 'https://company.com/webhook/alerts'
        }
        
        # Bildirim şablonları
        notification_templates = [
            {
                'id': 1,
                'name': 'Kritik Güvenlik Uyarısı',
                'type': 'security',
                'subject': '🚨 KRİTİK: {alert_title}',
                'message': 'Güvenlik uyarısı: {alert_description}\n\nCihaz: {device}\nZaman: {timestamp}\n\nHemen müdahale edin!',
                'is_active': True
            },
            {
                'id': 2,
                'name': 'Performans Uyarısı',
                'type': 'performance',
                'subject': '⚠️ Performans: {alert_title}',
                'message': 'Performans uyarısı: {alert_description}\n\nCihaz: {device}\nZaman: {timestamp}\n\nİnceleme gerekli.',
                'is_active': True
            },
            {
                'id': 3,
                'name': 'Network Uyarısı',
                'type': 'network',
                'subject': '🌐 Network: {alert_title}',
                'message': 'Network uyarısı: {alert_description}\n\nCihaz: {device}\nZaman: {timestamp}\n\nBağlantı kontrol edin.',
                'is_active': True
            }
        ]
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'notification_settings': notification_settings,
            'notification_templates': notification_templates,
        }
        
        return render(request, 'alert_system/notifications.html', context)
        
    except Exception as e:
        return render(request, 'alert_system/error.html', {'error': str(e)})


@login_required
def get_alerts_data(request, company_slug):
    """AJAX ile uyarı verilerini çeker"""
    try:
        # Demo gerçek zamanlı uyarı verisi
        real_time_alerts = {
            'new_alerts_count': random.randint(0, 5),
            'critical_alerts_count': random.randint(0, 2),
            'last_alert_time': timezone.now().isoformat(),
            'active_alerts': random.randint(5, 15)
        }
        
        return JsonResponse({
            'success': True,
            'data': real_time_alerts
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
