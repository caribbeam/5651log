from rest_framework import serializers
from log_kayit.models import Company, LogKayit, CompanyUser

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'address', 'contact_person', 'phone', 'logo', 'created_at', 'theme_color']

class LogKayitSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = LogKayit
        fields = [
            'id', 'company', 'company_name', 'tc_no', 'kimlik_turu', 'pasaport_no', 
            'pasaport_ulkesi', 'ad_soyad', 'telefon', 'ip_adresi', 'mac_adresi', 
            'giris_zamani', 'is_suspicious'
        ]
        read_only_fields = ['sha256_hash', 'giris_zamani']

class CompanyUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = CompanyUser
        fields = ['id', 'username', 'email', 'role', 'created_at']
