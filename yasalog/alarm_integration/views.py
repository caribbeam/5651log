from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from log_kayit.models import Company, CompanyUser
from .models import AlarmRule, AlarmEvent, AlarmNotification, AlarmSuppression, AlarmStatistics


@login_required
def dashboard(request, company_slug):
    """Alarm entegrasyonu dashboard"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # İstatistikler
    rules = AlarmRule.objects.filter(company=company)
    active_rules = rules.filter(is_active=True)
    events = AlarmEvent.objects.filter(company=company)
    active_events = events.filter(status='ACTIVE')
    
    context = {
        'company': company,
        'rules': rules,
        'active_rules': active_rules,
        'events': events,
        'active_events': active_events,
    }
    
    return render(request, 'alarm_integration/dashboard.html', context)


@login_required
def rules_list(request, company_slug):
    """Rules listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    rules = AlarmRule.objects.filter(company=company)
    
    context = {
        'company': company,
        'rules': rules,
    }
    
    return render(request, 'alarm_integration/rules_list.html', context)


@login_required
def rule_detail(request, company_slug, rule_id):
    """Rule detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    rule = get_object_or_404(AlarmRule, id=rule_id, company=company)
    events = AlarmEvent.objects.filter(rule=rule)
    
    context = {
        'company': company,
        'rule': rule,
        'events': events,
    }
    
    return render(request, 'alarm_integration/rule_detail.html', context)


@login_required
def events_list(request, company_slug):
    """Events listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    events = AlarmEvent.objects.filter(company=company)
    
    context = {
        'company': company,
        'events': events,
    }
    
    return render(request, 'alarm_integration/events_list.html', context)


@login_required
def event_detail(request, company_slug, event_id):
    """Event detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    event = get_object_or_404(AlarmEvent, id=event_id, company=company)
    notifications = AlarmNotification.objects.filter(event=event)
    
    context = {
        'company': company,
        'event': event,
        'notifications': notifications,
    }
    
    return render(request, 'alarm_integration/event_detail.html', context)


@login_required
def notifications_list(request, company_slug):
    """Notifications listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    notifications = AlarmNotification.objects.filter(event__company=company)
    
    context = {
        'company': company,
        'notifications': notifications,
    }
    
    return render(request, 'alarm_integration/notifications_list.html', context)


@login_required
def suppressions_list(request, company_slug):
    """Suppressions listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    suppressions = AlarmSuppression.objects.filter(company=company)
    
    context = {
        'company': company,
        'suppressions': suppressions,
    }
    
    return render(request, 'alarm_integration/suppressions_list.html', context)


@login_required
def statistics(request, company_slug):
    """İstatistikler"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    statistics = AlarmStatistics.objects.filter(company=company)
    
    context = {
        'company': company,
        'statistics': statistics,
    }
    
    return render(request, 'alarm_integration/statistics.html', context)


# API Views
@login_required
def api_trigger_alarm(request, company_slug, rule_id):
    """Trigger alarm API"""
    company = get_object_or_404(Company, slug=company_slug)
    rule = get_object_or_404(AlarmRule, id=rule_id, company=company)
    
    details = request.GET.dict()
    rule.trigger_alarm(details)
    
    return JsonResponse({'status': 'success', 'message': 'Alarm triggered'})


@login_required
def api_alarm_status(request, company_slug):
    """Alarm status API"""
    company = get_object_or_404(Company, slug=company_slug)
    
    events = AlarmEvent.objects.filter(company=company, status='ACTIVE')
    status_data = []
    
    for event in events:
        status_data.append({
            'id': event.id,
            'title': event.title,
            'severity': event.severity,
            'triggered_at': event.triggered_at.isoformat(),
        })
    
    return JsonResponse({'status': 'success', 'data': status_data})


@login_required
def api_send_notifications(request, company_slug, event_id):
    """Send notifications API"""
    company = get_object_or_404(Company, slug=company_slug)
    event = get_object_or_404(AlarmEvent, id=event_id, company=company)
    
    # Bildirim gönderme işlemi burada yapılacak
    
    return JsonResponse({'status': 'success', 'message': 'Notifications sent'})


# Eksik view'lar
@login_required
def rule_add(request, company_slug):
    """Rule ekleme - şimdilik admin'e yönlendir"""
    return redirect('/admin/alarm_integration/alarmrule/add/')


@login_required
def rule_edit(request, company_slug, rule_id):
    """Rule düzenleme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/alarm_integration/alarmrule/{rule_id}/change/')


@login_required
def rule_delete(request, company_slug, rule_id):
    """Rule silme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/alarm_integration/alarmrule/{rule_id}/delete/')


@login_required
def rule_test(request, company_slug, rule_id):
    """Rule test et"""
    company = get_object_or_404(Company, slug=company_slug)
    rule = get_object_or_404(AlarmRule, id=rule_id, company=company)
    
    # Test alarmı tetikle
    rule.trigger_alarm({'test': True})
    messages.success(request, 'Test alarmı tetiklendi.')
    
    return redirect('alarm_integration:rule_detail', company.slug, rule.id)


@login_required
def event_acknowledge(request, company_slug, event_id):
    """Event kabul et"""
    company = get_object_or_404(Company, slug=company_slug)
    event = get_object_or_404(AlarmEvent, id=event_id, company=company)
    
    event.acknowledge(request.user)
    messages.success(request, 'Alarm kabul edildi.')
    
    return redirect('alarm_integration:event_detail', company.slug, event.id)


@login_required
def event_resolve(request, company_slug, event_id):
    """Event çöz"""
    company = get_object_or_404(Company, slug=company_slug)
    event = get_object_or_404(AlarmEvent, id=event_id, company=company)
    
    event.resolve(request.user, 'Manuel olarak çözüldü')
    messages.success(request, 'Alarm çözüldü.')
    
    return redirect('alarm_integration:event_detail', company.slug, event.id)


@login_required
def notification_detail(request, company_slug, notification_id):
    """Notification detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    notification = get_object_or_404(AlarmNotification, id=notification_id, event__company=company)
    
    context = {
        'company': company,
        'notification': notification,
    }
    
    return render(request, 'alarm_integration/notification_detail.html', context)


@login_required
def notification_resend(request, company_slug, notification_id):
    """Notification tekrar gönder"""
    company = get_object_or_404(Company, slug=company_slug)
    notification = get_object_or_404(AlarmNotification, id=notification_id, event__company=company)
    
    # Tekrar gönderme işlemi burada yapılacak
    messages.success(request, 'Bildirim tekrar gönderildi.')
    
    return redirect('alarm_integration:notification_detail', company.slug, notification.id)


@login_required
def suppression_add(request, company_slug):
    """Suppression ekleme - şimdilik admin'e yönlendir"""
    return redirect('/admin/alarm_integration/alarmsuppression/add/')


@login_required
def suppression_edit(request, company_slug, suppression_id):
    """Suppression düzenleme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/alarm_integration/alarmsuppression/{suppression_id}/change/')


@login_required
def suppression_delete(request, company_slug, suppression_id):
    """Suppression silme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/alarm_integration/alarmsuppression/{suppression_id}/delete/')
