from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Max, Min
from django.db.models.functions import TruncHour
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import json

from .models import FirewallRule, FirewallPolicy, FirewallEvent, FirewallLog
from log_kayit.models import Company, CompanyUser

@login_required
def firewall_dashboard(request, company_id=None, company_slug=None):
    """Firewall management ana dashboard"""
    
    # Şirket kontrolü
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
    else:
        return HttpResponseForbidden("Company not found.")
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Firewall istatistikleri
    rules = FirewallRule.objects.filter(company=company)
    policies = FirewallPolicy.objects.filter(company=company)
    events = FirewallEvent.objects.filter(company=company)
    logs = FirewallLog.objects.filter(company=company)
    
    # Kural istatistikleri
    rule_stats = {
        'total': rules.count(),
        'active': rules.filter(is_active=True).count(),
        'allow': rules.filter(rule_type='ALLOW').count(),
        'deny': rules.filter(rule_type='DENY').count(),
        'drop': rules.filter(rule_type='DROP').count(),
        'reject': rules.filter(rule_type='REJECT').count(),
    }
    
    # Politika istatistikleri
    policy_stats = {
        'total': policies.count(),
        'active': policies.filter(is_active=True).count(),
        'security': policies.filter(policy_type='SECURITY').count(),
        'compliance': policies.filter(policy_type='COMPLIANCE').count(),
        'performance': policies.filter(policy_type='PERFORMANCE').count(),
        'monitoring': policies.filter(policy_type='MONITORING').count(),
    }
    
    # Olay istatistikleri
    event_stats = {
        'total': events.count(),
        'resolved': events.filter(is_resolved=True).count(),
        'unresolved': events.filter(is_resolved=False).count(),
        'critical': events.filter(severity='CRITICAL').count(),
        'high': events.filter(severity='HIGH').count(),
        'medium': events.filter(severity='MEDIUM').count(),
        'low': events.filter(severity='LOW').count(),
    }
    
    # Trafik istatistikleri (son 24 saat)
    last_24h = timezone.now() - timedelta(hours=24)
    recent_logs = logs.filter(timestamp__gte=last_24h)
    
    traffic_stats = {
        'total_bytes': recent_logs.aggregate(
            total=Sum('bytes_sent') + Sum('bytes_received')
        )['total'] or 0,
        'total_packets': recent_logs.aggregate(
            total=Sum('packets_sent') + Sum('packets_received')
        )['total'] or 0,
        'blocked_connections': recent_logs.filter(action__in=['DENY', 'DROP', 'REJECT']).count(),
        'allowed_connections': recent_logs.filter(action='ALLOW').count(),
    }
    
    # 24 saatlik olay grafiği
    hourly_events = []
    for hour in range(24):
        hour_start = last_24h + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)
        
        hour_events = events.filter(timestamp__range=[hour_start, hour_end])
        
        hourly_events.append({
            'hour': hour_start.strftime('%H:00'),
            'total_events': hour_events.count(),
            'critical_events': hour_events.filter(severity='CRITICAL').count(),
            'blocked_connections': recent_logs.filter(
                timestamp__range=[hour_start, hour_end],
                action__in=['DENY', 'DROP', 'REJECT']
            ).count(),
        })
    
    # Son olaylar ve loglar
    recent_events = events.order_by('-timestamp')[:10]
    recent_logs_list = logs.order_by('-timestamp')[:20]
    
    # En çok eşleşen kurallar
    top_rules = rules.order_by('-hit_count')[:5]
    
    context = {
        'company': company,
        'rule_stats': rule_stats,
        'policy_stats': policy_stats,
        'event_stats': event_stats,
        'traffic_stats': traffic_stats,
        'hourly_events': hourly_events,
        'recent_events': recent_events,
        'recent_logs': recent_logs_list,
        'top_rules': top_rules,
    }
    
    return render(request, 'firewall_management/firewall_dashboard.html', context)

@login_required
def rules_list(request, company_slug):
    """Firewall kuralları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    rules = FirewallRule.objects.filter(company=company)
    
    # Filtreleme
    rule_type = request.GET.get('rule_type')
    protocol = request.GET.get('protocol')
    is_active = request.GET.get('is_active')
    
    if rule_type:
        rules = rules.filter(rule_type=rule_type)
    if protocol:
        rules = rules.filter(protocol=protocol)
    if is_active is not None:
        rules = rules.filter(is_active=is_active == 'true')
    
    # Sıralama
    sort_by = request.GET.get('sort', '-priority')
    rules = rules.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(rules, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'filters': {
            'rule_type': rule_type,
            'protocol': protocol,
            'is_active': is_active,
        }
    }
    
    return render(request, 'firewall_management/rules_list.html', context)

@login_required
def rule_detail(request, rule_id):
    """Firewall kural detayı"""
    rule = get_object_or_404(FirewallRule, id=rule_id)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=rule.company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Kural ile ilgili loglar
    related_logs = FirewallLog.objects.filter(rule=rule).order_by('-timestamp')[:50]
    
    # Kural ile ilgili olaylar
    related_events = FirewallEvent.objects.filter(rule=rule).order_by('-timestamp')[:20]
    
    context = {
        'rule': rule,
        'related_logs': related_logs,
        'related_events': related_events,
    }
    
    return render(request, 'firewall_management/rule_detail.html', context)

@login_required
def events_list(request, company_slug):
    """Firewall olayları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    events = FirewallEvent.objects.filter(company=company)
    
    # Filtreleme
    event_type = request.GET.get('event_type')
    severity = request.GET.get('severity')
    is_resolved = request.GET.get('is_resolved')
    
    if event_type:
        events = events.filter(event_type=event_type)
    if severity:
        events = events.filter(severity=severity)
    if is_resolved is not None:
        events = events.filter(is_resolved=is_resolved == 'true')
    
    # Sıralama
    events = events.order_by('-timestamp')
    
    # Sayfalama
    paginator = Paginator(events, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'filters': {
            'event_type': event_type,
            'severity': severity,
            'is_resolved': is_resolved,
        }
    }
    
    return render(request, 'firewall_management/events_list.html', context)

