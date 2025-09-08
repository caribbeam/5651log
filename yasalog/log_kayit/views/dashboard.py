from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncHour
from django.db.models import Count
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from ..models import LogKayit, Company, CompanyUser
from ..services.analytics import AnalyticsService

def _get_dashboard_statistics(logs, company):
    """Calculates basic statistics and card data for the dashboard."""
    today = timezone.now().date()
    toplam_giris = logs.count()
    suspicious_logs = logs.filter(is_suspicious=True)
    today_logs = logs.filter(giris_zamani__date=today)
    most_active = logs.values('ad_soyad').annotate(count=Count('id')).order_by('-count').first()

    return {
        'toplam_giris': toplam_giris,
        'son_giris': logs.first(),
        'toplam_kullanici': CompanyUser.objects.filter(company=company).count(),
        'toplam_aktif_kullanici': CompanyUser.objects.filter(company=company, user__is_active=True).count(),
        'toplam_suspicious': suspicious_logs.count(),
        'today_total': today_logs.count(),
        'today_suspicious': today_logs.filter(is_suspicious=True).count(),
        'last_log_user': logs.first().ad_soyad if logs.first() else None,
        'last_log_time': logs.first().giris_zamani if logs.first() else None,
        'most_active_user': most_active['ad_soyad'] if most_active else None,
        'most_active_count': most_active['count'] if most_active else None,
    }

def _get_chart_data(logs):
    """Prepares data for the dashboard charts."""
    today = timezone.now().date()
    days = [today - timedelta(days=i) for i in range(29, -1, -1)]
    daily_counts = [logs.filter(giris_zamani__date=day).count() for day in days]

    now = timezone.now()
    last_24_hours = [now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i) for i in range(23, -1, -1)]
    hourly_qs = logs.filter(giris_zamani__gte=now - timedelta(hours=24))
    hour_map = {
        h['hour'].replace(tzinfo=None): h['count'] 
        for h in hourly_qs.annotate(hour=TruncHour('giris_zamani')).values('hour').annotate(count=Count('id'))
    }
    hourly_counts = [hour_map.get(h.replace(tzinfo=None), 0) for h in last_24_hours]
    
    top_users = logs.values('ad_soyad').annotate(count=Count('id')).order_by('-count')[:5]

    return {
        'days': [day.strftime('%d.%m') for day in days],
        'daily_counts': daily_counts,
        'hour_labels': [hour.strftime('%H:00') for hour in last_24_hours],
        'hourly_counts': hourly_counts,
        'top_users': top_users,
    }

@login_required
def company_dashboard(request, company_id=None, company_slug=None):
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
    else:
        return HttpResponseForbidden(_("Company not found."))
    
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden(_("You are not authorized to access this company's dashboard."))

    all_logs = LogKayit.objects.filter(company=company).select_related('company')
    logs_to_filter = get_filtered_logs(request, company, base_queryset=all_logs)

    valid_logs = logs_to_filter.filter(is_suspicious=False)
    suspicious_logs = logs_to_filter.filter(is_suspicious=True)

    paginator = Paginator(valid_logs.order_by('-giris_zamani'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    suspicious_paginator = Paginator(suspicious_logs.order_by('-giris_zamani'), 10)
    suspicious_page_obj = suspicious_paginator.get_page(request.GET.get('suspicious_page'))

    is_company_admin = CompanyUser.objects.filter(user=request.user, company=company, role='admin').exists() or request.user.is_superuser
    user_cu = CompanyUser.objects.filter(user=request.user, company=company).first()
    
    context = {
        'company': company,
        'logs': page_obj.object_list,
        'page_obj': page_obj,
        'suspicious_logs': suspicious_page_obj.object_list,
        'suspicious_page_obj': suspicious_page_obj,
        'filter_params': request.GET,
        'is_company_admin': is_company_admin,
        'user_last_login': request.user.last_login,
        'user_role': user_cu.get_role_display() if user_cu else (_("Superuser") if request.user.is_superuser else None),
        'theme_color': company.theme_color or "#0d6efd",
        'logo_url': company.logo.url if company.logo else None,
    }
    context.update(_get_dashboard_statistics(all_logs, company))
    context.update(_get_chart_data(all_logs.filter(is_suspicious=False)))

    return render(request, 'log_kayit/dashboard.html', context)

def get_filtered_logs(request, company, base_queryset=None):
    """Applies filters from the request to a queryset of logs."""
    logs = base_queryset if base_queryset is not None else LogKayit.objects.filter(company=company)
    
    filter_params = {
        'tc_no': request.GET.get('tc_no', '').strip(),
        'ad_soyad': request.GET.get('ad_soyad', '').strip(),
        'date_start': request.GET.get('date_start', '').strip(),
        'date_end': request.GET.get('date_end', '').strip(),
    }
    
    if filter_params['tc_no']:
        logs = logs.filter(tc_no__icontains=filter_params['tc_no'])
    if filter_params['ad_soyad']:
        logs = logs.filter(ad_soyad__icontains=filter_params['ad_soyad'])
    if filter_params['date_start']:
        logs = logs.filter(giris_zamani__date__gte=filter_params['date_start'])
    if filter_params['date_end']:
        logs = logs.filter(giris_zamani__date__lte=filter_params['date_end'])
        
    return logs

@login_required
@require_http_methods(["GET"])
def advanced_analytics(request, company_slug):
    """Gelişmiş analitik API endpoint'i"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden(_("You are not authorized to access this company's analytics."))
    
    days = int(request.GET.get('days', 30))
    
    # Analitik verileri
    overview = AnalyticsService.get_company_overview(company, days)
    anomalies = AnalyticsService.detect_anomalies(company, min(days, 7))
    user_patterns = AnalyticsService.get_user_behavior_patterns(company, days)
    compliance = AnalyticsService.generate_compliance_report(company)
    
    return JsonResponse({
        'overview': overview,
        'anomalies': anomalies,
        'user_patterns': user_patterns,
        'compliance': compliance,
        'generated_at': timezone.now().isoformat()
    }) 