from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from log_kayit.models import Company, CompanyUser
from .models import LogFlowMonitor, LogFlowAlert, LogFlowStatistics


@login_required
def dashboard(request, company_slug):
    """Log akış izleme dashboard"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # İstatistikler
    monitors = LogFlowMonitor.objects.filter(company=company)
    active_monitors = monitors.filter(is_active=True)
    alerts = LogFlowAlert.objects.filter(monitor__company=company, is_resolved=False)
    
    context = {
        'company': company,
        'monitors': monitors,
        'active_monitors': active_monitors,
        'alerts': alerts,
    }
    
    return render(request, 'log_flow_monitoring/dashboard.html', context)


@login_required
def monitors_list(request, company_slug):
    """Monitor listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    monitors = LogFlowMonitor.objects.filter(company=company)
    
    context = {
        'company': company,
        'monitors': monitors,
    }
    
    return render(request, 'log_flow_monitoring/monitors_list.html', context)


@login_required
def monitor_detail(request, company_slug, monitor_id):
    """Monitor detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    monitor = get_object_or_404(LogFlowMonitor, id=monitor_id, company=company)
    
    context = {
        'company': company,
        'monitor': monitor,
    }
    
    return render(request, 'log_flow_monitoring/monitor_detail.html', context)


@login_required
def alerts_list(request, company_slug):
    """Alert listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    alerts = LogFlowAlert.objects.filter(monitor__company=company)
    
    context = {
        'company': company,
        'alerts': alerts,
    }
    
    return render(request, 'log_flow_monitoring/alerts_list.html', context)


@login_required
def statistics(request, company_slug):
    """İstatistikler"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    statistics = LogFlowStatistics.objects.filter(company=company)
    
    context = {
        'company': company,
        'statistics': statistics,
    }
    
    return render(request, 'log_flow_monitoring/statistics.html', context)


# API Views
@login_required
def api_heartbeat(request, company_slug, monitor_id):
    """Heartbeat API"""
    company = get_object_or_404(Company, slug=company_slug)
    monitor = get_object_or_404(LogFlowMonitor, id=monitor_id, company=company)
    
    monitor.update_heartbeat()
    
    return JsonResponse({'status': 'success', 'message': 'Heartbeat updated'})


@login_required
def api_log_received(request, company_slug, monitor_id):
    """Log received API"""
    company = get_object_or_404(Company, slug=company_slug)
    monitor = get_object_or_404(LogFlowMonitor, id=monitor_id, company=company)
    
    log_size = request.GET.get('size', 0)
    monitor.update_log_received(int(log_size))
    
    return JsonResponse({'status': 'success', 'message': 'Log received'})


@login_required
def api_status(request, company_slug):
    """Status API"""
    company = get_object_or_404(Company, slug=company_slug)
    
    monitors = LogFlowMonitor.objects.filter(company=company)
    status_data = []
    
    for monitor in monitors:
        status_data.append({
            'id': monitor.id,
            'name': monitor.name,
            'status': monitor.status,
            'is_receiving_logs': monitor.is_receiving_logs,
            'last_log_received': monitor.last_log_received.isoformat() if monitor.last_log_received else None,
        })
    
    return JsonResponse({'status': 'success', 'data': status_data})


# Eksik view'lar
@login_required
def monitor_add(request, company_slug):
    """Monitor ekleme - şimdilik admin'e yönlendir"""
    return redirect('/admin/log_flow_monitoring/logflowmonitor/add/')


@login_required
def monitor_edit(request, company_slug, monitor_id):
    """Monitor düzenleme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/log_flow_monitoring/logflowmonitor/{monitor_id}/change/')


@login_required
def monitor_delete(request, company_slug, monitor_id):
    """Monitor silme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/log_flow_monitoring/logflowmonitor/{monitor_id}/delete/')


@login_required
def alert_detail(request, company_slug, alert_id):
    """Alert detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    alert = get_object_or_404(LogFlowAlert, id=alert_id, monitor__company=company)
    
    context = {
        'company': company,
        'alert': alert,
    }
    
    return render(request, 'log_flow_monitoring/alert_detail.html', context)


@login_required
def alert_acknowledge(request, company_slug, alert_id):
    """Alert kabul et"""
    company = get_object_or_404(Company, slug=company_slug)
    alert = get_object_or_404(LogFlowAlert, id=alert_id, monitor__company=company)
    
    alert.acknowledge()
    messages.success(request, 'Uyarı kabul edildi.')
    
    return redirect('log_flow_monitoring:alerts_list', company.slug)


@login_required
def alert_resolve(request, company_slug, alert_id):
    """Alert çöz"""
    company = get_object_or_404(Company, slug=company_slug)
    alert = get_object_or_404(LogFlowAlert, id=alert_id, monitor__company=company)
    
    alert.resolve()
    messages.success(request, 'Uyarı çözüldü.')
    
    return redirect('log_flow_monitoring:alerts_list', company.slug)
