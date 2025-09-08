# 5651log - Kullanım Kılavuzu

## 📋 İçindekiler

1. [Hızlı Başlangıç](#hızlı-başlangıç)
2. [Şirket Kurulumu](#şirket-kurulumu)
3. [Wi-Fi Entegrasyonu](#wi-fi-entegrasyonu)
4. [Kullanıcı Yönetimi](#kullanıcı-yönetimi)
5. [Dashboard Kullanımı](#dashboard-kullanımı)
6. [Raporlama](#raporlama)
7. [Güvenlik ve Uyumluluk](#güvenlik-ve-uyumluluk)
8. [Sık Sorulan Sorular](#sık-sorulan-sorular)

## 🚀 Hızlı Başlangıç

### **1. Admin Paneline Erişim**
```
URL: http://213.194.98.98:8880/admin/
Kullanıcı Adı: [superuser-username]
Şifre: [superuser-password]
```

### **2. İlk Şirket Oluşturma**
1. Admin panelinde "Firmalar" bölümüne gidin
2. "Firma Ekle" butonuna tıklayın
3. Gerekli bilgileri doldurun:
   - **Firma Adı**: Şirketinizin adı
   - **URL Kodu**: Otomatik oluşturulur (örn: "abc-sirket")
   - **Adres**: Şirket adresi
   - **Yetkili Kişi**: İletişim kişisi
   - **Telefon**: İletişim telefonu

### **3. Şirket Ayarları**
- **Logo**: Şirket logosunu yükleyin
- **Tema Rengi**: Renk seçin (örn: #0d6efd)
- **KVKK Metni**: Veri işleme şartları
- **Giriş Formu Açıklaması**: Kullanıcılara gösterilecek metin
- **Yabancı Girişine İzin Ver**: Pasaport ile giriş izni

## 🏢 Şirket Kurulumu

### **Adım 1: Şirket Bilgilerini Girin**
```
Firma Adı: ABC Şirketi
URL Kodu: abc-sirket (otomatik)
Adres: İstanbul, Türkiye
Yetkili Kişi: Ahmet Yılmaz
Telefon: +90 212 123 45 67
```

### **Adım 2: Görsel Ayarları**
```
Logo: abc-logo.png (önerilen boyut: 200x100px)
Tema Rengi: #0d6efd (mavi)
```

### **Adım 3: Metin Ayarları**
```
KVKK Metni: 
"Kişisel verileriniz 5651 sayılı kanun gereği kayıt altına alınmaktadır..."

Giriş Formu Açıklaması:
"ABC Şirketi Wi-Fi ağına hoş geldiniz. Giriş yapmak için kimlik bilgilerinizi giriniz."
```

### **Adım 4: Şirket Yöneticisi Oluşturma**
1. "Kullanıcılar" bölümüne gidin
2. Yeni kullanıcı oluşturun
3. "Firma Kullanıcıları" bölümünde kullanıcıyı şirkete bağlayın
4. Rol olarak "Firma Yöneticisi" seçin

## 📶 Wi-Fi Entegrasyonu

### **Router/Access Point Ayarları**

#### **A. Captive Portal Konfigürasyonu**
1. Router yönetim paneline giriş yapın
2. "Captive Portal" veya "Hotspot" bölümünü bulun
3. Aşağıdaki ayarları yapın:

```
Portal URL: http://213.194.98.98:8880/giris/abc-sirket/
Portal Type: External Portal
Authentication: None (External)
Redirect After Login: Disabled
```

#### **B. MAC Adresi Yakalama**
```
MAC Detection: Enabled
MAC Format: XX:XX:XX:XX:XX:XX
MAC Source: DHCP Request
```

#### **C. DNS Ayarları**
```
DNS Server 1: 8.8.8.8
DNS Server 2: 8.8.4.4
DNS Hijacking: Enabled
```

### **Test Etme**
1. Wi-Fi'ye bağlanın
2. Tarayıcıda herhangi bir siteye gitmeye çalışın
3. Otomatik olarak giriş sayfasına yönlendirilmelisiniz
4. Form doldurup test edin

## 👥 Kullanıcı Yönetimi

### **Kullanıcı Rolleri**

#### **1. Firma Yöneticisi**
- **Yetkiler**: Tam yetki
- **Erişim**: Dashboard, ayarlar, kullanıcı yönetimi
- **İşlemler**: Şirket ayarları, raporlama, kullanıcı ekleme

#### **2. Personel**
- **Yetkiler**: Sınırlı yetki
- **Erişim**: Dashboard, raporlama
- **İşlemler**: Veri görüntüleme, export

#### **3. Sadece Görüntüleyici**
- **Yetkiler**: Sadece görüntüleme
- **Erişim**: Dashboard
- **İşlemler**: Veri görüntüleme

### **Kullanıcı Ekleme**
1. Admin panelinde "Kullanıcılar" bölümüne gidin
2. "Kullanıcı Ekle" butonuna tıklayın
3. Bilgileri doldurun:
   ```
   Kullanıcı Adı: personel1
   E-posta: personel1@abc.com
   Şifre: Güvenli şifre
   ```
4. "Firma Kullanıcıları" bölümünde:
   ```
   Firma: ABC Şirketi
   Rol: Personel
   ```

## 📊 Dashboard Kullanımı

### **Dashboard Erişimi**
```
URL: http://213.194.98.98:8880/dashboard/abc-sirket/
Giriş: Şirket kullanıcısı ile
```

### **Ana Sayfa İstatistikleri**

#### **Üst Kartlar**
- **Toplam Giriş**: Tüm zamanların toplam giriş sayısı
- **Bugünkü Giriş**: Bugün yapılan giriş sayısı
- **Toplam Kullanıcı**: Şirkete atanmış kullanıcı sayısı
- **Şüpheli Giriş**: Geçersiz kimlik numaraları

#### **Grafikler**
- **Günlük Giriş Grafiği**: Son 30 günün giriş trendi
- **Saatlik Giriş Grafiği**: Son 24 saatin saatlik dağılımı
- **En Aktif Kullanıcılar**: En çok giriş yapan kişiler

### **Veri Filtreleme**
```
Filtre Seçenekleri:
- TC No: Belirli TC kimlik numarası
- Ad Soyad: İsim bazlı arama
- Tarih Başlangıç: Başlangıç tarihi
- Tarih Bitiş: Bitiş tarihi
```

### **Şüpheli Girişler**
- Geçersiz TC kimlik numaraları
- Eksik bilgi ile yapılan girişler
- Şüpheli aktivite uyarıları

## 📈 Raporlama

### **Excel Export**
1. Dashboard'da "Excel İndir" butonuna tıklayın
2. Filtreleri ayarlayın (opsiyonel)
3. Dosya otomatik indirilir
4. Format: `loglar_ABC_Şirketi_2024-01-15.xlsx`

### **PDF Export**
1. "PDF İndir" butonuna tıklayın
2. Resmi rapor formatında çıktı
3. Format: `loglar_ABC_Şirketi_2024-01-15.pdf`

### **ZIP Export**
1. "ZIP İndir" butonuna tıklayın
2. Excel ve PDF dosyaları birlikte
3. Format: `loglar_ABC_Şirketi_2024-01-15.zip`

### **Rapor İçeriği**
```
Sütunlar:
- TC No / Pasaport No
- Ad Soyad
- Telefon
- IP Adresi
- MAC Adresi
- Giriş Zamanı
- SHA256 Hash
```

## 🔒 Güvenlik ve Uyumluluk

### **5651 Sayılı Kanun Uyumluluğu**

#### **Zorunlu Kayıtlar**
- ✅ Kullanıcı kimlik bilgileri
- ✅ IP adresi
- ✅ MAC adresi
- ✅ Giriş zamanı
- ✅ Veri bütünlüğü (hash)

#### **Saklama Süreleri**
- **Kayıtlar**: 2 yıl saklanır
- **Hash**: Veri bütünlüğü için sürekli
- **Yedekleme**: Düzenli olarak yapılır

### **KVKK Uyumluluğu**

#### **Aydınlatma Yükümlülüğü**
- ✅ KVKK metni gösterilir
- ✅ Kullanıcı onayı alınır
- ✅ Veri işleme şartları açıklanır

#### **Veri Güvenliği**
- ✅ SHA256 hash ile bütünlük
- ✅ Şifreli veri saklama
- ✅ Erişim kontrolü

### **Güvenlik Önlemleri**

#### **Erişim Kontrolü**
- URL bazlı yetki kontrolü
- Şirket bazlı veri izolasyonu
- Session yönetimi

#### **Veri Doğrulama**
- TC kimlik algoritması kontrolü
- Pasaport numarası validasyonu
- Şüpheli giriş tespiti

## ❓ Sık Sorulan Sorular

### **Q: Wi-Fi cihazım captive portal desteklemiyor, ne yapmalıyım?**
**A:** DNS hijacking yöntemi kullanabilirsiniz. Router'da tüm HTTP trafiğini giriş sayfasına yönlendirin.

### **Q: Yabancı misafirler nasıl giriş yapacak?**
**A:** Şirket ayarlarında "Yabancı Girişine İzin Ver" seçeneğini aktif edin. Pasaport numarası ve ülke seçimi ile giriş yapabilirler.

### **Q: Cihaz hatırlama özelliği nasıl çalışır?**
**A:** Aynı MAC adresinden 24 saat içinde tekrar giriş yapılırsa, form doldurmadan otomatik giriş yapılır.

### **Q: Şüpheli giriş nedir?**
**A:** Geçersiz TC kimlik numarası, eksik bilgi veya algoritma kontrolünden geçmeyen girişler şüpheli olarak işaretlenir.

### **Q: Verilerim güvenli mi?**
**A:** Evet, SHA256 hash ile veri bütünlüğü sağlanır, şirketler arası veri izolasyonu vardır ve düzenli yedekleme yapılır.

### **Q: Raporları nasıl alabilirim?**
**A:** Dashboard'da Excel, PDF veya ZIP formatında raporları indirebilirsiniz. Filtreleme seçenekleri ile özel raporlar oluşturabilirsiniz.

### **Q: Yeni şirket eklemek için ne yapmalıyım?**
**A:** Admin panelinden yeni şirket oluşturun, Wi-Fi cihazını yeni giriş adresine yönlendirin ve şirket yöneticisi hesabı oluşturun.

### **Q: Sistem çökerse verilerim kaybolur mu?**
**A:** Hayır, düzenli yedekleme yapılır ve veriler güvenli şekilde saklanır. Sistem geri yükleme prosedürleri mevcuttur.

## 📞 Destek

### **Teknik Destek**
- **E-posta**: [support@5651log.com]
- **Telefon**: [destek telefonu]
- **Çalışma Saatleri**: 09:00-18:00 (Pazartesi-Cuma)

### **Acil Durumlar**
- **Sistem Kesintisi**: [acil telefon]
- **Güvenlik Sorunu**: [güvenlik e-posta]

### **Dokümantasyon**
- **Kullanım Kılavuzu**: Bu dosya
- **Teknik Dokümantasyon**: TECHNICAL_SPECS.md
- **API Dokümantasyonu**: [API link]

---

**5651log** - Güvenli ve uyumlu Wi-Fi giriş kayıt sistemi 