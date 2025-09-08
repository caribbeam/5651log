from django.apps import AppConfig


class ProfileManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profile_management'
    verbose_name = 'Profil Yönetimi'
    
    def ready(self):
        import profile_management.signals
