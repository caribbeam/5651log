from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from log_kayit.models import Company, CompanyUser
from .models import AuditLog, AuditLogConfig, AuditLogReport
from django.utils.translation import gettext as _


@login_required
def audit_dashboard(request, company_slug):
    """Audit log dashboard"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Son 24 saat
    last_24h = timezone.now() - timedelta(hours=24)
    
    # İstatistikler
    total_logs = AuditLog.objects.filter(company=company).count()
    today_logs = AuditLog.objects.filter(company=company, timestamp__gte=last_24h).count()
    critical_logs = AuditLog.objects.filter(company=company, severity='CRITICAL').count()
    failed_logs = AuditLog.objects.filter(company=company, success=False).count()
    
    # Son loglar
    recent_logs = AuditLog.objects.filter(company=company).order_by('-timestamp')[:10]
    
    # Action dağılımı
    action_stats = AuditLog.objects.filter(company=company).values('action').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Severity dağılımı
    severity_stats = AuditLog.objects.filter(company=company).values('severity').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'company': company,
        'total_logs': total_logs,
        'today_logs': today_logs,
        'critical_logs': critical_logs,
        'failed_logs': failed_logs,
        'recent_logs': recent_logs,
        'action_stats': action_stats,
        'severity_stats': severity_stats,
    }
    
    return render(request, 'audit_logging/dashboard.html', context)


@login_required
def audit_logs_list(request, company_slug):
    """Audit logları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Filtreleme
    logs = AuditLog.objects.filter(company=company)
    
    # Arama
    search = request.GET.get('search', '')
    if search:
        logs = logs.filter(
            Q(user__username__icontains=search) |
            Q(resource_name__icontains=search) |
            Q(description__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    # Filtreler
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    severity_filter = request.GET.get('severity', '')
    if severity_filter:
        logs = logs.filter(severity=severity_filter)
    
    success_filter = request.GET.get('success', '')
    if success_filter:
        logs = logs.filter(success=success_filter == 'true')
    
    # Tarih filtresi
    date_from = request.GET.get('date_from', '')
    if date_from:
        logs = logs.filter(timestamp__gte=date_from)
    
    date_to = request.GET.get('date_to', '')
    if date_to:
        logs = logs.filter(timestamp__lte=date_to)
    
    # Sayfalama
    paginator = Paginator(logs.order_by('-timestamp'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'action_filter': action_filter,
        'severity_filter': severity_filter,
        'success_filter': success_filter,
        'date_from': date_from,
        'date_to': date_to,
        'action_choices': AuditLog.ACTION_CHOICES,
        'severity_choices': AuditLog.SEVERITY_CHOICES,
    }
    
    return render(request, 'audit_logging/logs_list.html', context)


@login_required
def audit_log_detail(request, company_slug, log_id):
    """Audit log detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    log = get_object_or_404(AuditLog, id=log_id, company=company)
    
    context = {
        'company': company,
        'log': log,
    }
    
    return render(request, 'audit_logging/log_detail.html', context)


@login_required
def audit_config(request, company_slug):
    """Audit log konfigürasyonu"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Konfigürasyon güncelle
        for action, _ in AuditLog.ACTION_CHOICES:
            enabled = request.POST.get(f'action_{action}', False)
            severity = request.POST.get(f'severity_{action}', 'LOW')
            retention_days = request.POST.get(f'retention_{action}', 365)
            
            config, created = AuditLogConfig.objects.get_or_create(
                company=company,
                action=action,
                defaults={
                    'enabled': bool(enabled),
                    'severity': severity,
                    'retention_days': int(retention_days)
                }
            )
            
            if not created:
                config.enabled = bool(enabled)
                config.severity = severity
                config.retention_days = int(retention_days)
                config.save()
    
    # Mevcut konfigürasyonlar
    configs = AuditLogConfig.objects.filter(company=company)
    config_dict = {config.action: config for config in configs}
    
    context = {
        'company': company,
        'action_choices': AuditLog.ACTION_CHOICES,
        'severity_choices': AuditLog.SEVERITY_CHOICES,
        'configs': config_dict,
    }
    
    return render(request, 'audit_logging/config.html', context)


@login_required
def audit_reports(request, company_slug):
    """Audit log raporları"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    reports = AuditLogReport.objects.filter(company=company).order_by('-generated_at')
    
    context = {
        'company': company,
        'reports': reports,
    }
    
    return render(request, 'audit_logging/reports.html', context)


@login_required
def audit_statistics(request, company_slug):
    """Audit log istatistikleri"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Son 30 gün
    last_30_days = timezone.now() - timedelta(days=30)
    
    # Günlük istatistikler
    daily_stats = AuditLog.objects.filter(
        company=company,
        timestamp__gte=last_30_days
    ).extra(
        select={'day': 'date(timestamp)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Action istatistikleri
    action_stats = AuditLog.objects.filter(company=company).values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Severity istatistikleri
    severity_stats = AuditLog.objects.filter(company=company).values('severity').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # User istatistikleri
    user_stats = AuditLog.objects.filter(
        company=company,
        user__isnull=False
    ).values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'company': company,
        'daily_stats': daily_stats,
        'action_stats': action_stats,
        'severity_stats': severity_stats,
        'user_stats': user_stats,
    }
    
    return render(request, 'audit_logging/statistics.html', context)