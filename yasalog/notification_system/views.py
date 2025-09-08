"""
Gelişmiş Bildirim Sistemi View'ları
5651 Loglama için kapsamlı bildirim sistemi
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from datetime import datetime, timedelta
import json

from .models import (
    NotificationChannel, NotificationTemplate, NotificationRule, 
    NotificationLog, NotificationSubscription
)
from .services import NotificationService, NotificationRuleEngine, NotificationManager
from log_kayit.models import Company, LogKayit
from log_kayit.decorators import company_required


@company_required
def dashboard(request, company_slug):
    """Bildirim sistemi dashboard"""
    company = request.company
    
    # İstatistikler
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    stats = {
        'total_channels': NotificationChannel.objects.filter(company=company).count(),
        'active_channels': NotificationChannel.objects.filter(company=company, is_active=True).count(),
        'total_templates': NotificationTemplate.objects.filter(company=company).count(),
        'active_templates': NotificationTemplate.objects.filter(company=company, is_active=True).count(),
        'total_rules': NotificationRule.objects.filter(company=company).count(),
        'active_rules': NotificationRule.objects.filter(company=company, is_active=True).count(),
        'notifications_today': NotificationLog.objects.filter(
            rule__company=company,
            created_at__date=today
        ).count(),
        'notifications_week': NotificationLog.objects.filter(
            rule__company=company,
            created_at__gte=week_ago
        ).count(),
        'notifications_month': NotificationLog.objects.filter(
            rule__company=company,
            created_at__gte=month_ago
        ).count(),
    }
    
    # Son bildirimler
    recent_notifications = NotificationLog.objects.filter(
        rule__company=company
    ).order_by('-created_at')[:10]
    
    # Kanal istatistikleri
    channel_stats = []
    for channel in NotificationChannel.objects.filter(company=company):
        channel_stats.append({
            'channel': channel,
            'sent': NotificationLog.objects.filter(
                channel=channel,
                created_at__gte=week_ago,
                status='sent'
            ).count(),
            'failed': NotificationLog.objects.filter(
                channel=channel,
                created_at__gte=week_ago,
                status='failed'
            ).count(),
        })
    
    # Kural istatistikleri
    rule_stats = []
    for rule in NotificationRule.objects.filter(company=company, is_active=True):
        rule_stats.append({
            'rule': rule,
            'trigger_count': rule.trigger_count,
            'last_triggered': rule.last_triggered,
            'recent_notifications': NotificationLog.objects.filter(
                rule=rule,
                created_at__gte=week_ago
            ).count(),
        })
    
    # Durum dağılımı
    status_distribution = NotificationLog.objects.filter(
        rule__company=company,
        created_at__gte=month_ago
    ).values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'company': company,
        'stats': stats,
        'recent_notifications': recent_notifications,
        'channel_stats': channel_stats,
        'rule_stats': rule_stats,
        'status_distribution': status_distribution,
    }
    
    return render(request, 'notification_system/dashboard.html', context)


@company_required
def channels_list(request, company_slug):
    """Bildirim kanalları listesi"""
    company = request.company
    
    channels = NotificationChannel.objects.filter(company=company).order_by('priority', 'name')
    
    # Arama
    search = request.GET.get('search', '')
    if search:
        channels = channels.filter(
            Q(name__icontains=search) |
            Q(channel_type__icontains=search)
        )
    
    # Filtreleme
    channel_type = request.GET.get('type', '')
    if channel_type:
        channels = channels.filter(channel_type=channel_type)
    
    is_active = request.GET.get('active', '')
    if is_active == 'true':
        channels = channels.filter(is_active=True)
    elif is_active == 'false':
        channels = channels.filter(is_active=False)
    
    # Sayfalama
    paginator = Paginator(channels, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'channel_type': channel_type,
        'is_active': is_active,
        'channel_types': NotificationChannel.CHANNEL_TYPES,
    }
    
    return render(request, 'notification_system/channels_list.html', context)


@company_required
def channel_detail(request, company_slug, channel_id):
    """Bildirim kanalı detayı"""
    company = request.company
    channel = get_object_or_404(NotificationChannel, id=channel_id, company=company)
    
    # Kanal istatistikleri
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    stats = {
        'total_notifications': NotificationLog.objects.filter(channel=channel).count(),
        'notifications_week': NotificationLog.objects.filter(
            channel=channel,
            created_at__gte=week_ago
        ).count(),
        'notifications_month': NotificationLog.objects.filter(
            channel=channel,
            created_at__gte=month_ago
        ).count(),
        'success_rate': 0,
        'failed_count': NotificationLog.objects.filter(
            channel=channel,
            status='failed'
        ).count(),
    }
    
    # Başarı oranı hesapla
    total_sent = NotificationLog.objects.filter(
        channel=channel,
        status__in=['sent', 'delivered', 'failed']
    ).count()
    
    if total_sent > 0:
        successful = NotificationLog.objects.filter(
            channel=channel,
            status__in=['sent', 'delivered']
        ).count()
        stats['success_rate'] = round((successful / total_sent) * 100, 1)
    
    # Son bildirimler
    recent_notifications = NotificationLog.objects.filter(
        channel=channel
    ).order_by('-created_at')[:20]
    
    # Kullanılan kurallar
    used_rules = NotificationRule.objects.filter(
        company=company,
        channels=channel
    ).distinct()
    
    context = {
        'company': company,
        'channel': channel,
        'stats': stats,
        'recent_notifications': recent_notifications,
        'used_rules': used_rules,
    }
    
    return render(request, 'notification_system/channel_detail.html', context)


@company_required
def channel_add(request, company_slug):
    """Yeni bildirim kanalı ekle"""
    company = request.company
    
    if request.method == 'POST':
        try:
            channel = NotificationChannel.objects.create(
                company=company,
                name=request.POST.get('name'),
                channel_type=request.POST.get('channel_type'),
                is_active=request.POST.get('is_active') == 'on',
                priority=int(request.POST.get('priority', 1)),
                
                # E-posta ayarları
                smtp_host=request.POST.get('smtp_host', ''),
                smtp_port=int(request.POST.get('smtp_port', 0)) if request.POST.get('smtp_port') else None,
                smtp_username=request.POST.get('smtp_username', ''),
                smtp_password=request.POST.get('smtp_password', ''),
                smtp_use_tls=request.POST.get('smtp_use_tls') == 'on',
                from_email=request.POST.get('from_email', ''),
                
                # SMS ayarları
                sms_provider=request.POST.get('sms_provider', ''),
                sms_api_key=request.POST.get('sms_api_key', ''),
                sms_api_secret=request.POST.get('sms_api_secret', ''),
                sms_sender_id=request.POST.get('sms_sender_id', ''),
                
                # Webhook ayarları
                webhook_url=request.POST.get('webhook_url', ''),
                webhook_secret=request.POST.get('webhook_secret', ''),
                
                # Slack ayarları
                slack_webhook_url=request.POST.get('slack_webhook_url', ''),
                slack_channel=request.POST.get('slack_channel', ''),
                slack_username=request.POST.get('slack_username', ''),
                
                # Teams ayarları
                teams_webhook_url=request.POST.get('teams_webhook_url', ''),
                
                # Telegram ayarları
                telegram_bot_token=request.POST.get('telegram_bot_token', ''),
                telegram_chat_id=request.POST.get('telegram_chat_id', ''),
                
                # Discord ayarları
                discord_webhook_url=request.POST.get('discord_webhook_url', ''),
                
                # Test ayarları
                test_mode=request.POST.get('test_mode') == 'on',
                test_recipients=request.POST.get('test_recipients', ''),
            )
            
            messages.success(request, 'Bildirim kanalı başarıyla oluşturuldu.')
            return redirect('notification_system:channel_detail', company.slug, channel.id)
            
        except Exception as e:
            messages.error(request, f'Kanal oluşturulurken hata: {str(e)}')
    
    context = {
        'company': company,
        'channel_types': [
            ('email', 'E-posta'),
            ('sms', 'SMS'),
            ('webhook', 'Webhook'),
            ('slack', 'Slack'),
            ('teams', 'Microsoft Teams'),
            ('telegram', 'Telegram'),
            ('discord', 'Discord'),
        ],
    }
    
    return render(request, 'notification_system/channel_add.html', context)


@company_required
def channel_edit(request, company_slug, channel_id):
    """Bildirim kanalı düzenle"""
    company = request.company
    channel = get_object_or_404(NotificationChannel, id=channel_id, company=company)
    
    if request.method == 'POST':
        try:
            channel.name = request.POST.get('name')
            channel.channel_type = request.POST.get('channel_type')
            channel.is_active = request.POST.get('is_active') == 'on'
            channel.priority = int(request.POST.get('priority', 1))
            
            # E-posta ayarları
            channel.smtp_host = request.POST.get('smtp_host', '')
            channel.smtp_port = int(request.POST.get('smtp_port', 0)) if request.POST.get('smtp_port') else None
            channel.smtp_username = request.POST.get('smtp_username', '')
            channel.smtp_password = request.POST.get('smtp_password', '')
            channel.smtp_use_tls = request.POST.get('smtp_use_tls') == 'on'
            channel.from_email = request.POST.get('from_email', '')
            
            # SMS ayarları
            channel.sms_provider = request.POST.get('sms_provider', '')
            channel.sms_api_key = request.POST.get('sms_api_key', '')
            channel.sms_api_secret = request.POST.get('sms_api_secret', '')
            channel.sms_sender_id = request.POST.get('sms_sender_id', '')
            
            # Webhook ayarları
            channel.webhook_url = request.POST.get('webhook_url', '')
            channel.webhook_secret = request.POST.get('webhook_secret', '')
            
            # Slack ayarları
            channel.slack_webhook_url = request.POST.get('slack_webhook_url', '')
            channel.slack_channel = request.POST.get('slack_channel', '')
            channel.slack_username = request.POST.get('slack_username', '')
            
            # Teams ayarları
            channel.teams_webhook_url = request.POST.get('teams_webhook_url', '')
            
            # Telegram ayarları
            channel.telegram_bot_token = request.POST.get('telegram_bot_token', '')
            channel.telegram_chat_id = request.POST.get('telegram_chat_id', '')
            
            # Discord ayarları
            channel.discord_webhook_url = request.POST.get('discord_webhook_url', '')
            
            # Test ayarları
            channel.test_mode = request.POST.get('test_mode') == 'on'
            channel.test_recipients = request.POST.get('test_recipients', '')
            
            channel.save()
            
            messages.success(request, 'Bildirim kanalı başarıyla güncellendi.')
            return redirect('notification_system:channel_detail', company.slug, channel.id)
            
        except Exception as e:
            messages.error(request, f'Kanal güncellenirken hata: {str(e)}')
    
    context = {
        'company': company,
        'channel': channel,
        'channel_types': NotificationChannel.CHANNEL_TYPES,
    }
    
    return render(request, 'notification_system/channel_edit.html', context)


@company_required
def templates_list(request, company_slug):
    """Bildirim şablonları listesi"""
    company = request.company
    
    templates = NotificationTemplate.objects.filter(company=company).order_by('template_type', 'name')
    
    # Arama
    search = request.GET.get('search', '')
    if search:
        templates = templates.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filtreleme
    template_type = request.GET.get('type', '')
    if template_type:
        templates = templates.filter(template_type=template_type)
    
    is_active = request.GET.get('active', '')
    if is_active == 'true':
        templates = templates.filter(is_active=True)
    elif is_active == 'false':
        templates = templates.filter(is_active=False)
    
    # Sayfalama
    paginator = Paginator(templates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'template_type': template_type,
        'is_active': is_active,
        'template_types': NotificationTemplate.TEMPLATE_TYPES,
    }
    
    return render(request, 'notification_system/templates_list.html', context)


@company_required
def template_detail(request, company_slug, template_id):
    """Bildirim şablonu detayı"""
    company = request.company
    template = get_object_or_404(NotificationTemplate, id=template_id, company=company)
    
    # Şablona ait kurallar
    rules = NotificationRule.objects.filter(template=template)
    
    # Şablona ait bildirimler
    notifications = NotificationLog.objects.filter(
        template=template
    ).order_by('-created_at')[:20]
    
    # İstatistikler
    stats = {
        'total_rules': rules.count(),
        'active_rules': rules.filter(is_active=True).count(),
        'total_notifications': notifications.count(),
        'successful_notifications': notifications.filter(status='sent').count(),
        'failed_notifications': notifications.filter(status='failed').count(),
    }
    
    context = {
        'company': company,
        'template': template,
        'rules': rules,
        'notifications': notifications,
        'stats': stats,
    }
    
    return render(request, 'notification_system/template_detail.html', context)


@company_required
def template_add(request, company_slug):
    """Yeni bildirim şablonu ekle"""
    company = request.company
    
    if request.method == 'POST':
        try:
            template = NotificationTemplate.objects.create(
                company=company,
                name=request.POST.get('name'),
                template_type=request.POST.get('template_type'),
                description=request.POST.get('description', ''),
                
                # E-posta şablonu
                email_subject=request.POST.get('email_subject', ''),
                email_body_html=request.POST.get('email_body_html', ''),
                email_body_text=request.POST.get('email_body_text', ''),
                
                # SMS şablonu
                sms_message=request.POST.get('sms_message', ''),
                
                # Push bildirim şablonu
                push_title=request.POST.get('push_title', ''),
                push_body=request.POST.get('push_body', ''),
                push_icon=request.POST.get('push_icon', ''),
                
                # Webhook şablonu
                webhook_payload=json.loads(request.POST.get('webhook_payload', '{}')),
                
                # Slack şablonu
                slack_message=request.POST.get('slack_message', ''),
                slack_color=request.POST.get('slack_color', 'good'),
                
                # Teams şablonu
                teams_title=request.POST.get('teams_title', ''),
                teams_message=request.POST.get('teams_message', ''),
                
                # Telegram şablonu
                telegram_message=request.POST.get('telegram_message', ''),
                telegram_parse_mode=request.POST.get('telegram_parse_mode', 'HTML'),
                
                # Discord şablonu
                discord_embed=json.loads(request.POST.get('discord_embed', '{}')),
                
                # Değişkenler
                available_variables=request.POST.get('available_variables', ''),
                
                # Durum
                is_active=request.POST.get('is_active') == 'on',
                is_default=request.POST.get('is_default') == 'on',
                created_by=request.user,
            )
            
            messages.success(request, 'Bildirim şablonu başarıyla oluşturuldu.')
            return redirect('notification_system:template_detail', company.slug, template.id)
            
        except Exception as e:
            messages.error(request, f'Şablon oluşturulurken hata: {str(e)}')
    
    context = {
        'company': company,
        'template_types': NotificationTemplate.TEMPLATE_TYPES,
    }
    
    return render(request, 'notification_system/template_add.html', context)


@company_required
def rules_list(request, company_slug):
    """Bildirim kuralları listesi"""
    company = request.company
    
    rules = NotificationRule.objects.filter(company=company).order_by('name')
    
    # Arama
    search = request.GET.get('search', '')
    if search:
        rules = rules.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filtreleme
    trigger_type = request.GET.get('trigger_type', '')
    if trigger_type:
        rules = rules.filter(trigger_type=trigger_type)
    
    is_active = request.GET.get('active', '')
    if is_active == 'true':
        rules = rules.filter(is_active=True)
    elif is_active == 'false':
        rules = rules.filter(is_active=False)
    
    # Sayfalama
    paginator = Paginator(rules, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'trigger_type': trigger_type,
        'is_active': is_active,
        'trigger_types': NotificationRule.TRIGGER_TYPES,
    }
    
    return render(request, 'notification_system/rules_list.html', context)


@company_required
def rule_detail(request, company_slug, rule_id):
    """Bildirim kuralı detayı"""
    company = request.company
    rule = get_object_or_404(NotificationRule, id=rule_id, company=company)
    
    # Kural istatistikleri
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    stats = {
        'total_notifications': NotificationLog.objects.filter(rule=rule).count(),
        'notifications_week': NotificationLog.objects.filter(
            rule=rule,
            created_at__gte=week_ago
        ).count(),
        'notifications_month': NotificationLog.objects.filter(
            rule=rule,
            created_at__gte=month_ago
        ).count(),
        'success_rate': 0,
        'last_triggered': rule.last_triggered,
        'trigger_count': rule.trigger_count,
    }
    
    # Başarı oranı hesapla
    total_sent = NotificationLog.objects.filter(
        rule=rule,
        status__in=['sent', 'delivered', 'failed']
    ).count()
    
    if total_sent > 0:
        successful = NotificationLog.objects.filter(
            rule=rule,
            status__in=['sent', 'delivered']
        ).count()
        stats['success_rate'] = round((successful / total_sent) * 100, 1)
    
    # Son bildirimler
    recent_notifications = NotificationLog.objects.filter(
        rule=rule
    ).order_by('-created_at')[:20]
    
    # Kanal istatistikleri
    channel_stats = []
    for channel in rule.channels.all():
        channel_stats.append({
            'channel': channel,
            'sent': NotificationLog.objects.filter(
                rule=rule,
                channel=channel,
                created_at__gte=week_ago,
                status='sent'
            ).count(),
            'failed': NotificationLog.objects.filter(
                rule=rule,
                channel=channel,
                created_at__gte=week_ago,
                status='failed'
            ).count(),
        })
    
    context = {
        'company': company,
        'rule': rule,
        'stats': stats,
        'recent_notifications': recent_notifications,
        'channel_stats': channel_stats,
    }
    
    return render(request, 'notification_system/rule_detail.html', context)


@company_required
def rule_add(request, company_slug):
    """Yeni bildirim kuralı ekle"""
    company = request.company
    
    if request.method == 'POST':
        try:
            rule = NotificationRule.objects.create(
                company=company,
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                trigger_type=request.POST.get('rule_type', 'immediate'),
                trigger_condition=request.POST.get('trigger_condition', ''),
                threshold_value=int(request.POST.get('threshold_value', 0)) if request.POST.get('threshold_value') else None,
                time_window=int(request.POST.get('time_window', 5)),
                
                # Filtreleme
                filter_conditions=json.loads(request.POST.get('filter_conditions', '{}')),
                severity_levels=json.loads(request.POST.get('severity_levels', '[]')),
                
                # Bildirim ayarları
                template_id=request.POST.get('template') if request.POST.get('template') else None,
                recipients=request.POST.get('recipients', ''),
                
                # Zamanlama
                schedule_cron=request.POST.get('schedule_cron', ''),
                schedule_timezone=request.POST.get('schedule_timezone', 'Europe/Istanbul'),
                
                # Sınırlamalar
                max_notifications_per_hour=int(request.POST.get('max_notifications_per_hour', 10)),
                max_notifications_per_day=int(request.POST.get('max_notifications_per_day', 50)),
                cooldown_period=int(request.POST.get('cooldown_period', 30)),
                
                # Durum
                is_active=request.POST.get('is_active') == 'on',
                created_by=request.user,
            )
            
            # Kanalları ekle
            channel_types = request.POST.getlist('channels')
            if channel_types:
                # Channel type'larından gerçek channel objelerini bul
                channels = NotificationChannel.objects.filter(
                    company=company,
                    channel_type__in=channel_types,
                    is_active=True
                )
                if channels.exists():
                    rule.channels.set(channels)
                else:
                    # Seçilen channel type'lar için channel yoksa oluştur
                    for channel_type in channel_types:
                        channel, created = NotificationChannel.objects.get_or_create(
                            company=company,
                            channel_type=channel_type,
                            defaults={
                                'name': f'{channel_type.title()} Kanalı',
                                'is_active': True,
                            }
                        )
                        rule.channels.add(channel)
            else:
                # En az bir kanal seçilmeli
                messages.error(request, 'En az bir bildirim kanalı seçilmelidir.')
                return redirect('notification_system:rule_add', company.slug)
            
            messages.success(request, 'Bildirim kuralı başarıyla oluşturuldu.')
            return redirect('notification_system:rule_detail', company.slug, rule.id)
            
        except Exception as e:
            messages.error(request, f'Kural oluşturulurken hata: {str(e)}')
    
    templates = NotificationTemplate.objects.filter(company=company, is_active=True).order_by('name')
    channels = NotificationChannel.objects.filter(company=company, is_active=True).order_by('name')
    
    context = {
        'company': company,
        'templates': templates,
        'channels': channels,
        'trigger_types': [
            ('immediate', 'Anında'),
            ('threshold', 'Eşik Aşımı'),
            ('schedule', 'Zamanlanmış'),
            ('event', 'Olay Bazlı'),
            ('condition', 'Koşul Bazlı'),
        ],
    }
    
    return render(request, 'notification_system/rule_add.html', context)


@company_required
def notifications_list(request, company_slug):
    """Bildirim logları listesi"""
    company = request.company
    
    notifications = NotificationLog.objects.filter(
        rule__company=company
    ).order_by('-created_at')
    
    # Arama
    search = request.GET.get('search', '')
    if search:
        notifications = notifications.filter(
            Q(recipient__icontains=search) |
            Q(subject__icontains=search) |
            Q(message__icontains=search)
        )
    
    # Filtreleme
    status = request.GET.get('status', '')
    if status:
        notifications = notifications.filter(status=status)
    
    channel_id = request.GET.get('channel', '')
    if channel_id:
        notifications = notifications.filter(channel_id=channel_id)
    
    rule_id = request.GET.get('rule', '')
    if rule_id:
        notifications = notifications.filter(rule_id=rule_id)
    
    # Tarih aralığı
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            notifications = notifications.filter(created_at__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            notifications = notifications.filter(created_at__date__lte=date_to)
        except ValueError:
            pass
    
    # Sayfalama
    paginator = Paginator(notifications, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtre seçenekleri
    channels = NotificationChannel.objects.filter(company=company).order_by('name')
    rules = NotificationRule.objects.filter(company=company).order_by('name')
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'channel_id': channel_id,
        'rule_id': rule_id,
        'date_from': date_from,
        'date_to': date_to,
        'channels': channels,
        'rules': rules,
        'status_choices': NotificationLog.STATUS_CHOICES,
    }
    
    return render(request, 'notification_system/notifications_list.html', context)


@company_required
def subscriptions_list(request, company_slug):
    """Bildirim abonelikleri listesi"""
    company = request.company
    
    subscriptions = NotificationSubscription.objects.filter(company=company).order_by('user__username')
    
    # Arama
    search = request.GET.get('search', '')
    if search:
        subscriptions = subscriptions.filter(
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    
    # Sayfalama
    paginator = Paginator(subscriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
    }
    
    return render(request, 'notification_system/subscriptions_list.html', context)


@company_required
def subscription_detail(request, company_slug, subscription_id):
    """Bildirim aboneliği detayı"""
    company = request.company
    subscription = get_object_or_404(NotificationSubscription, id=subscription_id, company=company)
    
    # Kullanıcının bildirim geçmişi
    notifications = NotificationLog.objects.filter(
        rule__company=company,
        recipient=subscription.user.email
    ).order_by('-created_at')[:20]
    
    context = {
        'company': company,
        'subscription': subscription,
        'notifications': notifications,
    }
    
    return render(request, 'notification_system/subscription_detail.html', context)


@company_required
def test_notification(request, company_slug):
    """Test bildirimi gönder"""
    company = request.company
    
    if request.method == 'POST':
        try:
            channel_id = request.POST.get('channel')
            template_id = request.POST.get('template')
            recipient = request.POST.get('recipient')
            
            if not all([channel_id, template_id, recipient]):
                messages.error(request, 'Tüm alanları doldurun.')
                return redirect('notification_system:test_notification', company.slug)
            
            channel = get_object_or_404(NotificationChannel, id=channel_id, company=company)
            template = get_object_or_404(NotificationTemplate, id=template_id, company=company)
            
            # Test verisi
            test_data = {
                'user_log': LogKayit.objects.filter(company=company).first(),
                'syslog_message': None,  # Syslog modülü varsa eklenebilir
            }
            
            # Bildirim gönder
            manager = NotificationManager(company)
            success = manager.send_immediate_notification(
                template_type=template.template_type,
                data=test_data,
                channels=[channel],
                recipients=[recipient]
            )
            
            if success:
                messages.success(request, f'Test bildirimi {recipient} adresine gönderildi.')
            else:
                messages.error(request, 'Test bildirimi gönderilemedi.')
            
        except Exception as e:
            messages.error(request, f'Test bildirimi hatası: {str(e)}')
    
    channels = NotificationChannel.objects.filter(company=company, is_active=True).order_by('name')
    templates = NotificationTemplate.objects.filter(company=company, is_active=True).order_by('name')
    
    context = {
        'company': company,
        'channels': channels,
        'templates': templates,
    }
    
    return render(request, 'notification_system/test_notification.html', context)


@company_required
@require_http_methods(["POST"])
def delete_channel(request, company_slug, channel_id):
    """Bildirim kanalı sil"""
    company = request.company
    channel = get_object_or_404(NotificationChannel, id=channel_id, company=company)
    
    try:
        # Kanalı kullanan kuralları kontrol et
        rule_count = NotificationRule.objects.filter(channels=channel).count()
        if rule_count > 0:
            messages.error(request, f'Bu kanal {rule_count} kural tarafından kullanılıyor. Önce kuralları güncelleyin.')
            return redirect('notification_system:channel_detail', company.slug, channel.id)
        
        channel.delete()
        messages.success(request, 'Bildirim kanalı başarıyla silindi.')
        
    except Exception as e:
        messages.error(request, f'Kanal silinirken hata: {str(e)}')
    
    return redirect('notification_system:channels_list', company.slug)


@company_required
@require_http_methods(["POST"])
def delete_template(request, company_slug, template_id):
    """Bildirim şablonu sil"""
    company = request.company
    template = get_object_or_404(NotificationTemplate, id=template_id, company=company)
    
    try:
        # Şablonu kullanan kuralları kontrol et
        rule_count = NotificationRule.objects.filter(template=template).count()
        if rule_count > 0:
            messages.error(request, f'Bu şablon {rule_count} kural tarafından kullanılıyor. Önce kuralları güncelleyin.')
            return redirect('notification_system:template_detail', company.slug, template.id)
        
        template.delete()
        messages.success(request, 'Bildirim şablonu başarıyla silindi.')
        
    except Exception as e:
        messages.error(request, f'Şablon silinirken hata: {str(e)}')
    
    return redirect('notification_system:templates_list', company.slug)


@company_required
@require_http_methods(["POST"])
def delete_rule(request, company_slug, rule_id):
    """Bildirim kuralı sil"""
    company = request.company
    rule = get_object_or_404(NotificationRule, id=rule_id, company=company)
    
    try:
        rule.delete()
        messages.success(request, 'Bildirim kuralı başarıyla silindi.')
        
    except Exception as e:
        messages.error(request, f'Kural silinirken hata: {str(e)}')
    
    return redirect('notification_system:rules_list', company.slug)


@company_required
@require_http_methods(["POST"])
def toggle_rule(request, company_slug, rule_id):
    """Bildirim kuralını aktif/pasif yap"""
    company = request.company
    rule = get_object_or_404(NotificationRule, id=rule_id, company=company)
    
    try:
        rule.is_active = not rule.is_active
        rule.save()
        
        status = "aktif" if rule.is_active else "pasif"
        messages.success(request, f'Bildirim kuralı {status} yapıldı.')
        
    except Exception as e:
        messages.error(request, f'Durum değiştirilirken hata: {str(e)}')
    
    return redirect('notification_system:rule_detail', company.slug, rule.id)


@company_required
def api_notification_stats(request, company_slug):
    """Bildirim istatistikleri API"""
    company = request.company
    
    # Son 30 günlük veriler
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    notifications = NotificationLog.objects.filter(
        rule__company=company,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    # Günlük bildirim sayıları
    daily_data = []
    for i in range(30):
        date = start_date + timedelta(days=i)
        count = notifications.filter(created_at__date=date).count()
        daily_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Durum dağılımı
    status_data = list(notifications.values('status').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # Kanal dağılımı
    channel_data = list(notifications.values('channel__name').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    return JsonResponse({
        'daily_notifications': daily_data,
        'status_distribution': status_data,
        'channel_distribution': channel_data,
        'total_notifications': notifications.count(),
        'successful_notifications': notifications.filter(status='sent').count(),
        'failed_notifications': notifications.filter(status='failed').count(),
    })
