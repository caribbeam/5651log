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
    """Rule ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            alarm_type = request.POST.get('rule_type')
            severity = request.POST.get('severity')
            condition = request.POST.get('condition', '')
            threshold_value = request.POST.get('threshold_value', '')
            time_window_minutes = int(request.POST.get('time_window_minutes', 5))
            notify_email = 'notification_enabled' in request.POST
            notify_sms = 'notify_sms' in request.POST
            notify_webhook = 'notify_webhook' in request.POST
            notify_dashboard = 'notify_dashboard' in request.POST
            email_recipients = request.POST.get('notification_recipients', '')
            sms_recipients = request.POST.get('sms_recipients', '')
            webhook_url = request.POST.get('webhook_url', '')
            repeat_notification = 'repeat_notification' in request.POST
            repeat_interval_minutes = int(request.POST.get('repeat_interval_minutes', 60))
            max_repeat_count = int(request.POST.get('max_repeat_count', 5))
            is_active = 'is_active' in request.POST
            is_enabled = 'is_enabled' in request.POST
            
            # Threshold value'yu float'a çevir
            if threshold_value:
                try:
                    threshold_value = float(threshold_value)
                except ValueError:
                    threshold_value = None
            else:
                threshold_value = None
            
            # Rule oluştur
            rule = AlarmRule.objects.create(
                company=company,
                name=name,
                description=description,
                alarm_type=alarm_type,
                severity=severity,
                condition=condition,
                threshold_value=threshold_value,
                time_window_minutes=time_window_minutes,
                notify_email=notify_email,
                notify_sms=notify_sms,
                notify_webhook=notify_webhook,
                notify_dashboard=notify_dashboard,
                email_recipients=email_recipients,
                sms_recipients=sms_recipients,
                webhook_url=webhook_url,
                repeat_notification=repeat_notification,
                repeat_interval_minutes=repeat_interval_minutes,
                max_repeat_count=max_repeat_count,
                is_active=is_active,
                is_enabled=is_enabled
            )
            
            messages.success(request, 'Alarm kuralı başarıyla oluşturuldu.')
            return redirect('alarm_integration:rule_detail', company.slug, rule.id)
            
        except Exception as e:
            messages.error(request, f'Kural oluşturma hatası: {str(e)}')
    
    context = {
        'company': company,
    }
    
    return render(request, 'alarm_integration/rule_add.html', context)


@login_required
def rule_edit(request, company_slug, rule_id):
    """Rule düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    rule = get_object_or_404(AlarmRule, id=rule_id, company=company)
    
    if request.method == 'POST':
        try:
            # Form verilerini al ve güncelle
            rule.name = request.POST.get('name', rule.name)
            rule.description = request.POST.get('description', rule.description)
            rule.alarm_type = request.POST.get('rule_type', rule.alarm_type)
            rule.severity = request.POST.get('severity', rule.severity)
            rule.condition = request.POST.get('condition', rule.condition)
            
            threshold_value = request.POST.get('threshold_value', '')
            if threshold_value:
                try:
                    rule.threshold_value = float(threshold_value)
                except ValueError:
                    rule.threshold_value = None
            else:
                rule.threshold_value = None
                
            rule.time_window_minutes = int(request.POST.get('time_window_minutes', rule.time_window_minutes))
            rule.notify_email = 'notification_enabled' in request.POST
            rule.notify_sms = 'notify_sms' in request.POST
            rule.notify_webhook = 'notify_webhook' in request.POST
            rule.notify_dashboard = 'notify_dashboard' in request.POST
            rule.email_recipients = request.POST.get('notification_recipients', rule.email_recipients)
            rule.sms_recipients = request.POST.get('sms_recipients', rule.sms_recipients)
            rule.webhook_url = request.POST.get('webhook_url', rule.webhook_url)
            rule.repeat_notification = 'repeat_notification' in request.POST
            rule.repeat_interval_minutes = int(request.POST.get('repeat_interval_minutes', rule.repeat_interval_minutes))
            rule.max_repeat_count = int(request.POST.get('max_repeat_count', rule.max_repeat_count))
            rule.is_active = 'is_active' in request.POST
            rule.is_enabled = 'is_enabled' in request.POST
            
            rule.save()
            messages.success(request, 'Alarm kuralı başarıyla güncellendi.')
            return redirect('alarm_integration:rule_detail', company.slug, rule.id)
            
        except Exception as e:
            messages.error(request, f'Kural güncelleme hatası: {str(e)}')
    
    context = {
        'company': company,
        'rule': rule,
    }
    
    return render(request, 'alarm_integration/rule_edit.html', context)


@login_required
def rule_delete(request, company_slug, rule_id):
    """Rule silme"""
    company = get_object_or_404(Company, slug=company_slug)
    rule = get_object_or_404(AlarmRule, id=rule_id, company=company)
    
    if request.method == 'POST':
        try:
            rule_name = rule.name
            rule.delete()
            messages.success(request, f'Alarm kuralı "{rule_name}" başarıyla silindi.')
            return redirect('alarm_integration:rules_list', company.slug)
        except Exception as e:
            messages.error(request, f'Kural silme hatası: {str(e)}')
    
    context = {
        'company': company,
        'rule': rule,
    }
    
    return render(request, 'alarm_integration/rule_delete.html', context)


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
