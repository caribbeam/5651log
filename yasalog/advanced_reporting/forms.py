from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ReportTemplate, ReportSchedule, GeneratedReport


class ReportTemplateForm(forms.ModelForm):
    """Rapor şablonu formu"""
    
    class Meta:
        model = ReportTemplate
        fields = [
            'name', 'description', 'report_type', 'report_format',
            'generation_time', 'is_active', 'filters', 'template_config'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Şablon adı girin')
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Açıklama girin')
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'report_format': forms.Select(attrs={
                'class': 'form-control'
            }),
            'generation_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'filters': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '{"date_range": "last_30_days", "user_type": "all"}'
            }),
            'template_config': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '{"sections": ["summary", "details"], "charts": true}'
            })
        }
        labels = {
            'name': _('Şablon Adı'),
            'description': _('Açıklama'),
            'report_type': _('Rapor Türü'),
            'report_format': _('Rapor Formatı'),
            'generation_time': _('Oluşturma Saati'),
            'is_active': _('Aktif'),
            'filters': _('Filtreler (JSON)'),
            'template_config': _('Şablon Konfigürasyonu (JSON)')
        }
    
    def clean_filters(self):
        """JSON formatını kontrol et"""
        filters = self.cleaned_data.get('filters')
        if filters:
            try:
                import json
                json.loads(filters)
            except json.JSONDecodeError:
                raise forms.ValidationError(_('Geçerli bir JSON formatı girin'))
        return filters
    
    def clean_template_config(self):
        """JSON formatını kontrol et"""
        config = self.cleaned_data.get('template_config')
        if config:
            try:
                import json
                json.loads(config)
            except json.JSONDecodeError:
                raise forms.ValidationError(_('Geçerli bir JSON formatı girin'))
        return config


class ReportScheduleForm(forms.ModelForm):
    """Rapor zamanlama formu"""
    
    class Meta:
        model = ReportSchedule
        fields = [
            'name', 'description', 'template', 'frequency',
            'run_time', 'is_active', 'email_recipients'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Zamanlama adı girin')
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Açıklama girin')
            }),
            'template': forms.Select(attrs={
                'class': 'form-control'
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'run_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_recipients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'email1@example.com, email2@example.com'
            })
        }
        labels = {
            'name': _('Zamanlama Adı'),
            'description': _('Açıklama'),
            'template': _('Rapor Şablonu'),
            'frequency': _('Sıklık'),
            'run_time': _('Çalıştırma Saati'),
            'is_active': _('Aktif'),
            'email_recipients': _('E-posta Alıcıları')
        }


class NotificationChannelForm(forms.Form):
    """Bildirim kanalı formu"""
    
    CHANNEL_TYPES = [
        ('email', _('E-posta')),
        ('sms', _('SMS')),
        ('webhook', _('Webhook')),
        ('slack', _('Slack')),
        ('teams', _('Microsoft Teams')),
        ('telegram', _('Telegram')),
        ('discord', _('Discord')),
    ]
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Kanal adı girin')
        }),
        label=_('Kanal Adı')
    )
    
    channel_type = forms.ChoiceField(
        choices=CHANNEL_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label=_('Kanal Türü')
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Açıklama girin')
        }),
        label=_('Açıklama')
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('Aktif')
    )
    
    config = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '{"headers": {"Authorization": "Bearer token"}, "timeout": 30}'
        }),
        label=_('Konfigürasyon (JSON)')
    )
    
    def clean_config(self):
        """JSON formatını kontrol et"""
        config = self.cleaned_data.get('config')
        if config:
            try:
                import json
                json.loads(config)
            except json.JSONDecodeError:
                raise forms.ValidationError(_('Geçerli bir JSON formatı girin'))
        return config


class NotificationRuleForm(forms.Form):
    """Bildirim kuralı formu"""
    
    RULE_TYPES = [
        ('threshold', _('Eşik Değeri')),
        ('pattern', _('Desen Eşleşmesi')),
        ('schedule', _('Zamanlanmış')),
        ('event', _('Olay Bazlı')),
    ]
    
    PRIORITIES = [
        ('low', _('Düşük')),
        ('medium', _('Orta')),
        ('high', _('Yüksek')),
        ('critical', _('Kritik')),
    ]
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Kural adı girin')
        }),
        label=_('Kural Adı')
    )
    
    rule_type = forms.ChoiceField(
        choices=RULE_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label=_('Kural Türü')
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Açıklama girin')
        }),
        label=_('Açıklama')
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITIES,
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label=_('Öncelik')
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('Aktif')
    )
    
    rate_limit = forms.IntegerField(
        min_value=1,
        initial=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        label=_('Hız Sınırı (dakika)')
    )
    
    message_template = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Bildirim mesajı şablonu...')
        }),
        label=_('Mesaj Şablonu')
    )
