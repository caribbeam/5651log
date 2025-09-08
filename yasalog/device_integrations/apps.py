"""
Device Integrations App Configuration
5651log platformunda cihaz entegrasyonları için app yapılandırması
"""

from django.apps import AppConfig


class DeviceIntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'device_integrations'
    verbose_name = 'Cihaz Entegrasyonları'
    label = 'device_integrations'
    
    def ready(self):
        """App hazır olduğunda çalışır"""
        pass
