# 5651log - Teknik Özellikler ve Mimari Dokümantasyonu

## 🏗️ Sistem Mimarisi

### **Genel Mimari**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Wi-Fi Client  │    │   Captive Portal│    │   Django App    │
│                 │    │                 │    │                 │
│ - Mobile Device │───▶│ - Router/AP     │───▶│ - Web Server    │
│ - Laptop        │    │ - Redirect URL  │    │ - Nginx/Gunicorn│
│ - Tablet        │    │ - MAC Detection │    │ - Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Teknoloji Stack**
- **Backend**: Django 4.x (Python 3.8+)
- **Database**: PostgreSQL/MySQL/SQLite
- **Web Server**: Nginx + Gunicorn
- **Frontend**: Bootstrap 5 + Chart.js + jQuery
- **Process Manager**: Supervisor
- **Container**: Docker (opsiyonel)

## 📊 Veri Modeli Detayı

### **Company Model**
```python
class Company(models.Model):
    name = models.CharField(max_length=100)           # Şirket adı
    slug = models.SlugField(unique=True)              # URL slug'ı
    address = models.CharField(max_length=255)        # Adres
    contact_person = models.CharField(max_length=100) # Yetkili kişi
    phone = models.CharField(max_length=20)           # Telefon
    logo = models.ImageField(upload_to="company_logos/") # Logo
    kvkk_text = models.TextField()                    # KVKK metni
    login_info_text = models.CharField(max_length=255) # Giriş açıklaması
    theme_color = models.CharField(max_length=7)      # Tema rengi
    allow_foreigners = models.BooleanField(default=True) # Yabancı izni
```

### **LogKayit Model**
```python
class LogKayit(models.Model):
    company = models.ForeignKey(Company)              # Şirket ilişkisi
    tc_no = models.CharField(max_length=11)           # TC Kimlik No
    kimlik_turu = models.CharField(choices=[...])     # TC/Pasaport
    pasaport_no = models.CharField(max_length=32)     # Pasaport No
    pasaport_ulkesi = models.CharField(max_length=32) # Pasaport ülkesi
    ad_soyad = models.CharField(max_length=100)       # Ad Soyad
    telefon = models.CharField(max_length=15)         # Telefon
    ip_adresi = models.GenericIPAddressField()        # IP Adresi
    mac_adresi = models.CharField(max_length=17)      # MAC Adresi
    giris_zamani = models.DateTimeField(auto_now_add=True) # Giriş zamanı
    sha256_hash = models.CharField(max_length=64)     # Hash
    is_suspicious = models.BooleanField(default=False) # Şüpheli durum
```

### **CompanyUser Model**
```python
class CompanyUser(models.Model):
    user = models.ForeignKey(User)                    # Django User
    company = models.ForeignKey(Company)              # Şirket ilişkisi
    role = models.CharField(choices=[                 # Rol
        ("admin", "Firma Yöneticisi"),
        ("staff", "Personel"),
        ("viewer", "Sadece Görüntüleyici"),
    ])
```

## 🔧 Çalışma Mantığı Detayı

### **1. Kullanıcı Giriş Süreci**

#### **A. Wi-Fi Bağlantısı**
1. Kullanıcı Wi-Fi'ye bağlanır
2. Router/Access Point captive portal'ı tetikler
3. Kullanıcı otomatik olarak `/giris/<şirket-slug>/` adresine yönlendirilir

#### **B. Cihaz Hatırlama Kontrolü**
```python
def get_mac_from_request(request):
    # Gerçek MAC adresi captive portal'dan gelir
    return request.META.get('HTTP_USER_AGENT', '00:00:00:00:00:00')

# Son 24 saatteki geçerli giriş kontrolü
recent_log = LogKayit.objects.filter(
    mac_adresi=mac_adresi,
    company=company_instance,
    giris_zamani__gte=zaman_siniri,
    is_suspicious=False
).first()
```

#### **C. Form İşleme**
1. **TC Kimlik Doğrulama**: Algoritma kontrolü
2. **Pasaport Kontrolü**: Ülke ve numara validasyonu
3. **Veri Kaydı**: IP, MAC, zaman damgası ile
4. **Hash Oluşturma**: SHA256 ile veri bütünlüğü

### **2. Güvenlik Mekanizmaları**

#### **A. TC Kimlik Algoritması**
```python
def check_tc_kimlik_no(tc):
    if not tc or len(tc) != 11 or not tc.isdigit() or tc[0] == '0':
        return False
    d = [int(x) for x in tc]
    # 1. Kontrol: İlk 10 hanenin toplamının son hanesi 11. hane olmalı
    if (sum(d[:10]) % 10 != d[10]):
        return False
    # 2. Kontrol: Algoritma kontrolü
    if (((sum(d[0:10:2]) * 7) - sum(d[1:9:2])) % 10 != d[9]):
        return False
    return True
```

#### **B. Hash Oluşturma**
```python
def generate_log_hash(tc_no, ad_soyad, telefon, ip_adresi, mac_adresi, timestamp):
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    hash_input = f"{tc_no}{ad_soyad}{telefon}{ip_adresi}{mac_adresi}{formatted_timestamp}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
```

#### **C. Yetki Kontrolü**
```python
# Dashboard erişim kontrolü
if not (CompanyUser.objects.filter(user=request.user, company=company).exists() 
        or request.user.is_superuser):
    return HttpResponseForbidden("Yetkisiz erişim.")

# Veri filtreleme
logs = LogKayit.objects.filter(company=company)
```

### **3. Dashboard ve Analitik**

