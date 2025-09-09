"""
Zaman Damgası View'ları
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from log_kayit.models import Company, CompanyUser
from .models import TimestampSignature, TimestampConfiguration, TimestampLog, TimestampAuthority
from .services import BatchTimestampService


@login_required
def timestamp_dashboard(request, company_slug):
    """Zaman damgası dashboard'u"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # İstatistikler (şimdilik 0 olarak ayarlayalım)
    total_signatures = 0
    signed_count = 0
    verified_count = 0
    failed_count = 0
    
    # Son 30 günlük imza sayıları (örnek veri)
    daily_signatures = []
    for i in range(30):
        date = timezone.now() - timedelta(days=29-i)
        daily_signatures.append({
            'date': date.strftime('%d.%m'),
            'count': 0  # Şimdilik 0
        })
    
    # Son imzalar (şimdilik boş)
    recent_signatures = []
    
    # Konfigürasyon
    config = None
    
    context = {
        'company': company,
        'stats': {
            'total_signatures': total_signatures,
            'signed_count': signed_count,
            'verified_count': verified_count,
            'failed_count': failed_count,
            'success_rate': 0
        },
        'daily_signatures': daily_signatures,
        'recent_signatures': recent_signatures,
        'config': config,
    }
    
    return render(request, 'timestamp_signing/dashboard.html', context)


@login_required
def signatures_list(request, company_slug):
    """İmza listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Gerçek imza listesi
    signatures = TimestampSignature.objects.filter(company=company).order_by('-created_at')
    
    # Filtreleme
    status = request.GET.get('status')
    authority = request.GET.get('authority')
    search = request.GET.get('search')
    
    if status and status != 'all':
        signatures = signatures.filter(status=status)
    
    if authority and authority != 'all':
        signatures = signatures.filter(authority_id=authority)
    
    if search:
        signatures = signatures.filter(
            Q(log_entry__ad_soyad__icontains=search) |
            Q(log_entry__tc_no__icontains=search) |
            Q(serial_number__icontains=search)
        )
    
    # Sayfalama
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(signatures, 50)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'filters': {
            'status': status,
            'authority': authority,
            'search': search
        }
    }
    
    return render(request, 'timestamp_signing/signatures_list.html', context)


@login_required
def signature_detail(request, company_slug, signature_id):
    """İmza detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    signature = get_object_or_404(TimestampSignature, id=signature_id, company=company)
    
    context = {
        'company': company,
        'signature': signature,
    }
    
    return render(request, 'timestamp_signing/signature_detail.html', context)


@login_required
def batch_sign(request, company_slug):
    """Toplu imzalama"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        try:
            # Toplu imzalama servisini başlat
            batch_service = BatchTimestampService(company)
            result = batch_service.sign_pending_logs()
            
            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.error(request, f"Hata: {result['error']}")
                
        except Exception as e:
            messages.error(request, f"Toplu imzalama hatası: {str(e)}")
    
    return redirect('timestamp_signing:dashboard', company_slug=company_slug)


@login_required
def verify_signature(request, company_slug, signature_id):
    """İmza doğrulama"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    signature = get_object_or_404(TimestampSignature, id=signature_id, company=company)
    
    if request.method == 'POST':
        try:
            if signature.verify():
                messages.success(request, "İmza başarıyla doğrulandı.")
            else:
                messages.error(request, "İmza doğrulama başarısız.")
        except Exception as e:
            messages.error(request, f"Doğrulama hatası: {str(e)}")
    
    return redirect('timestamp_signing:signature_detail', company_slug=company_slug, signature_id=signature_id)


