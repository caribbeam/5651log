"""
Analytics Dashboard Views
5651log platformunda AI destekli analizler için view'lar
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta
import json
import random

from log_kayit.models import Company


@login_required
def analytics_dashboard(request, company_slug):
    """Ana analiz dashboard'u"""
    try:
        # Company bilgisini veritabanından al
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo analiz verileri
        analytics_data = {
            'total_metrics': 1250,
            'active_insights': 8,
            'ai_models': 5,
            'prediction_accuracy': 94.2,
            'anomalies_detected': 12,
            'trends_identified': 6,
        }
        
        # Son 7 günlük metrik trendi
        daily_metrics = []
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            daily_metrics.append({
                'date': date.strftime('%Y-%m-%d'),
                'network_traffic': random.randint(800, 1200),
                'security_events': random.randint(5, 25),
                'user_activity': random.randint(150, 300),
                'device_performance': random.randint(85, 98)
            })
        
        # AI içgörüleri
        ai_insights = [
            {
                'id': 1,
                'title': 'Network Trafik Anomalisi Tespit Edildi',
                'type': 'anomaly',
                'severity': 'high',
                'confidence': 92.5,
                'description': 'Son 2 saatte normal seviyenin %150 üzerinde network trafiği gözlemlendi.',
                'timestamp': timezone.now() - timedelta(hours=2),
                'recommendations': ['Bandwidth analizi yapın', 'Şüpheli bağlantıları kontrol edin']
            },
            {
                'id': 2,
                'title': 'Kullanıcı Davranış Kalıbı Tespit Edildi',
                'type': 'pattern',
                'severity': 'medium',
                'confidence': 87.3,
                'description': '5 kullanıcı benzer şüpheli aktivite kalıbı gösteriyor.',
                'timestamp': timezone.now() - timedelta(hours=4),
                'recommendations': ['Kullanıcı aktivitelerini inceleyin', 'Güvenlik politikalarını gözden geçirin']
            },
            {
                'id': 3,
                'title': 'Performans Tahmini: Yüksek CPU Kullanımı',
                'type': 'prediction',
                'severity': 'warning',
                'confidence': 78.9,
                'description': 'Önümüzdeki 2 saatte CPU kullanımı %90\'ın üzerine çıkabilir.',
                'timestamp': timezone.now() - timedelta(hours=1),
                'recommendations': ['Kaynak kullanımını optimize edin', 'Yedek sunucuları hazırlayın']
            }
        ]
        
        # Performans metrikleri
        performance_metrics = {
            'cpu_usage': 67.5,
            'memory_usage': 78.2,
            'disk_usage': 45.8,
            'network_bandwidth': 82.1,
            'response_time': 145,
            'throughput': 1250
        }
        
        # Güvenlik metrikleri
        security_metrics = {
            'threats_blocked': 156,
            'vulnerabilities_found': 8,
            'incidents_resolved': 12,
            'risk_score': 23.5,
            'compliance_score': 94.8
        }
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'analytics_data': analytics_data,
            'daily_metrics': daily_metrics,
            'ai_insights': ai_insights,
            'performance_metrics': performance_metrics,
            'security_metrics': security_metrics,
        }
        
        
        return render(request, 'analytics_dashboard/dashboard.html', context)
        
    except Exception as e:
        return render(request, 'analytics_dashboard/error.html', {'error': str(e)})


