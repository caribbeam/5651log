from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth.models import User
from django.utils import timezone
from .models import AuditLog
from log_kayit.models import LogKayit, Company
import json


def get_client_ip(request):
    """Client IP adresini al"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(user, company, action, resource_type, resource_id=None, 
                    resource_name=None, description="", details=None, 
                    severity='LOW', success=True, error_message=None, request=None):
    """Audit log oluştur"""
    
    # IP ve User Agent bilgilerini al
    ip_address = None
    user_agent = None
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Audit log oluştur
    audit_log = AuditLog.objects.create(
        user=user,
        company=company,
        action=action,
        severity=severity,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        description=description,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        error_message=error_message,
        timestamp=timezone.now()
    )
    
    return audit_log


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Kullanıcı giriş logu"""
    # Company bilgisini al (eğer varsa)
    company = None
    if hasattr(request, 'company'):
        company = request.company
    
    create_audit_log(
        user=user,
        company=company,
        action='LOGIN',
        resource_type='User',
        resource_id=str(user.id),
        resource_name=user.username,
        description=f"Kullanıcı giriş yaptı: {user.username}",
        severity='MEDIUM',
        request=request
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Kullanıcı çıkış logu"""
    if user:
        # Company bilgisini al (eğer varsa)
        company = None
        if hasattr(request, 'company'):
            company = request.company
        
        create_audit_log(
            user=user,
            company=company,
            action='LOGOUT',
            resource_type='User',
            resource_id=str(user.id),
            resource_name=user.username,
            description=f"Kullanıcı çıkış yaptı: {user.username}",
            severity='LOW',
            request=request
        )


@receiver(post_save, sender=LogKayit)
def log_logkayit_create_update(sender, instance, created, **kwargs):
    """LogKayit oluşturma/güncelleme logu"""
    action = 'CREATE' if created else 'UPDATE'
    description = f"Log kaydı {'oluşturuldu' if created else 'güncellendi'}: {instance.tc_no}"
    
    create_audit_log(
        user=None,  # Sistem tarafından oluşturuldu
        company=instance.company,
        action=action,
        resource_type='LogKayit',
        resource_id=str(instance.id),
        resource_name=f"TC: {instance.tc_no}",
        description=description,
        details={
            'tc_no': instance.tc_no,
            'mac_address': instance.mac_address,
            'ip_address': instance.ip_address,
            'suspicious': instance.suspicious,
        },
        severity='MEDIUM'
    )


@receiver(post_delete, sender=LogKayit)
def log_logkayit_delete(sender, instance, **kwargs):
    """LogKayit silme logu"""
    create_audit_log(
        user=None,  # Sistem tarafından silindi
        company=instance.company,
        action='DELETE',
        resource_type='LogKayit',
        resource_id=str(instance.id),
        resource_name=f"TC: {instance.tc_no}",
        description=f"Log kaydı silindi: {instance.tc_no}",
        details={
            'tc_no': instance.tc_no,
            'mac_address': instance.mac_address,
            'ip_address': instance.ip_address,
        },
        severity='HIGH'
    )


@receiver(post_save, sender=Company)
def log_company_create_update(sender, instance, created, **kwargs):
    """Company oluşturma/güncelleme logu"""
    action = 'CREATE' if created else 'UPDATE'
    description = f"Şirket {'oluşturuldu' if created else 'güncellendi'}: {instance.name}"
    
    create_audit_log(
        user=None,  # Sistem tarafından oluşturuldu
        company=instance,
        action=action,
        resource_type='Company',
        resource_id=str(instance.id),
        resource_name=instance.name,
        description=description,
        details={
            'name': instance.name,
            'slug': instance.slug,
            'is_active': instance.is_active,
        },
        severity='HIGH'
    )


@receiver(post_save, sender=User)
def log_user_create_update(sender, instance, created, **kwargs):
    """User oluşturma/güncelleme logu"""
    action = 'CREATE' if created else 'UPDATE'
    description = f"Kullanıcı {'oluşturuldu' if created else 'güncellendi'}: {instance.username}"
    
    create_audit_log(
        user=instance,
        company=None,  # User model'inde company yok
        action=action,
        resource_type='User',
        resource_id=str(instance.id),
        resource_name=instance.username,
        description=description,
        details={
            'username': instance.username,
            'email': instance.email,
            'is_active': instance.is_active,
            'is_staff': instance.is_staff,
            'is_superuser': instance.is_superuser,
        },
        severity='HIGH'
    )
