from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import User
from log_kayit.models import Company, CompanyUser
from .models import TwoFactorAuth, TwoFactorAuthLog, TwoFactorAuthSettings, TwoFactorAuthAttempt
import json


def get_client_ip(request):
    """Client IP adresini al"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_2fa_action(user, action, success=True, ip_address=None, user_agent=None, details=None):
    """2FA işlemini logla"""
    TwoFactorAuthLog.objects.create(
        user=user,
        action=action,
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {}
    )


@login_required
def setup_2fa(request, company_slug):
    """2FA kurulum sayfası"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # 2FA objesi al veya oluştur
    two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'enable':
            token = request.POST.get('token')
            if two_factor.verify_token(token):
                two_factor.is_enabled = True
                two_factor.save()
                
                # Yedek tokenlar oluştur
                backup_tokens = two_factor.generate_backup_tokens()
                
                log_2fa_action(
                    request.user, 
                    'ENABLE', 
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                
                messages.success(request, '2FA başarıyla aktif edildi!')
                return render(request, 'two_factor_auth/backup_tokens.html', {
                    'company': company,
                    'backup_tokens': backup_tokens
                })
            else:
                messages.error(request, 'Geçersiz token! Lütfen tekrar deneyin.')
        
        elif action == 'disable':
            password = request.POST.get('password')
            if request.user.check_password(password):
                two_factor.is_enabled = False
                two_factor.save()
                
                log_2fa_action(
                    request.user, 
                    'DISABLE', 
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                
                messages.success(request, '2FA deaktif edildi.')
            else:
                messages.error(request, 'Yanlış şifre!')
        
        elif action == 'regenerate_backup':
            backup_tokens = two_factor.generate_backup_tokens()
            
            log_2fa_action(
                request.user, 
                'BACKUP_GENERATED', 
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            return render(request, 'two_factor_auth/backup_tokens.html', {
                'company': company,
                'backup_tokens': backup_tokens
            })
    
    context = {
        'company': company,
        'two_factor': two_factor,
        'qr_code': two_factor.get_qr_code_image(),
        'secret_key': two_factor.secret_key,
    }
    
    return render(request, 'two_factor_auth/setup.html', context)


def verify_2fa(request):
    """2FA doğrulama sayfası"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        token = request.POST.get('token')
        backup_token = request.POST.get('backup_token')
        
        if not username or not password:
            messages.error(request, 'Kullanıcı adı ve şifre gerekli!')
            return render(request, 'two_factor_auth/verify.html')
        
        # Kullanıcıyı doğrula
        user = authenticate(request, username=username, password=password)
        if not user:
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre!')
            return render(request, 'two_factor_auth/verify.html')
        
        # 2FA kontrolü
        try:
            two_factor = TwoFactorAuth.objects.get(user=user)
            if not two_factor.is_enabled:
                # 2FA aktif değil, normal giriş
                login(request, user)
                return redirect('log_kayit:company_dashboard_slug', 'demo-kafe')  # Default company
        except TwoFactorAuth.DoesNotExist:
            # 2FA kurulmamış, normal giriş
            login(request, user)
            return redirect('log_kayit:company_dashboard_slug', 'demo-kafe')
        
        # IP ve attempt kontrolü
        ip_address = get_client_ip(request)
        attempt, created = TwoFactorAuthAttempt.objects.get_or_create(
            user=user,
            ip_address=ip_address
        )
        
        if attempt.is_locked():
            messages.error(request, f'Hesap geçici olarak kilitli. Lütfen daha sonra deneyin.')
            log_2fa_action(user, 'LOGIN_FAILED', False, ip_address, request.META.get('HTTP_USER_AGENT'))
            return render(request, 'two_factor_auth/verify.html')
        
        # Token doğrulama
        token_valid = False
        
        if token and two_factor.verify_token(token):
            token_valid = True
        elif backup_token and two_factor.verify_backup_token(backup_token):
            token_valid = True
            log_2fa_action(user, 'BACKUP_USED', True, ip_address, request.META.get('HTTP_USER_AGENT'))
        
        if token_valid:
            # Başarılı giriş
            attempt.reset_attempts()
            login(request, user)
            
            log_2fa_action(user, 'LOGIN_SUCCESS', True, ip_address, request.META.get('HTTP_USER_AGENT'))
            
            # Redirect to intended page or default
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            
            return redirect('log_kayit:company_dashboard_slug', 'demo-kafe')
        else:
            # Başarısız giriş
            attempt.increment_failed_attempts()
            
            log_2fa_action(user, 'LOGIN_FAILED', False, ip_address, request.META.get('HTTP_USER_AGENT'))
            
            if backup_token:
                messages.error(request, 'Geçersiz yedek token!')
            else:
                messages.error(request, 'Geçersiz 2FA token!')
    
    return render(request, 'two_factor_auth/verify.html')


@login_required
def dashboard_2fa(request, company_slug):
    """2FA yönetim dashboard'u"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # İstatistikler
    total_users = User.objects.count()
    enabled_2fa = TwoFactorAuth.objects.filter(is_enabled=True).count()
    recent_logs = TwoFactorAuthLog.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Sistem ayarları
    settings = TwoFactorAuthSettings.get_settings()
    
    context = {
        'company': company,
        'total_users': total_users,
        'enabled_2fa': enabled_2fa,
        'recent_logs': recent_logs,
        'settings': settings,
        'user_2fa': TwoFactorAuth.objects.filter(user=request.user).first(),
    }
    
    return render(request, 'two_factor_auth/dashboard.html', context)


@login_required
def settings_2fa(request, company_slug):
    """2FA sistem ayarları"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü (sadece admin)
    if not request.user.is_superuser:
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    settings = TwoFactorAuthSettings.get_settings()
    
    if request.method == 'POST':
        settings.enforce_for_admins = request.POST.get('enforce_for_admins') == 'on'
        settings.enforce_for_all = request.POST.get('enforce_for_all') == 'on'
        settings.backup_tokens_count = int(request.POST.get('backup_tokens_count', 10))
        settings.token_validity_window = int(request.POST.get('token_validity_window', 1))
        settings.max_failed_attempts = int(request.POST.get('max_failed_attempts', 5))
        settings.lockout_duration = int(request.POST.get('lockout_duration', 300))
        settings.save()
        
        messages.success(request, '2FA ayarları güncellendi.')
    
    context = {
        'company': company,
        'settings': settings,
    }
    
    return render(request, 'two_factor_auth/settings.html', context)


@login_required
def logs_2fa(request, company_slug):
    """2FA logları"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    logs = TwoFactorAuthLog.objects.all().order_by('-created_at')
    
    # Filtreleme
    user_filter = request.GET.get('user')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    success_filter = request.GET.get('success')
    if success_filter:
        logs = logs.filter(success=success_filter == 'true')
    
    # Sayfalama
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'success_filter': success_filter,
        'action_choices': TwoFactorAuthLog.ACTION_CHOICES,
    }
    
    return render(request, 'two_factor_auth/logs.html', context)