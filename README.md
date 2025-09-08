# 5651log - Çoklu Şirket Wi-Fi Giriş Kayıt Sistemi

## 📋 Proje Tanıtımı

**5651log**, 5651 sayılı Kanun gereği Wi-Fi erişim noktalarında kullanıcı kimlik doğrulaması ve kayıt tutma zorunluluğunu karşılayan, çoklu şirket desteği olan modern bir web uygulamasıdır. Her şirketin kendi Wi-Fi ağında bağımsız olarak çalışabilir ve kullanıcı verilerini izole eder.

## 🎯 Ana Özellikler

### 🔐 **Çoklu Şirket Desteği**
- Her şirket için ayrı giriş adresi (`/giris/<şirket-slug>/`)
- Tam veri izolasyonu - şirketler birbirinin verilerini göremez
- Şirket bazlı tema ve logo özelleştirme
- Her şirket için ayrı KVKK metni ve giriş açıklaması

### 📊 **Gelişmiş Dashboard**
- Gerçek zamanlı istatistikler ve grafikler
- Günlük/saatlik giriş analizleri
- En aktif kullanıcı listesi
- Şüpheli giriş tespiti ve raporlama
- Filtreleme ve arama özellikleri

### 🔒 **Güvenlik ve Uyumluluk**
- TC Kimlik algoritması doğrulaması
- SHA256 hash ile veri bütünlüğü
- Şüpheli giriş tespiti ve kayıt
- KVKK uyumlu veri işleme
- Yabancı uyruklu kullanıcı desteği (pasaport)

### 📱 **Wi-Fi Entegrasyonu**
- Captive portal uyumlu tasarım
- Cihaz hatırlama özelliği (24 saat)
- Otomatik MAC adresi tespiti
- Responsive tasarım (mobil uyumlu)

## 🏗️ Teknik Mimari

### **Backend Teknolojileri**
- **Django 4.x** - Ana web framework
- **Python 3.8+** - Programlama dili
- **PostgreSQL/MySQL** - Veritabanı
- **Redis** - Cache ve session yönetimi (opsiyonel)

### **Frontend Teknolojileri**
- **Bootstrap 5** - UI framework
- **Chart.js** - Grafik ve istatistikler
- **jQuery** - JavaScript kütüphanesi
- **Responsive Design** - Mobil uyumlu tasarım

### **Deployment & DevOps**
- **Nginx** - Web sunucusu ve reverse proxy
- **Gunicorn** - WSGI sunucusu
- **Supervisor** - Process yönetimi
- **Docker** - Container desteği (opsiyonel)

## 🔧 Çalışma Mantığı

### **1. Kullanıcı Giriş Süreci**
```
Wi-Fi Bağlantısı → Captive Portal → /giris/<şirket-slug>/ → Form Doldurma → Veri Kaydı → İnternet Erişimi
```

### **2. Veri İşleme Akışı**
1. **Kimlik Doğrulama**: TC Kimlik algoritması veya pasaport kontrolü
2. **Veri Kaydı**: IP, MAC, zaman damgası ile birlikte kayıt
3. **Hash Oluşturma**: SHA256 ile veri bütünlüğü sağlama
4. **Şüpheli Tespit**: Geçersiz kimlik numaraları işaretlenir

### **3. Dashboard Erişimi**
```
Yönetici Girişi → /dashboard/<şirket-slug>/ → Yetki Kontrolü → Şirket Verileri → Analiz ve Raporlama
```

## 📊 Veri Modeli

### **Ana Modeller**
- **Company**: Şirket bilgileri ve ayarları
- **LogKayit**: Kullanıcı giriş kayıtları
- **CompanyUser**: Şirket-kullanıcı ilişkisi ve yetkiler

### **Kayıtlanan Veriler**
- TC Kimlik No / Pasaport No
- Ad Soyad
- Telefon (opsiyonel)
- IP Adresi
- MAC Adresi
- Giriş Zamanı
- SHA256 Hash
- Şüpheli Durum

## 🚀 Özellikler Detayı

### **Çoklu Dil Desteği**
- Türkçe ve İngilizce dil desteği
- Dinamik dil değiştirme
- Çeviri dosyaları (Django i18n)

