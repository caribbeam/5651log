"""
Cron job functions for 5651 law compliance and data retention management
"""

import logging
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import LogKayit, Company
from .management.commands.cleanup_old_logs import Command as CleanupCommand

logger = logging.getLogger(__name__)

def cleanup_old_logs():
    """
    Her gün gece 02:00'de 2 yıldan eski logları temizler
    5651 kanunu uyumluluğu için
    """
    try:
        logger.info("Otomatik log temizleme işlemi başlatıldı")
        
        # Cleanup command'ı çalıştır
        cleanup_cmd = CleanupCommand()
        cleanup_cmd.handle()
        
        logger.info("Otomatik log temizleme işlemi tamamlandı")
        
        # Admin'lere bilgilendirme e-postası gönder
        send_cleanup_notification()
        
    except Exception as e:
        logger.error(f"Otomatik log temizleme hatası: {str(e)}")
        # Hata durumunda admin'lere uyarı e-postası gönder
        send_error_notification("Log Temizleme Hatası", str(e))

def generate_retention_report():
    """
    Her hafta Pazar günü 03:00'de veri saklama raporu oluşturur
    """
    try:
        logger.info("Veri saklama raporu oluşturuluyor")
        
        # 2 yıldan eski kayıtları bul
        cutoff_date = timezone.now() - timedelta(days=730)
        old_logs = LogKayit.objects.filter(giris_zamani__lt=cutoff_date)
        
        # Şirket bazında istatistikler
        company_stats = []
        for company in Company.objects.all():
            company_old_logs = company.logkayit_set.filter(giris_zamani__lt=cutoff_date)
            company_stats.append({
                'name': company.name,
                'domain': company.domain,
                'old_logs_count': company_old_logs.count(),
                'total_logs': company.logkayit_set.count(),
                'compliance_status': 'Uyumlu' if company_old_logs.count() == 0 else 'Uyumsuz'
            })
        
        # Rapor oluştur
        report = create_retention_report(company_stats, old_logs.count(), cutoff_date)
        
        # Admin'lere rapor gönder
        send_retention_report(report)
        
        logger.info("Veri saklama raporu oluşturuldu ve gönderildi")
        
    except Exception as e:
        logger.error(f"Veri saklama raporu hatası: {str(e)}")
        send_error_notification("Rapor Oluşturma Hatası", str(e))

def create_retention_report(company_stats, total_old_logs, cutoff_date):
    """
    Veri saklama raporu oluşturur
    """
    report = f"""
    ========================================
    VERİ SAKLAMA RAPORU - 5651 KANUNU
    ========================================
    Tarih: {timezone.now().strftime('%d.%m.%Y %H:%M')}
    Kesim Tarihi: {cutoff_date.strftime('%d.%m.%Y')}
    
    GENEL DURUM:
    - Toplam 2+ yıl eski kayıt: {total_old_logs}
    - Toplam şirket sayısı: {len(company_stats)}
    
    ŞİRKET BAZINDA DURUM:
    """
    
    for stat in company_stats:
        status_icon = "✅" if stat['compliance_status'] == 'Uyumlu' else "⚠️"
        report += f"""
        {status_icon} {stat['name']} ({stat['domain']})
        - Toplam log: {stat['total_logs']}
        - Eski log (2+ yıl): {stat['old_logs_count']}
        - Durum: {stat['compliance_status']}
        """
    
    report += f"""
    
    ÖNERİLER:
    """
    
    if total_old_logs > 0:
        report += f"""
        ⚠️ {total_old_logs} adet eski kayıt bulunmaktadır.
        Bu kayıtlar 5651 kanunu gereği derhal temizlenmelidir.
        
        Temizlik komutu:
        python manage.py cleanup_old_logs
        """
    else:
        report += """
        ✅ Tüm kayıtlar 5651 kanunu uyumludur.
        Herhangi bir işlem gerekmez.
        """
    
    return report

def send_cleanup_notification():
    """
    Log temizleme işlemi sonrası admin'lere bilgilendirme gönderir
    """
    try:
        subject = "5651 Kanunu - Log Temizleme Tamamlandı"
        message = """
        Merhaba,
        
        Otomatik log temizleme işlemi başarıyla tamamlanmıştır.
        2 yıldan eski tüm log kayıtları sistem tarafından temizlenmiştir.
        
        Bu işlem 5651 kanunu uyumluluğu için gereklidir.
        
        Detaylı bilgi için admin panelindeki "Veri Saklama Yönetimi" 
        sayfasını kontrol edebilirsiniz.
        
        Saygılarımızla,
        5651 Log Sistemi
        """
        
        # Admin e-postalarını al (gerçek uygulamada Company modelinden alınabilir)
        admin_emails = get_admin_emails()
        
        for email in admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True
            )
            
    except Exception as e:
        logger.error(f"Bilgilendirme e-postası gönderilemedi: {str(e)}")

def send_retention_report(report):
    """
    Veri saklama raporunu admin'lere gönderir
    """
    try:
        subject = "5651 Kanunu - Haftalık Veri Saklama Raporu"
        
        # Admin e-postalarını al
        admin_emails = get_admin_emails()
        
        for email in admin_emails:
            send_mail(
                subject=subject,
                message=report,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True
            )
            
    except Exception as e:
        logger.error(f"Rapor e-postası gönderilemedi: {str(e)}")

def send_error_notification(error_type, error_message):
    """
    Hata durumunda admin'lere uyarı gönderir
    """
    try:
        subject = f"5651 Kanunu - {error_type}"
        message = f"""
        Merhaba,
        
        Sistemde bir hata oluşmuştur:
        
        Hata Türü: {error_type}
        Hata Mesajı: {error_message}
        Tarih: {timezone.now().strftime('%d.%m.%Y %H:%M')}
        
        Lütfen bu hatayı kontrol ediniz.
        
        Saygılarımızla,
        5651 Log Sistemi
        """
        
        # Admin e-postalarını al
        admin_emails = get_admin_emails()
        
        for email in admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True
            )
            
    except Exception as e:
        logger.error(f"Hata bildirimi gönderilemedi: {str(e)}")

def get_admin_emails():
    """
    Admin e-postalarını döndürür
    """
    try:
        # Company modelinden admin e-postalarını al
        admin_emails = []
        for company in Company.objects.all():
            if company.email:
                admin_emails.append(company.email)
        
        # Eğer hiç e-posta bulunamazsa varsayılan e-posta kullan
        if not admin_emails:
            admin_emails = [getattr(settings, 'ADMIN_EMAIL', 'admin@example.com')]
        
        return admin_emails
        
    except Exception as e:
        logger.error(f"Admin e-postaları alınamadı: {str(e)}")
        return [getattr(settings, 'ADMIN_EMAIL', 'admin@example.com')]
