#!/usr/bin/env python
"""
Demo veri oluşturma scripti
"""
import os
import sys
import django

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yasalog.settings')
django.setup()

from log_kayit.models import Company, CompanyUser
from django.contrib.auth.models import User

def create_demo_data():
    """Demo şirket ve kullanıcı verileri oluşturur"""
    
    # Demo şirket oluştur
    company, created = Company.objects.get_or_create(
        name="Demo Kafe",
        defaults={
            'slug': 'demo-kafe',
            'address': 'İstanbul, Türkiye',
            'contact_person': 'Ahmet Yılmaz',
            'phone': '+90 212 555 0123',
            'kvkk_text': 'Kişisel verileriniz 5651 sayılı kanun gereği kayıt altına alınmaktadır.',
            'login_info_text': 'Wi-Fi erişimi için lütfen bilgilerinizi giriniz.',
            'theme_color': '#28a745',
            'allow_foreigners': True
        }
    )
    
    if created:
        print(f"✅ Demo şirket oluşturuldu: {company.name}")
    else:
        print(f"ℹ️ Demo şirket zaten mevcut: {company.name}")
    
    # Demo kullanıcı oluştur
    user, created = User.objects.get_or_create(
        username='demo_user',
        defaults={
            'email': 'demo@5651log.com',
            'first_name': 'Demo',
            'last_name': 'Kullanıcı',
            'is_staff': True
        }
    )
    
    if created:
        user.set_password('demo123456')
        user.save()
        print(f"✅ Demo kullanıcı oluşturuldu: {user.username}")
    else:
        print(f"ℹ️ Demo kullanıcı zaten mevcut: {user.username}")
    
    # Şirket-kullanıcı ilişkisi oluştur
    company_user, created = CompanyUser.objects.get_or_create(
        user=user,
        company=company,
        defaults={
            'role': 'admin'
        }
    )
    
    if created:
        print(f"✅ Şirket-kullanıcı ilişkisi oluşturuldu: {user.username} -> {company.name}")
    else:
        print(f"ℹ️ Şirket-kullanıcı ilişkisi zaten mevcut")
    
    print("\n🎯 Demo veri oluşturma tamamlandı!")
    print(f"📱 Wi-Fi giriş sayfası: http://localhost:8000/giris/{company.slug}/")
    print(f"🔐 Admin paneli: http://localhost:8000/admin/")
    print(f"📊 Dashboard: http://localhost:8000/dashboard/{company.slug}/")
    print(f"🔌 API endpoint: http://localhost:8000/api/v1/companies/{company.slug}/logs/")
    
    return company, user

if __name__ == '__main__':
    create_demo_data()
