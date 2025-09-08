"""
Syslog Server Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from datetime import datetime, timedelta
from log_kayit.models import Company, CompanyUser
from .models import SyslogServer, SyslogClient, SyslogMessage, SyslogFilter, SyslogAlert, SyslogStatistics


@login_required
def syslog_dashboard(request, company_slug):
    """Syslog dashboard'u"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/dashboard.html', context)


@login_required
def servers_list(request, company_slug):
    """Syslog sunucuları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut sunucuları al
    servers = SyslogServer.objects.filter(company=company).order_by('-created_at')
    
    context = {
        'company': company,
        'servers': servers,
    }
    
    return render(request, 'syslog_server/servers_list.html', context)


@login_required
def server_add(request, company_slug):
    """Yeni syslog sunucusu ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        host = request.POST.get('host')
        port = int(request.POST.get('port', 514))
        protocol = request.POST.get('protocol', 'UDP')
        use_tls = request.POST.get('use_tls') == 'on'
        certificate_path = request.POST.get('certificate_path', '')
        private_key_path = request.POST.get('private_key_path', '')
        allowed_facilities = request.POST.get('allowed_facilities', '')
        allowed_priorities = request.POST.get('allowed_priorities', '')
        max_connections = int(request.POST.get('max_connections', 100))
        buffer_size = int(request.POST.get('buffer_size', 1024))
        batch_size = int(request.POST.get('batch_size', 100))
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            # Yeni sunucu oluştur
            server = SyslogServer.objects.create(
                company=company,
                name=name,
                host=host,
                port=port,
                protocol=protocol,
                use_tls=use_tls,
                certificate_path=certificate_path,
                private_key_path=private_key_path,
                allowed_facilities=allowed_facilities,
                allowed_priorities=allowed_priorities,
                max_connections=max_connections,
                buffer_size=buffer_size,
                batch_size=batch_size,
                is_active=is_active
            )
            
            messages.success(request, f"Syslog sunucusu '{name}' başarıyla oluşturuldu.")
            return redirect('syslog_server:server_detail', company_slug=company.slug, server_id=server.id)
            
        except Exception as e:
            messages.error(request, f"Syslog sunucusu oluşturulamadı: {str(e)}")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/server_add.html', context)


@login_required
def server_detail(request, company_slug, server_id):
    """Syslog sunucu detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/server_detail.html', context)


@login_required
def clients_list(request, company_slug):
    """Syslog istemcileri listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut istemcileri al
    clients = SyslogClient.objects.filter(company=company).order_by('-created_at')
    
    context = {
        'company': company,
        'clients': clients,
    }
    
    return render(request, 'syslog_server/clients_list.html', context)


@login_required
def client_add(request, company_slug):
    """Yeni syslog istemcisi ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut sunucuları al
    servers = SyslogServer.objects.filter(company=company, is_active=True)
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        client_type = request.POST.get('client_type')
        ip_address = request.POST.get('ip_address')
        mac_address = request.POST.get('mac_address', '')
        hostname = request.POST.get('hostname', '')
        syslog_server_id = request.POST.get('syslog_server', '')
        facility = request.POST.get('facility', 'local0')
        priority = request.POST.get('priority', 'info')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            # Syslog server seçimi
            syslog_server = None
            if syslog_server_id and syslog_server_id != '':
                syslog_server = SyslogServer.objects.get(id=syslog_server_id)
            
            # Yeni istemci oluştur
            client = SyslogClient.objects.create(
                company=company,
                name=name,
                client_type=client_type,
                ip_address=ip_address,
                mac_address=mac_address,
                hostname=hostname,
                syslog_server=syslog_server,
                facility=facility,
                priority=priority,
                is_active=is_active
            )
            
            messages.success(request, f"Syslog istemcisi '{name}' başarıyla oluşturuldu.")
            return redirect('syslog_server:client_detail', company_slug=company.slug, client_id=client.id)
            
        except Exception as e:
            messages.error(request, f"Syslog istemcisi oluşturulamadı: {str(e)}")
    
    context = {
        'company': company,
        'servers': servers,
    }
    
    return render(request, 'syslog_server/client_add.html', context)


@login_required
def client_detail(request, company_slug, client_id):
    """Syslog istemci detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/client_detail.html', context)


