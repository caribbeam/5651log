"""
Sistem sağlık kontrolü komutu
"""
import psutil
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from log_kayit.models import Company, LogKayit


class Command(BaseCommand):
    help = 'Sistem sağlık durumunu kontrol eder'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Sistem Sağlık Kontrolü Başlıyor...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'OK',
            'checks': {}
        }
        
        # 1. Disk Kullanımı
        disk_usage = psutil.disk_usage('/')
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        health_status['checks']['disk_usage'] = {
            'percent': round(disk_percent, 2),
            'free_gb': round(disk_usage.free / (1024**3), 2),
            'status': 'OK' if disk_percent < 80 else 'WARNING' if disk_percent < 90 else 'CRITICAL'
        }
        
        # 2. RAM Kullanımı
        memory = psutil.virtual_memory()
        health_status['checks']['memory_usage'] = {
            'percent': memory.percent,
            'available_gb': round(memory.available / (1024**3), 2),
            'status': 'OK' if memory.percent < 80 else 'WARNING' if memory.percent < 90 else 'CRITICAL'
        }
        
        # 3. CPU Kullanımı
        cpu_percent = psutil.cpu_percent(interval=1)
        health_status['checks']['cpu_usage'] = {
            'percent': cpu_percent,
            'status': 'OK' if cpu_percent < 70 else 'WARNING' if cpu_percent < 85 else 'CRITICAL'
        }
        
        # 4. Veritabanı Bağlantısı
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = {
                'status': 'OK',
                'message': 'Veritabanı bağlantısı başarılı'
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'ERROR',
                'message': f'Veritabanı hatası: {str(e)}'
            }
            health_status['status'] = 'ERROR'
        
        # 5. Uygulama Verileri
        try:
            company_count = Company.objects.count()
            log_count = LogKayit.objects.count()
            recent_logs = LogKayit.objects.filter(
                giris_zamani__gte=datetime.now().replace(hour=0, minute=0, second=0)
            ).count()
            
            health_status['checks']['application_data'] = {
                'status': 'OK',
                'company_count': company_count,
                'total_logs': log_count,
                'today_logs': recent_logs
            }
        except Exception as e:
            health_status['checks']['application_data'] = {
                'status': 'ERROR',
                'message': f'Uygulama veri hatası: {str(e)}'
            }
            health_status['status'] = 'ERROR'
        
        # 6. Log Dosyaları
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        if os.path.exists(logs_dir):
            log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
            health_status['checks']['log_files'] = {
                'status': 'OK',
                'count': len(log_files),
                'files': log_files
            }
        else:
            health_status['checks']['log_files'] = {
                'status': 'WARNING',
                'message': 'Log klasörü bulunamadı'
            }
        
        # Genel durum belirleme
        critical_issues = []
        warnings = []
        
        for check_name, check_data in health_status['checks'].items():
            if check_data['status'] == 'CRITICAL':
                critical_issues.append(f"{check_name}: {check_data.get('message', 'Kritik seviye aşıldı')}")
            elif check_data['status'] == 'WARNING':
                warnings.append(f"{check_name}: {check_data.get('message', 'Uyarı seviyesi')}")
        
        if critical_issues:
            health_status['status'] = 'CRITICAL'
        elif warnings:
            health_status['status'] = 'WARNING'
        
        # Sonuçları göster
        self.stdout.write(f"\n📊 Sistem Durumu: {health_status['status']}")
        
        if critical_issues:
            self.stdout.write(self.style.ERROR("🚨 KRİTİK SORUNLAR:"))
            for issue in critical_issues:
                self.stdout.write(self.style.ERROR(f"  - {issue}"))
        
        if warnings:
            self.stdout.write(self.style.WARNING("⚠️ UYARILAR:"))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f"  - {warning}"))
        
        if health_status['status'] == 'OK':
            self.stdout.write(self.style.SUCCESS("✅ Tüm sistemler normal çalışıyor"))
        
        # Detaylı bilgiler
        self.stdout.write(f"\n📈 Detaylı Bilgiler:")
        self.stdout.write(f"  💾 Disk Kullanımı: {health_status['checks']['disk_usage']['percent']}%")
        self.stdout.write(f"  🧠 RAM Kullanımı: {health_status['checks']['memory_usage']['percent']}%")
        self.stdout.write(f"  ⚡ CPU Kullanımı: {health_status['checks']['cpu_usage']['percent']}%")
        
        if 'application_data' in health_status['checks']:
            app_data = health_status['checks']['application_data']
            if app_data['status'] == 'OK':
                self.stdout.write(f"  🏢 Şirket Sayısı: {app_data['company_count']}")
                self.stdout.write(f"  📝 Toplam Log: {app_data['total_logs']}")
                self.stdout.write(f"  📅 Bugünkü Log: {app_data['today_logs']}")
        
        return health_status
