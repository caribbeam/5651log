from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from ..models import LogKayit, Company
import json

class AnalyticsService:
    """Gelişmiş analitik ve raporlama servisleri"""
    
    @staticmethod
    def get_company_overview(company, days=30):
        """Şirket genel bakış raporu"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        logs = LogKayit.objects.filter(
            company=company,
            giris_zamani__range=(start_date, end_date)
        )
        
        # Günlük giriş sayıları
        daily_stats = logs.extra(
            select={'day': 'date(giris_zamani)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        # En aktif kullanıcılar
        top_users = logs.values('ad_soyad').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Şüpheli giriş analizi
        suspicious_stats = logs.filter(is_suspicious=True).aggregate(
            total=Count('id'),
            percentage=Count('id') * 100.0 / logs.count() if logs.count() > 0 else 0
        )
        
        # Saatlik dağılım
        hourly_stats = logs.extra(
            select={'hour': 'extract(hour from giris_zamani)'}
        ).values('hour').annotate(count=Count('id')).order_by('hour')
        
        return {
            'period': f'{days} gün',
            'total_logs': logs.count(),
            'daily_stats': list(daily_stats),
            'top_users': list(top_users),
            'suspicious_stats': suspicious_stats,
            'hourly_stats': list(hourly_stats),
            'avg_daily_logs': logs.count() / days if days > 0 else 0,
        }
    
    @staticmethod
    def detect_anomalies(company, days=7):
        """Anormal giriş tespiti"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        logs = LogKayit.objects.filter(
            company=company,
            giris_zamani__range=(start_date, end_date)
        )
        
        # Günlük ortalama giriş sayısı
        daily_avg = logs.count() / days if days > 0 else 0
        
        # Günlük giriş sayıları
        daily_counts = logs.extra(
            select={'day': 'date(giris_zamani)'}
        ).values('day').annotate(count=Count('id'))
        
        anomalies = []
        for day_data in daily_counts:
            count = day_data['count']
            if count > daily_avg * 2:  # 2x ortalama üzeri
                anomalies.append({
                    'date': day_data['day'],
                    'count': count,
                    'expected': round(daily_avg, 1),
                    'type': 'high_traffic'
                })
            elif count < daily_avg * 0.3:  # %30 altı
                anomalies.append({
                    'date': day_data['day'],
                    'count': count,
                    'expected': round(daily_avg, 1),
                    'type': 'low_traffic'
                })
        
        return {
            'period': f'{days} gün',
            'daily_average': round(daily_avg, 1),
            'anomalies': anomalies,
            'total_anomalies': len(anomalies)
        }
    
    @staticmethod
    def get_user_behavior_patterns(company, days=30):
        """Kullanıcı davranış analizi"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        logs = LogKayit.objects.filter(
            company=company,
            giris_zamani__range=(start_date, end_date)
        )
        
        # Tek seferlik kullanıcılar
        one_time_users = logs.values('ad_soyad').annotate(
            count=Count('id')
        ).filter(count=1).count()
        
        # Düzenli kullanıcılar (haftada 3+ giriş)
        regular_users = logs.values('ad_soyad').annotate(
            count=Count('id')
        ).filter(count__gte=3).count()
        
        # En sık giriş yapan kullanıcılar
        frequent_users = logs.values('ad_soyad').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Kullanıcı segmentasyonu
        user_segments = {
            'one_time': one_time_users,
            'occasional': logs.values('ad_soyad').annotate(
                count=Count('id')
            ).filter(count__range=(2, 5)).count(),
            'regular': regular_users,
            'frequent': logs.values('ad_soyad').annotate(
                count=Count('id')
            ).filter(count__gt=5).count(),
        }
        
        return {
            'period': f'{days} gün',
            'total_unique_users': logs.values('ad_soyad').distinct().count(),
            'user_segments': user_segments,
            'frequent_users': list(frequent_users),
            'avg_logs_per_user': logs.count() / logs.values('ad_soyad').distinct().count() if logs.values('ad_soyad').distinct().count() > 0 else 0,
        }
    
    @staticmethod
    def generate_compliance_report(company, start_date=None, end_date=None):
        """5651 uyumluluk raporu"""
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        logs = LogKayit.objects.filter(
            company=company,
            giris_zamani__range=(start_date, end_date)
        )
        
        # Yasal gereklilikler kontrolü
        compliance_checks = {
            'total_records': logs.count(),
            'valid_identity_records': logs.filter(
                Q(tc_no__isnull=False) | Q(pasaport_no__isnull=False)
            ).count(),
            'suspicious_records': logs.filter(is_suspicious=True).count(),
            'complete_records': logs.filter(
                Q(tc_no__isnull=False) | Q(pasaport_no__isnull=False),
                ad_soyad__isnull=False,
                ip_adresi__isnull=False,
                mac_adresi__isnull=False
            ).count(),
        }
        
        # Uyumluluk yüzdesi
        compliance_percentage = (
            compliance_checks['complete_records'] / compliance_checks['total_records'] * 100
        ) if compliance_checks['total_records'] > 0 else 0
        
        return {
            'period': f'{start_date.strftime("%d.%m.%Y")} - {end_date.strftime("%d.%m.%Y")}',
            'compliance_checks': compliance_checks,
            'compliance_percentage': round(compliance_percentage, 2),
            'is_compliant': compliance_percentage >= 95,  # %95 üzeri uyumlu
            'recommendations': _get_compliance_recommendations(compliance_checks, compliance_percentage)
        }

def _get_compliance_recommendations(checks, percentage):
    """Uyumluluk önerileri"""
    recommendations = []
    
    if percentage < 95:
        recommendations.append("Veri kalitesi artırılmalı - eksik kayıtlar tamamlanmalı")
    
    if checks['suspicious_records'] > 0:
        recommendations.append("Şüpheli kayıtlar incelenmeli ve gerekirse düzeltilmeli")
    
    if checks['valid_identity_records'] < checks['total_records']:
        recommendations.append("Tüm kayıtlarda kimlik bilgisi bulunmalı")
    
    return recommendations