@login_required
def messages_list(request, company_slug):
    """Syslog mesajları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Son 24 saatlik mesajları al
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=24)
    
    # Önce tüm mesajları al, sonra slice yap
    all_messages = SyslogMessage.objects.filter(
        company=company, 
        timestamp__gte=start_time
    ).order_by('-timestamp')
    
    messages = all_messages[:100]  # Son 100 mesaj
    
    # İstatistikler - slice yapmadan önce hesapla
    stats = {
        'total_messages': SyslogMessage.objects.filter(company=company).count(),
        'last_24h': all_messages.count(),
        'suspicious': all_messages.filter(is_suspicious=True).count(),
        'by_facility': all_messages.values('facility').annotate(count=Count('id')).order_by('-count')[:5],
        'by_priority': all_messages.values('priority').annotate(count=Count('id')).order_by('-count')[:5],
    }
    
    context = {
        'company': company,
        'messages': messages,
        'stats': stats,
    }
    
    return render(request, 'syslog_server/messages_list.html', context)


@login_required
def message_detail(request, company_slug, message_id):
    """Syslog mesaj detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/message_detail.html', context)


@login_required
def filters_list(request, company_slug):
    """Syslog filtreleri listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut filtreleri al
    filters = SyslogFilter.objects.filter(company=company).order_by('-created_at')
    
    context = {
        'company': company,
        'filters': filters,
    }
    
    return render(request, 'syslog_server/filters_list.html', context)


@login_required
def filter_add(request, company_slug):
    """Yeni syslog filtresi ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        filter_type = request.POST.get('filter_type')
        filter_value = request.POST.get('filter_value')
        description = request.POST.get('description', '')
        action = request.POST.get('action', 'ACCEPT')
        priority = int(request.POST.get('priority', 1))
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            # Yeni filtre oluştur
            filter_obj = SyslogFilter.objects.create(
                company=company,
                name=name,
                filter_type=filter_type,
                filter_value=filter_value,
                description=description,
                action=action,
                priority=priority,
                is_active=is_active
            )
            
            messages.success(request, f"Syslog filtresi '{name}' başarıyla oluşturuldu.")
            return redirect('syslog_server:filter_detail', company_slug=company.slug, filter_id=filter_obj.id)
            
        except Exception as e:
            messages.error(request, f"Syslog filtresi oluşturulamadı: {str(e)}")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/filter_add.html', context)


@login_required
def filter_detail(request, company_slug, filter_id):
    """Syslog filtre detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/filter_detail.html', context)


@login_required
def alerts_list(request, company_slug):
    """Syslog uyarıları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut uyarıları al
    alerts = SyslogAlert.objects.filter(company=company).order_by('-created_at')
    
    context = {
        'company': company,
        'alerts': alerts,
    }
    
    return render(request, 'syslog_server/alerts_list.html', context)


@login_required
def alert_add(request, company_slug):
    """Yeni syslog uyarısı ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        alert_type = request.POST.get('alert_type')
        condition = request.POST.get('condition')
        threshold_value = int(request.POST.get('threshold_value', 0))
        time_window = int(request.POST.get('time_window', 300))
        notify_email = request.POST.get('notify_email') == 'on'
        notify_sms = request.POST.get('notify_sms') == 'on'
        notification_recipients = request.POST.get('notification_recipients', '')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            # Yeni uyarı oluştur
            alert = SyslogAlert.objects.create(
                company=company,
                name=name,
                alert_type=alert_type,
                condition=condition,
                threshold_value=threshold_value,
                time_window=time_window,
                notify_email=notify_email,
                notify_sms=notify_sms,
                notification_recipients=notification_recipients,
                is_active=is_active
            )
            
            messages.success(request, f"Syslog uyarısı '{name}' başarıyla oluşturuldu.")
            return redirect('syslog_server:alert_detail', company_slug=company.slug, alert_id=alert.id)
            
        except Exception as e:
            messages.error(request, f"Syslog uyarısı oluşturulamadı: {str(e)}")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/alert_add.html', context)


@login_required
def alert_detail(request, company_slug, alert_id):
    """Syslog uyarı detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/alert_detail.html', context)


@login_required
def statistics(request, company_slug):
    """Syslog istatistikleri"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    context = {
        'company': company,
    }
    
    return render(request, 'syslog_server/statistics.html', context)


@login_required
def api_syslog_stats(request, company_slug):
    """Syslog istatistikleri API"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    return JsonResponse({
        'total_servers': 0,
        'active_servers': 0,
        'total_clients': 0,
        'total_messages': 0
    })


@login_required
def api_messages(request, company_slug):
    """Syslog mesajları API"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    return JsonResponse({
        'messages': [],
        'total_count': 0
    })