#### **A. İstatistik Hesaplama**
```python
def _get_dashboard_statistics(logs, company):
    today = timezone.now().date()
    return {
        'toplam_giris': logs.count(),
        'today_total': logs.filter(giris_zamani__date=today).count(),
        'toplam_suspicious': logs.filter(is_suspicious=True).count(),
        'most_active_user': logs.values('ad_soyad')
                              .annotate(count=Count('id'))
                              .order_by('-count').first()
    }
```

#### **B. Grafik Verileri**
```python
def _get_chart_data(logs):
    # Son 30 günlük günlük giriş sayıları
    days = [today - timedelta(days=i) for i in range(29, -1, -1)]
    daily_counts = [logs.filter(giris_zamani__date=day).count() for day in days]
    
    # Son 24 saatlik saatlik giriş sayıları
    last_24_hours = [now.replace(minute=0, second=0, microsecond=0) - 
                     timedelta(hours=i) for i in range(23, -1, -1)]
    return {
        'days': [day.strftime('%d.%m') for day in days],
        'daily_counts': daily_counts,
        'hour_labels': [hour.strftime('%H:00') for hour in last_24_hours],
        'hourly_counts': hourly_counts,
    }
```

## 🔄 URL Yapısı

### **Ziyaretçi URL'leri**
```
/giris/<slug>/                    # Şirket giriş sayfası
/giris/<id>/                      # ID ile giriş sayfası
/giris/cikis/<slug>/              # Cihaz çıkış işlemi
```

### **Yönetim URL'leri**
```
/yonetici/login/                  # Yönetici girişi
/dashboard/<slug>/                # Şirket dashboard'u
/panel/                           # Kullanıcı paneli
/panel/ayarlar/                   # Şirket ayarları
/panel/kullanicilar/              # Kullanıcı yönetimi
```

### **Export URL'leri**
```
/export/excel/<id>/               # Excel export
/export/pdf/<id>/                 # PDF export
/export/zip/<id>/                 # ZIP export
```

## 📊 Performans Optimizasyonları

### **Database Optimizasyonları**
```python
# Index'ler
class LogKayit(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['company', 'giris_zamani']),
            models.Index(fields=['mac_adresi', 'company']),
            models.Index(fields=['is_suspicious']),
        ]

# Query optimizasyonu
logs = LogKayit.objects.filter(company=company).select_related('company')
```

### **Cache Stratejisi**
```python
# Dashboard istatistikleri cache'leme
from django.core.cache import cache

def get_cached_statistics(company_id):
    cache_key = f"stats_{company_id}_{timezone.now().date()}"
    stats = cache.get(cache_key)
    if not stats:
        stats = calculate_statistics(company_id)
        cache.set(cache_key, stats, 300)  # 5 dakika
    return stats
```

## 🔒 Güvenlik Önlemleri

### **1. Veri Güvenliği**
- **Hash Doğrulama**: SHA256 ile veri bütünlüğü
- **Şifreleme**: Hassas veriler şifrelenir
- **Backup**: Düzenli veri yedekleme

### **2. Erişim Kontrolü**
- **URL Güvenliği**: Slug bazlı erişim kontrolü
- **Yetki Sistemi**: Rol tabanlı yetkilendirme
- **Session Yönetimi**: Güvenli oturum kontrolü

### **3. Input Validation**
- **TC Kimlik**: Algoritma kontrolü
- **XSS Koruması**: HTML encoding
- **SQL Injection**: Django ORM koruması
- **CSRF Koruması**: Token tabanlı koruma

## 📈 Ölçeklenebilirlik

### **Horizontal Scaling**
- **Load Balancer**: Nginx ile yük dağıtımı
- **Database Sharding**: Şirket bazlı veri ayrımı
- **CDN**: Static dosya dağıtımı

### **Vertical Scaling**
- **Database Optimization**: Index ve query optimizasyonu
- **Caching**: Redis ile cache katmanı
- **Async Processing**: Celery ile arka plan işlemleri

## 🔧 Deployment Konfigürasyonu

### **Nginx Konfigürasyonu**
```nginx
server {
    listen 8880;
    server_name 213.194.98.98;
    
    location /static/ {
        alias /path/to/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /path/to/media/;
        expires 30d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### **Gunicorn Konfigürasyonu**
```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
```

### **Supervisor Konfigürasyonu**
```ini
[program:5651log]
command=/path/to/venv/bin/gunicorn yasalog.wsgi:application -c gunicorn.conf.py
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/5651log/gunicorn.log
```

## 📊 Monitoring ve Logging

### **Application Logging**
```python
import logging

logger = logging.getLogger(__name__)

def log_user_entry(log_entry):
    logger.info(f"User entry: {log_entry.ad_soyad} - {log_entry.company.name}")
    
def log_suspicious_activity(tc_no, company):
    logger.warning(f"Suspicious TC: {tc_no} - Company: {company.name}")
```

### **Performance Monitoring**
- **Response Time**: Gunicorn access logs
- **Error Rate**: Django error logs
- **Database Performance**: Query execution time
- **System Resources**: CPU, Memory, Disk usage

## 🔮 Gelecek Geliştirmeler

### **API Desteği**
```python
# REST API endpoints
/api/v1/companies/
/api/v1/logs/
/api/v1/statistics/
/api/v1/exports/
```

### **Real-time Updates**
```python
# WebSocket desteği
from channels import Channel

def send_dashboard_update(company_id):
    Channel("dashboard").send({
        "type": "dashboard.update",
        "company_id": company_id
    })
```

### **Machine Learning**
```python
# Anomali tespiti
def detect_anomalies(logs):
    # ML model ile şüpheli aktivite tespiti
    pass
```

---

**Bu dokümantasyon, 5651log uygulamasının teknik detaylarını ve mimarisini açıklamaktadır.** 