@login_required
def ai_insights(request, company_slug):
    """AI içgörüleri sayfası"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo AI içgörüleri
        insights = [
            {
                'id': 1,
                'title': 'Network Trafik Anomalisi',
                'type': 'anomaly',
                'severity': 'high',
                'confidence': 92.5,
                'description': 'Son 2 saatte normal seviyenin %150 üzerinde network trafiği gözlemlendi.',
                'timestamp': timezone.now() - timedelta(hours=2),
                'data_source': 'Network Monitoring',
                'recommendations': ['Bandwidth analizi yapın', 'Şüpheli bağlantıları kontrol edin']
            },
            {
                'id': 2,
                'title': 'Kullanıcı Davranış Kalıbı',
                'type': 'pattern',
                'severity': 'medium',
                'confidence': 87.3,
                'description': '5 kullanıcı benzer şüpheli aktivite kalıbı gösteriyor.',
                'timestamp': timezone.now() - timedelta(hours=4),
                'data_source': 'User Activity Logs',
                'recommendations': ['Kullanıcı aktivitelerini inceleyin', 'Güvenlik politikalarını gözden geçirin']
            },
            {
                'id': 3,
                'title': 'Performans Tahmini',
                'type': 'prediction',
                'severity': 'warning',
                'confidence': 78.9,
                'description': 'Önümüzdeki 2 saatte CPU kullanımı %90\'ın üzerine çıkabilir.',
                'timestamp': timezone.now() - timedelta(hours=1),
                'data_source': 'Performance Monitoring',
                'recommendations': ['Kaynak kullanımını optimize edin', 'Yedek sunucuları hazırlayın']
            },
            {
                'id': 4,
                'title': 'Güvenlik Risk Değerlendirmesi',
                'type': 'risk_assessment',
                'severity': 'medium',
                'confidence': 85.2,
                'description': '3 cihazda güvenlik açığı tespit edildi.',
                'timestamp': timezone.now() - timedelta(hours=6),
                'data_source': 'Security Scanner',
                'recommendations': ['Güvenlik güncellemelerini yapın', 'Firewall kurallarını gözden geçirin']
            }
        ]
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'insights': insights,
        }
        
        return render(request, 'analytics_dashboard/ai_insights.html', context)
        
    except Exception as e:
        return render(request, 'analytics_dashboard/error.html', {'error': str(e)})


@login_required
def predictive_analytics(request, company_slug):
    """Tahmin analizleri sayfası"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo tahmin verileri
        predictions = {
            'traffic_prediction': {
                'next_hour': 1250,
                'next_6_hours': 1100,
                'next_24_hours': 980,
                'confidence': 89.5
            },
            'performance_prediction': {
                'cpu_next_hour': 78.5,
                'memory_next_hour': 82.1,
                'disk_next_hour': 48.9,
                'confidence': 76.8
            },
            'security_prediction': {
                'threats_next_hour': 12,
                'vulnerabilities_next_day': 5,
                'incidents_next_week': 8,
                'confidence': 82.3
            }
        }
        
        # Trend analizi
        trends = [
            {'metric': 'Network Trafik', 'trend': 'increasing', 'change': '+15%', 'confidence': 87.2},
            {'metric': 'CPU Kullanımı', 'trend': 'stable', 'change': '0%', 'confidence': 92.1},
            {'metric': 'Güvenlik Olayları', 'trend': 'decreasing', 'change': '-8%', 'confidence': 78.9},
            {'metric': 'Kullanıcı Aktivitesi', 'trend': 'increasing', 'change': '+22%', 'confidence': 85.4}
        ]
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'predictions': predictions,
            'trends': trends,
        }
        
        return render(request, 'analytics_dashboard/predictive_analytics.html', context)
        
    except Exception as e:
        return render(request, 'analytics_dashboard/error.html', {'error': str(e)})


@login_required
def user_behavior_analysis(request, company_slug):
    """Kullanıcı davranış analizi sayfası"""
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Demo kullanıcı davranış verileri
        behavior_patterns = [
            {
                'user': 'user1@company.com',
                'pattern_type': 'Suspicious Login Pattern',
                'confidence': 89.5,
                'frequency': 15,
                'first_seen': timezone.now() - timedelta(days=3),
                'last_seen': timezone.now(),
                'description': 'Farklı IP adreslerinden düzenli giriş denemeleri'
            },
            {
                'user': 'user2@company.com',
                'pattern_type': 'Unusual File Access',
                'confidence': 76.8,
                'frequency': 8,
                'first_seen': timezone.now() - timedelta(days=2),
                'last_seen': timezone.now(),
                'description': 'Normal çalışma saatleri dışında dosya erişimi'
            },
            {
                'user': 'user3@company.com',
                'pattern_type': 'Bandwidth Anomaly',
                'confidence': 92.1,
                'frequency': 23,
                'first_seen': timezone.now() - timedelta(days=5),
                'last_seen': timezone.now(),
                'description': 'Normal seviyenin 3 katı bandwidth kullanımı'
            }
        ]
        
        # Kullanıcı aktivite istatistikleri
        activity_stats = {
            'total_users': 45,
            'active_users': 38,
            'suspicious_users': 3,
            'blocked_users': 1,
            'avg_session_duration': 145,
            'peak_activity_hour': '14:00'
        }
        
        context = {
            'company': company,
            'company_slug': company_slug,
            'behavior_patterns': behavior_patterns,
            'activity_stats': activity_stats,
        }
        
        return render(request, 'analytics_dashboard/user_behavior.html', context)
        
    except Exception as e:
        return render(request, 'analytics_dashboard/error.html', {'error': str(e)})


@login_required
def get_analytics_data(request, company_slug):
    """AJAX ile analiz verilerini çeker"""
    try:
        # Demo gerçek zamanlı veri
        real_time_data = {
            'current_traffic': random.randint(800, 1200),
            'active_connections': random.randint(150, 300),
            'cpu_usage': random.uniform(60, 90),
            'memory_usage': random.uniform(70, 95),
            'security_events': random.randint(5, 25),
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'data': real_time_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
