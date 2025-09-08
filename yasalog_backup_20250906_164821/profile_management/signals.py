"""
Profile Management Signals
5651log platformunda profil yönetimi için gerekli sinyaller
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, UserProfileAssignment

@receiver(post_save, sender=UserProfile)
def create_default_assignment(sender, instance, created, **kwargs):
    """Yeni profil oluşturulduğunda varsayılan atama yap"""
    if created:
        # Bu profil için varsayılan atama oluştur
        pass

@receiver(post_save, sender=UserProfileAssignment)
def update_user_profile(sender, instance, created, **kwargs):
    """Kullanıcı profil ataması güncellendiğinde"""
    if created:
        # Yeni atama oluşturuldu
        pass
    else:
        # Atama güncellendi
        pass

@receiver(post_delete, sender=UserProfile)
def cleanup_profile_assignments(sender, instance, **kwargs):
    """Profil silindiğinde atamaları temizle"""
    # Bu profil için olan tüm atamaları pasif yap
    UserProfileAssignment.objects.filter(profile=instance).update(is_active=False)