### **Raporlama ve Dışa Aktarma**
- **Excel Export**: Detaylı tablo formatında
- **PDF Export**: Resmi rapor formatında
- **ZIP Export**: Tüm formatları tek dosyada
- **Filtreleme**: Tarih, TC No, ad soyad bazında

### **Yönetim Paneli**
- **Şirket Yönetimi**: Logo, tema, KVKK metni
- **Kullanıcı Yönetimi**: Rol tabanlı yetkilendirme
- **Sistem Ayarları**: Genel konfigürasyon

### **Güvenlik Özellikleri**
- **Yetki Kontrolü**: URL bazlı erişim kontrolü
- **Veri İzolasyonu**: Şirket bazlı veri ayrımı
- **Hash Doğrulama**: Veri bütünlüğü kontrolü
- **Şüpheli Tespit**: Geçersiz kimlik uyarısı

## 🔄 İş Akışı

### **Şirket Kurulumu**
1. Admin panelinden şirket oluşturma
2. Şirket slug'ı ve ayarları belirleme
3. Wi-Fi cihazını `/giris/<slug>/` adresine yönlendirme
4. Şirket yöneticisi hesabı oluşturma

### **Günlük Kullanım**
1. **Ziyaretçi**: Wi-Fi'ye bağlanır → Captive portal açılır
2. **Form Doldurma**: Kimlik bilgileri girilir
3. **Doğrulama**: TC Kimlik algoritması kontrol edilir
4. **Kayıt**: Veriler güvenli şekilde kaydedilir
5. **Erişim**: İnternet erişimi sağlanır

### **Yönetim**
1. **Dashboard**: Gerçek zamanlı istatistikler
2. **Raporlama**: Excel/PDF export
3. **Analiz**: Giriş trendleri ve kullanıcı analizi
4. **Yönetim**: Şirket ayarları ve kullanıcı yönetimi

## 📈 Performans ve Ölçeklenebilirlik

### **Optimizasyonlar**
- Database indexleme
- Query optimizasyonu
- Cache kullanımı
- Static file serving

### **Ölçeklenebilirlik**
- Çoklu şirket desteği
- Modüler yapı
- Docker container desteği
- Load balancing uyumlu

## 🔧 Kurulum ve Deployment

### **Gereksinimler**
- Python 3.8+
- PostgreSQL/MySQL
- Nginx
- Supervisor
- Linux/Ubuntu Server

### **Hızlı Kurulum**
```bash
# Repository klonlama
git clone <repository-url>
cd 5651log

# Bağımlılıkları yükleme
pip install -r requirements.txt

# Veritabanı migrasyonu
python manage.py migrate

# Static dosyaları toplama
python manage.py collectstatic

# Superuser oluşturma
python manage.py createsuperuser
```

### **Production Deployment**
- Nginx konfigürasyonu
- Gunicorn process yönetimi
- SSL sertifikası
- Firewall ayarları
- Backup stratejisi

## 📋 Yasal Uyumluluk

### **5651 Sayılı Kanun**
- Kullanıcı kimlik doğrulaması
- Giriş kayıtları tutma
- Veri saklama süreleri
- KVKK uyumluluğu

### **KVKK Uyumluluğu**
- Aydınlatma metni
- Veri işleme şartları
- Kullanıcı onayı
- Veri güvenliği

## 🎯 Kullanım Senaryoları

### **Küçük İşletmeler**
- Kafe, restoran Wi-Fi'leri
- Otel lobi internet erişimi
- Mağaza müşteri Wi-Fi'si

### **Kurumsal Şirketler**
- Ofis Wi-Fi ağları
- Misafir internet erişimi
- Şube bazlı yönetim

### **Kamu Kurumları**
- Belediye Wi-Fi'leri
- Kütüphane internet erişimi
- Açık alan Wi-Fi'leri

## 🔮 Gelecek Özellikler

- **API Desteği**: REST API entegrasyonu
- **Mobil Uygulama**: iOS/Android app
- **Gelişmiş Analitik**: AI destekli analiz
- **Otomatik Raporlama**: Zamanlanmış raporlar
- **SMS/Email Bildirimleri**: Anlık uyarılar

## 📞 Destek ve İletişim

- **Teknik Destek**: [email]
- **Dokümantasyon**: [wiki-link]
- **GitHub**: [repository-url]
- **Lisans**: MIT License

---

**5651log** - Modern, güvenli ve uyumlu Wi-Fi giriş kayıt sistemi 