@login_required
def logs_list(request, company_slug):
    """Firewall logları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    logs = FirewallLog.objects.filter(company=company)
    
    # Filtreleme
    protocol = request.GET.get('protocol')
    action = request.GET.get('action')
    source_ip = request.GET.get('source_ip')
    destination_ip = request.GET.get('destination_ip')
    
    if protocol:
        logs = logs.filter(protocol=protocol)
    if action:
        logs = logs.filter(action=action)
    if source_ip:
        logs = logs.filter(source_ip__icontains=source_ip)
    if destination_ip:
        logs = logs.filter(destination_ip__icontains=destination_ip)
    
    # Sıralama
    logs = logs.order_by('-timestamp')
    
    # Sayfalama
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'filters': {
            'protocol': protocol,
            'action': action,
            'source_ip': source_ip,
            'destination_ip': destination_ip,
        }
    }
    
    return render(request, 'firewall_management/logs_list.html', context)

@login_required
def api_rule_stats(request, company_slug):
    """Kural istatistikleri API endpoint'i"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    rules = FirewallRule.objects.filter(company=company)
    
    stats = {
        'total_rules': rules.count(),
        'active_rules': rules.filter(is_active=True).count(),
        'rule_types': {
            'allow': rules.filter(rule_type='ALLOW').count(),
            'deny': rules.filter(rule_type='DENY').count(),
            'drop': rules.filter(rule_type='DROP').count(),
            'reject': rules.filter(rule_type='REJECT').count(),
        },
        'protocols': {
            'tcp': rules.filter(protocol='TCP').count(),
            'udp': rules.filter(protocol='UDP').count(),
            'icmp': rules.filter(protocol='ICMP').count(),
            'any': rules.filter(protocol='ANY').count(),
        }
    }
    
    return JsonResponse(stats)

# FRONTEND ARAYÜZÜ İÇİN YENİ VIEW'LAR
@login_required
def rule_add(request, company_slug):
    """Firewall kuralı ekleme - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        description = request.POST.get('description')
        rule_type = request.POST.get('rule_type')
        protocol = request.POST.get('protocol')
        source_ip = request.POST.get('source_ip')
        destination_ip = request.POST.get('destination_ip')
        source_port = request.POST.get('source_port')
        destination_port = request.POST.get('destination_port')
        priority = request.POST.get('priority', 100)
        is_active = request.POST.get('is_active') == 'on'
        
        # Kural oluştur
        rule = FirewallRule.objects.create(
            company=company,
            name=name,
            description=description,
            rule_type=rule_type,
            protocol=protocol,
            source_ip=source_ip,
            destination_ip=destination_ip,
            source_port=source_port,
            destination_port=destination_port,
            priority=int(priority),
            is_active=is_active,
        )
        
        messages.success(request, f'Firewall kuralı "{name}" başarıyla eklendi.')
        return redirect('firewall_management:rules_list', company_slug=company.slug)
    
    context = {
        'company': company,
        'rule_types': FirewallRule.RULE_TYPES,
        'protocols': FirewallRule.PROTOCOLS,
    }
    
    return render(request, 'firewall_management/rule_add.html', context)

@login_required
def rule_edit(request, company_slug, rule_id):
    """Firewall kuralı düzenleme - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    rule = get_object_or_404(FirewallRule, id=rule_id, company=company)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini güncelle
        rule.name = request.POST.get('name')
        rule.description = request.POST.get('description')
        rule.rule_type = request.POST.get('rule_type')
        rule.protocol = request.POST.get('protocol')
        rule.source_ip = request.POST.get('source_ip')
        rule.destination_ip = request.POST.get('destination_ip')
        rule.source_port = request.POST.get('source_port')
        rule.destination_port = request.POST.get('destination_port')
        rule.priority = int(request.POST.get('priority', 100))
        rule.is_active = request.POST.get('is_active') == 'on'
        
        rule.save()
        
        messages.success(request, f'Firewall kuralı "{rule.name}" başarıyla güncellendi.')
        return redirect('firewall_management:rules_list', company_slug=company.slug)
    
    context = {
        'company': company,
        'rule': rule,
        'rule_types': FirewallRule.RULE_TYPES,
        'protocols': FirewallRule.PROTOCOLS,
    }
    
    return render(request, 'firewall_management/rule_edit.html', context)

@login_required
@require_http_methods(["POST"])
def rule_delete(request, company_slug, rule_id):
    """Firewall kuralı silme - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    rule = get_object_or_404(FirewallRule, id=rule_id, company=company)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    rule_name = rule.name
    rule.delete()
    
    messages.success(request, f'Firewall kuralı "{rule_name}" başarıyla silindi.')
    return redirect('firewall_management:rules_list', company_slug=company.slug)
