"""
Kullanıcı yetkilendirme decorator'ları
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils.translation import gettext as _
from django.utils import timezone
from .models import UserPermission, UserActivityLog


def require_permission(permission_name):
    """Belirli bir yetki gerektiren decorator"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Süper kullanıcı her şeyi yapabilir
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Kullanıcının şirket yetkisi var mı?
            from .models import CompanyUser
            try:
                company_user = CompanyUser.objects.get(user=request.user)
                permission = getattr(company_user.permissions, permission_name, False)
                
                if not permission:
                    messages.error(request, _("Bu işlem için yetkiniz bulunmuyor."))
                    return HttpResponseForbidden(_("Yetkisiz erişim"))
                
                # Zaman kontrolü
                if not company_user.permissions.is_access_allowed_now():
                    messages.error(request, _("Bu saatlerde erişim izniniz bulunmuyor."))
                    return HttpResponseForbidden(_("Zaman sınırı"))
                
                # Tarih kontrolü
                if not company_user.permissions.is_valid_date():
                    messages.error(request, _("Hesabınızın geçerlilik süresi dolmuş."))
                    return HttpResponseForbidden(_("Geçerlilik süresi"))
                
                # IP kontrolü
                client_ip = request.META.get('REMOTE_ADDR')
                if not company_user.permissions.is_ip_allowed(client_ip):
                    # Yetkisiz erişim logu
                    UserActivityLog.objects.create(
                        company_user=company_user,
                        action='unauthorized_access',
                        ip_address=client_ip,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        details=f'IP {client_ip} izin verilen listede değil'
                    )
                    messages.error(request, _("Bu IP adresinden erişim izniniz bulunmuyor."))
                    return HttpResponseForbidden(_("IP sınırı"))
                
                # Aktivite logu
                UserActivityLog.objects.create(
                    company_user=company_user,
                    action='view_dashboard' if permission_name == 'can_view_dashboard' else 'other',
                    ip_address=client_ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details=f'{permission_name} yetkisi kullanıldı'
                )
                
                return view_func(request, *args, **kwargs)
                
            except CompanyUser.DoesNotExist:
                messages.error(request, _("Şirket yetkiniz bulunmuyor."))
                return HttpResponseForbidden(_("Şirket yetkisi yok"))
        
        return wrapper
    return decorator


def require_company_admin(view_func):
    """Şirket yöneticisi gerektiren decorator"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        from .models import CompanyUser
        try:
            company_user = CompanyUser.objects.get(user=request.user)
            if company_user.role != 'admin':
                messages.error(request, _("Bu işlem için yönetici yetkisi gerekiyor."))
                return HttpResponseForbidden(_("Yönetici yetkisi gerekli"))
            
            return view_func(request, *args, **kwargs)
            
        except CompanyUser.DoesNotExist:
            messages.error(request, _("Şirket yetkiniz bulunmuyor."))
            return HttpResponseForbidden(_("Şirket yetkisi yok"))
    
    return wrapper


def log_user_activity(action):
    """Kullanıcı aktivitesini loglayan decorator"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            result = view_func(request, *args, **kwargs)
            
            # Aktivite logu kaydet
            if request.user.is_authenticated and not request.user.is_superuser:
                from .models import CompanyUser
                try:
                    company_user = CompanyUser.objects.get(user=request.user)
                    UserActivityLog.objects.create(
                        company_user=company_user,
                        action=action,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        details=f'{action} işlemi gerçekleştirildi'
                    )
                except CompanyUser.DoesNotExist:
                    pass
            
            return result
        return wrapper
    return decorator


def check_user_permissions(view_func):
    """Genel kullanıcı yetki kontrolü"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        from .models import CompanyUser
        try:
            company_user = CompanyUser.objects.get(user=request.user)
            
            # Temel kontroller
            if not company_user.user.is_active:
                messages.error(request, _("Hesabınız deaktif durumda."))
                return redirect('yonetici_login')
            
            # Yetki kontrolü
            if hasattr(company_user, 'permissions'):
                if not company_user.permissions.is_access_allowed_now():
                    messages.error(request, _("Bu saatlerde erişim izniniz bulunmuyor."))
                    return HttpResponseForbidden(_("Zaman sınırı"))
                
                if not company_user.permissions.is_valid_date():
                    messages.error(request, _("Hesabınızın geçerlilik süresi dolmuş."))
                    return HttpResponseForbidden(_("Geçerlilik süresi"))
            
            return view_func(request, *args, **kwargs)
            
        except CompanyUser.DoesNotExist:
            messages.error(request, _("Şirket yetkiniz bulunmuyor."))
            return redirect('yonetici_login')
    
    return wrapper