@login_required
def configuration(request, company_slug):
    """Konfigürasyon sayfası"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut konfigürasyonu al
    try:
        config = TimestampConfiguration.objects.get(company=company)
    except TimestampConfiguration.DoesNotExist:
        config = None
    
    # Tüm otoriteleri al
    authorities = TimestampAuthority.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Konfigürasyon güncelleme/oluşturma işlemi
        from django.contrib import messages
        
        authority_id = request.POST.get('authority')
        auto_sign = request.POST.get('auto_sign') == 'on'
        sign_interval = int(request.POST.get('sign_interval', 60))
        batch_size = int(request.POST.get('batch_size', 100))
        max_retries = int(request.POST.get('max_retries', 3))
        retry_delay = int(request.POST.get('retry_delay', 300))
        notify_on_success = request.POST.get('notify_on_success') == 'on'
        notify_on_failure = request.POST.get('notify_on_failure') == 'on'
        notification_email = request.POST.get('notification_email', '')
        
        try:
            authority = TimestampAuthority.objects.get(id=authority_id)
            
            if config:
                # Güncelle
                config.authority = authority
                config.auto_sign = auto_sign
                config.sign_interval = sign_interval
                config.batch_size = batch_size
                config.max_retries = max_retries
                config.retry_delay = retry_delay
                config.notify_on_success = notify_on_success
                config.notify_on_failure = notify_on_failure
                config.notification_email = notification_email
                config.save()
                messages.success(request, "Konfigürasyon güncellendi.")
            else:
                # Yeni oluştur
                config = TimestampConfiguration.objects.create(
                    company=company,
                    authority=authority,
                    auto_sign=auto_sign,
                    sign_interval=sign_interval,
                    batch_size=batch_size,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    notify_on_success=notify_on_success,
                    notify_on_failure=notify_on_failure,
                    notification_email=notification_email
                )
                messages.success(request, "Konfigürasyon oluşturuldu.")
                
        except TimestampAuthority.DoesNotExist:
            messages.error(request, "Geçersiz otorite seçimi.")
        except Exception as e:
            messages.error(request, f"Konfigürasyon kaydedilemedi: {str(e)}")
        
        return redirect('timestamp_signing:configuration', company_slug=company_slug)
    
    context = {
        'company': company,
        'config': config,
        'authorities': authorities,
    }
    
    return render(request, 'timestamp_signing/configuration.html', context)


@login_required
def authority_management(request, company_slug):
    """Otorite yönetimi sayfası"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Tüm otoriteleri al
    authorities = TimestampAuthority.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        from django.contrib import messages
        
        action = request.POST.get('action')
        
        if action == 'create':
            # Yeni otorite oluştur
            name = request.POST.get('name')
            authority_type = request.POST.get('authority_type')
            api_endpoint = request.POST.get('api_endpoint')
            api_key = request.POST.get('api_key')
            username = request.POST.get('username')
            password = request.POST.get('password')
            certificate_path = request.POST.get('certificate_path')
            
            try:
                TimestampAuthority.objects.create(
                    name=name,
                    authority_type=authority_type,
                    api_endpoint=api_endpoint,
                    api_key=api_key,
                    username=username,
                    password=password,
                    certificate_path=certificate_path
                )
                messages.success(request, "Otorite başarıyla oluşturuldu.")
            except Exception as e:
                messages.error(request, f"Otorite oluşturulamadı: {str(e)}")
        
        elif action == 'toggle_status':
            # Otorite durumunu değiştir
            authority_id = request.POST.get('authority_id')
            try:
                authority = TimestampAuthority.objects.get(id=authority_id)
                authority.is_active = not authority.is_active
                authority.save()
                messages.success(request, f"Otorite durumu {'aktif' if authority.is_active else 'pasif'} yapıldı.")
            except TimestampAuthority.DoesNotExist:
                messages.error(request, "Otorite bulunamadı.")
        
        return redirect('timestamp_signing:authority_management', company_slug=company_slug)
    
    context = {
        'company': company,
        'authorities': authorities,
    }
    
    return render(request, 'timestamp_signing/authority_management.html', context)


@login_required
def api_signature_stats(request, company_slug):
    """İmza istatistikleri API"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    # Son 7 günlük istatistikler
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    daily_stats = []
    for i in range(7):
        date = seven_days_ago + timedelta(days=i)
        signed_count = TimestampSignature.objects.filter(
            company=company,
            created_at__date=date,
            status='SIGNED'
        ).count()
        
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'signed_count': signed_count
        })
    
    return JsonResponse({
        'daily_stats': daily_stats,
        'total_signatures': TimestampSignature.objects.filter(company=company).count(),
        'success_rate': TimestampSignature.objects.filter(company=company, status='SIGNED').count()
    })
