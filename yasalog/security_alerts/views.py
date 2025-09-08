from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json

from log_kayit.models import Company
from .models import SecurityThreat, SecurityAlert, ThreatIntelligence, SecurityIncident, SecurityMetrics


@login_required
def security_dashboard(request, company_slug):
    """Güvenlik dashboard'u"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Son 30 günlük veriler
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Tehdit istatistikleri
    threats_stats = SecurityThreat.objects.filter(
        company=company,
        detection_time__gte=thirty_days_ago
    ).aggregate(
        total=Count('id'),
        critical=Count('id', filter=Q(severity='CRITICAL')),
        high=Count('id', filter=Q(severity='HIGH')),
        medium=Count('id', filter=Q(severity='MEDIUM')),
        low=Count('id', filter=Q(severity='LOW'))
    )
    
    # Uyarı istatistikleri
    alerts_stats = SecurityAlert.objects.filter(
        company=company,
        created_at__gte=thirty_days_ago
    ).aggregate(
        total=Count('id'),
        acknowledged=Count('id', filter=Q(is_acknowledged=True)),
        resolved=Count('id', filter=Q(is_resolved=True)),
        urgent=Count('id', filter=Q(priority__in=['URGENT', 'IMMEDIATE']))
    )
    
    # Olay istatistikleri
    incidents_stats = SecurityIncident.objects.filter(
        company=company,
        discovered_at__gte=thirty_days_ago
    ).aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status='OPEN')),
        investigating=Count('id', filter=Q(status='INVESTIGATING')),
        resolved=Count('id', filter=Q(status='RESOLVED'))
    )
    
    # Son tehditler
    recent_threats = SecurityThreat.objects.filter(
        company=company
    ).order_by('-detection_time')[:5]
    
    # Son uyarılar
    recent_alerts = SecurityAlert.objects.filter(
        company=company
    ).order_by('-created_at')[:5]
    
    # Son olaylar
    recent_incidents = SecurityIncident.objects.filter(
        company=company
    ).order_by('-discovered_at')[:5]
    
    # Tehdit türlerine göre dağılım
    threat_types = SecurityThreat.objects.filter(
        company=company,
        detection_time__gte=thirty_days_ago
    ).values('threat_type').annotate(count=Count('id')).order_by('-count')[:10]
    
    # Günlük tehdit sayısı (son 7 gün)
    daily_threats = []
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        count = SecurityThreat.objects.filter(
            company=company,
            detection_time__date=date.date()
        ).count()
        daily_threats.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    daily_threats.reverse()
    
    context = {
        'company': company,
        'threats_stats': threats_stats,
        'alerts_stats': alerts_stats,
        'incidents_stats': incidents_stats,
        'recent_threats': recent_threats,
        'recent_alerts': recent_alerts,
        'recent_incidents': recent_incidents,
        'threat_types': threat_types,
        'daily_threats': daily_threats,
    }
    
    return render(request, 'security_alerts/security_dashboard.html', context)


@login_required
def threats_list(request, company_slug):
    """Tehdit listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Filtreleme
    threat_type = request.GET.get('threat_type', '')
    severity = request.GET.get('severity', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    threats = SecurityThreat.objects.filter(company=company)
    
    if threat_type:
        threats = threats.filter(threat_type=threat_type)
    if severity:
        threats = threats.filter(severity=severity)
    if status:
        threats = threats.filter(status=status)
    if search:
        threats = threats.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(source_ip__icontains=search) |
            Q(destination_ip__icontains=search) |
            Q(tags__icontains=search)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-detection_time')
    threats = threats.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(threats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'threats': page_obj,
        'filters': {
            'threat_type': threat_type,
            'severity': severity,
            'status': status,
            'search': search,
            'sort': sort_by
        },
        'threat_types': SecurityThreat.THREAT_TYPES,
        'severity_levels': SecurityThreat.SEVERITY_LEVELS,
        'status_choices': SecurityThreat.STATUS_CHOICES,
    }
    
    return render(request, 'security_alerts/threats_list.html', context)


@login_required
def threat_detail(request, company_slug, threat_id):
    """Tehdit detay sayfası"""
    company = get_object_or_404(Company, slug=company_slug)
    threat = get_object_or_404(SecurityThreat, id=threat_id, company=company)
    
    # İlişkili uyarılar
    related_alerts = SecurityAlert.objects.filter(
        related_threat=threat
    ).order_by('-created_at')
    
    # İlişkili olaylar
    related_incidents = SecurityIncident.objects.filter(
        related_threats=threat
    ).order_by('-discovered_at')
    
    context = {
        'company': company,
        'threat': threat,
        'related_alerts': related_alerts,
        'related_incidents': related_incidents,
    }
    
    return render(request, 'security_alerts/threat_detail.html', context)


@login_required
def alerts_list(request, company_slug):
    """Uyarı listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Filtreleme
    alert_type = request.GET.get('alert_type', '')
    priority = request.GET.get('priority', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    alerts = SecurityAlert.objects.filter(company=company)
    
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)
    if priority:
        alerts = alerts.filter(priority=priority)
    if status == 'acknowledged':
        alerts = alerts.filter(is_acknowledged=True)
    elif status == 'resolved':
        alerts = alerts.filter(is_resolved=True)
    elif status == 'open':
        alerts = alerts.filter(is_acknowledged=False, is_resolved=False)
    
    if search:
        alerts = alerts.filter(
            Q(title__icontains=search) |
            Q(message__icontains=search) |
            Q(details__icontains=search)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-created_at')
    alerts = alerts.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(alerts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'alerts': page_obj,
        'filters': {
            'alert_type': alert_type,
            'priority': priority,
            'status': status,
            'search': search,
            'sort': sort_by
        },
        'alert_types': SecurityAlert.ALERT_TYPES,
        'priority_levels': SecurityAlert.PRIORITY_LEVELS,
    }
    
    return render(request, 'security_alerts/alerts_list.html', context)


@login_required
def incidents_list(request, company_slug):
    """Olay listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Filtreleme
    incident_type = request.GET.get('incident_type', '')
    status = request.GET.get('status', '')
    severity = request.GET.get('severity', '')
    search = request.GET.get('search', '')
    
    incidents = SecurityIncident.objects.filter(company=company)
    
    if incident_type:
        incidents = incidents.filter(incident_type=incident_type)
    if status:
        incidents = incidents.filter(status=status)
    if severity:
        incidents = incidents.filter(severity=severity)
    if search:
        incidents = incidents.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(notes__icontains=search)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-discovered_at')
    incidents = incidents.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(incidents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'incidents': page_obj,
        'filters': {
            'incident_type': incident_type,
            'status': status,
            'severity': severity,
            'search': search,
            'sort': sort_by
        },
        'incident_types': SecurityIncident.INCIDENT_TYPES,
        'status_choices': SecurityIncident.STATUS_CHOICES,
        'severity_levels': SecurityThreat.SEVERITY_LEVELS,
    }
    
    return render(request, 'security_alerts/incidents_list.html', context)


@login_required
def threat_intelligence(request, company_slug):
    """Tehdit istihbaratı sayfası"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Filtreleme
    intel_type = request.GET.get('intel_type', '')
    severity = request.GET.get('severity', '')
    search = request.GET.get('search', '')
    
    intelligence = ThreatIntelligence.objects.filter(company=company, is_active=True)
    
    if intel_type:
        intelligence = intelligence.filter(intel_type=intel_type)
    if severity:
        intelligence = intelligence.filter(severity=severity)
    if search:
        intelligence = intelligence.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(value__icontains=search) |
            Q(tags__icontains=search)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-last_seen')
    intelligence = intelligence.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(intelligence, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'intelligence': page_obj,
        'filters': {
            'intel_type': intel_type,
            'severity': severity,
            'search': search,
            'sort': sort_by
        },
        'intel_types': ThreatIntelligence.INTEL_TYPES,
        'severity_levels': SecurityThreat.SEVERITY_LEVELS,
    }
    
    return render(request, 'security_alerts/threat_intelligence.html', context)


@login_required
def api_security_stats(request, company_slug):
    """Güvenlik istatistikleri API endpoint'i"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Son 7 günlük veriler
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # Günlük tehdit sayısı
    daily_threats = []
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        count = SecurityThreat.objects.filter(
            company=company,
            detection_time__date=date.date()
        ).count()
        daily_threats.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    daily_threats.reverse()
    
    # Tehdit türlerine göre dağılım
    threat_types = SecurityThreat.objects.filter(
        company=company,
        detection_time__gte=seven_days_ago
    ).values('threat_type').annotate(count=Count('id')).order_by('-count')[:5]
    
    # Önem seviyelerine göre dağılım
    severity_distribution = SecurityThreat.objects.filter(
        company=company,
        detection_time__gte=seven_days_ago
    ).values('severity').annotate(count=Count('id'))
    
    # Uyarı durumları
    alert_statuses = SecurityAlert.objects.filter(
        company=company,
        created_at__gte=seven_days_ago
    ).aggregate(
        total=Count('id'),
        acknowledged=Count('id', filter=Q(is_acknowledged=True)),
        resolved=Count('id', filter=Q(is_resolved=True)),
        open=Count('id', filter=Q(is_acknowledged=False, is_resolved=False))
    )
    
    return JsonResponse({
        'daily_threats': daily_threats,
        'threat_types': list(threat_types),
        'severity_distribution': list(severity_distribution),
        'alert_statuses': alert_statuses,
    })


@login_required
def acknowledge_alert(request, alert_id):
    """Uyarıyı kabul et"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Sadece POST metodu kabul edilir'})
    
    try:
        alert = get_object_or_404(SecurityAlert, id=alert_id)
        
        # Yetki kontrolü
        if not (request.user.is_superuser or 
                hasattr(request.user, 'companyuser') and 
                request.user.companyuser.company == alert.company):
            return JsonResponse({'success': False, 'message': 'Yetkisiz erişim'})
        
        if alert.is_acknowledged:
            return JsonResponse({'success': False, 'message': 'Bu uyarı zaten kabul edilmiş'})
        
        alert.is_acknowledged = True
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.save()
        
        return JsonResponse({'success': True, 'message': 'Uyarı başarıyla kabul edildi'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})


@login_required
def resolve_alert(request, alert_id):
    """Uyarıyı çözüldü olarak işaretle"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Sadece POST metodu kabul edilir'})
    
    try:
        alert = get_object_or_404(SecurityAlert, id=alert_id)
        
        # Yetki kontrolü
        if not (request.user.is_superuser or 
                hasattr(request.user, 'companyuser') and 
                request.user.companyuser.company == alert.company):
            return JsonResponse({'success': False, 'message': 'Yetkisiz erişim'})
        
        if alert.is_resolved:
            return JsonResponse({'success': False, 'message': 'Bu uyarı zaten çözülmüş'})
        
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.save()
        
        return JsonResponse({'success': True, 'message': 'Uyarı başarıyla çözüldü olarak işaretlendi'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})


@login_required
def update_threat_status(request, threat_id):
    """Tehdit durumunu güncelle"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Sadece POST metodu kabul edilir'})
    
    try:
        threat = get_object_or_404(SecurityThreat, id=threat_id)
        
        # Yetki kontrolü
        if not (request.user.is_superuser or 
                hasattr(request.user, 'companyuser') and 
                request.user.companyuser.company == threat.company):
            return JsonResponse({'success': False, 'message': 'Yetkisiz erişim'})
        
        import json
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in [choice[0] for choice in SecurityThreat.STATUS_CHOICES]:
            return JsonResponse({'success': False, 'message': 'Geçersiz durum'})
        
        threat.status = new_status
        threat.last_updated = timezone.now()
        
        if new_status == 'RESOLVED':
            threat.resolved_time = timezone.now()
        
        threat.save()
        
        return JsonResponse({'success': True, 'message': 'Tehdit durumu başarıyla güncellendi'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})


@login_required
def assign_threat(request, threat_id):
    """Tehdit atama"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Sadece POST metodu kabul edilir'})
    
    try:
        threat = get_object_or_404(SecurityThreat, id=threat_id)
        
        # Yetki kontrolü
        if not (request.user.is_superuser or 
                hasattr(request.user, 'companyuser') and 
                request.user.companyuser.company == threat.company):
            return JsonResponse({'success': False, 'message': 'Yetkisiz erişim'})
        
        import json
        data = json.loads(request.body)
        username = data.get('username')
        
        if not username:
            return JsonResponse({'success': False, 'message': 'Kullanıcı adı gerekli'})
        
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(username=username)
            threat.assigned_to = user
            threat.save()
            
            return JsonResponse({'success': True, 'message': f'Tehdit {user.get_full_name() or user.username} kullanıcısına atandı'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Kullanıcı bulunamadı'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})


@login_required
def add_threat_note(request, threat_id):
    """Tehdit notu ekleme"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Sadece POST metodu kabul edilir'})
    
    try:
        threat = get_object_or_404(SecurityThreat, id=threat_id)
        
        # Yetki kontrolü
        if not (request.user.is_superuser or 
                hasattr(request.user, 'companyuser') and 
                request.user.companyuser.company == threat.company):
            return JsonResponse({'success': False, 'message': 'Yetkisiz erişim'})
        
        import json
        data = json.loads(request.body)
        note = data.get('note')
        
        if not note:
            return JsonResponse({'success': False, 'message': 'Not gerekli'})
        
        # Mevcut notlara yeni notu ekle
        current_notes = threat.notes or ''
        timestamp = timezone.now().strftime('%d.%m.%Y %H:%M')
        new_note = f"[{timestamp}] {request.user.username}: {note}\n"
        
        threat.notes = current_notes + new_note
        threat.save()
        
        return JsonResponse({'success': True, 'message': 'Not başarıyla eklendi'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})