from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Company, CompanyUser, LogKayit
from .services import validate_tc_kimlik_no


class GirisForm(forms.ModelForm):
    """Wi-Fi giriş formu"""
    KIMLIK_TURU_CHOICES = [
        ('tc', 'T.C. Kimlik'),
        ('pasaport', 'Pasaport'),
    ]
    
    kimlik_turu = forms.ChoiceField(
        choices=KIMLIK_TURU_CHOICES,
        initial='tc',
        widget=forms.RadioSelect,
        label="Kimlik Türü"
    )
    
    tc_no = forms.CharField(
        max_length=11,
        required=False,
        label="T.C. Kimlik No",
        widget=forms.TextInput(attrs={'placeholder': '11 haneli TC kimlik numaranız'})
    )
    
    pasaport_no = forms.CharField(
        max_length=20,
        required=False,
        label="Pasaport No",
        widget=forms.TextInput(attrs={'placeholder': 'Pasaport numaranız'})
    )
    
    pasaport_ulkesi = forms.CharField(
        max_length=50,
        required=False,
        label="Pasaport Ülkesi",
        widget=forms.TextInput(attrs={'placeholder': 'Pasaport ülkesi'})
    )
    
    ad_soyad = forms.CharField(
        max_length=100,
        label="Ad Soyad",
        widget=forms.TextInput(attrs={'placeholder': 'Adınız ve soyadınız'})
    )
    
    telefon = forms.CharField(
        max_length=20,
        required=False,
        label="Telefon (İsteğe Bağlı)",
        widget=forms.TextInput(attrs={'placeholder': 'Telefon numaranız'})
    )
    
    class Meta:
        model = LogKayit
        fields = ['kimlik_turu', 'tc_no', 'pasaport_no', 'pasaport_ulkesi', 'ad_soyad', 'telefon']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.company_instance = kwargs.pop('company_instance', None)
        super().__init__(*args, **kwargs)
        
        # Yabancı uyruklu kullanıcılar için pasaport seçeneği
        if self.company_instance and not self.company_instance.allow_foreigners:
            self.fields['kimlik_turu'].choices = [('tc', 'T.C. Kimlik')]
    
    def clean(self):
        cleaned_data = super().clean()
        kimlik_turu = cleaned_data.get('kimlik_turu')
        tc_no = cleaned_data.get('tc_no')
        pasaport_no = cleaned_data.get('pasaport_no')
        pasaport_ulkesi = cleaned_data.get('pasaport_ulkesi')
        
        if kimlik_turu == 'tc':
            if not tc_no:
                raise forms.ValidationError("T.C. Kimlik numarası gereklidir.")
            if not validate_tc_kimlik_no(tc_no):
                raise forms.ValidationError("Geçersiz T.C. Kimlik numarası.")
        elif kimlik_turu == 'pasaport':
            if not pasaport_no:
                raise forms.ValidationError("Pasaport numarası gereklidir.")
            if not pasaport_ulkesi:
                raise forms.ValidationError("Pasaport ülkesi gereklidir.")
        
        return cleaned_data


class CompanyUserCreationForm(UserCreationForm):
    """Şirket kullanıcısı oluşturma formu"""
    email = forms.EmailField(required=True, label="E-posta")
    first_name = forms.CharField(max_length=30, required=True, label="Ad")
    last_name = forms.CharField(max_length=30, required=True, label="Soyad")
    role = forms.ChoiceField(
        choices=CompanyUser.ROLE_CHOICES,
        initial='viewer',
        label="Rol"
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2", "role")
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Şirket yöneticisi sadece staff ve viewer ekleyebilir
        if self.company:
            self.fields['role'].choices = [
                ('staff', 'Personel'),
                ('viewer', 'Sadece Görüntüleyici')
            ]
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        
        if commit:
            user.save()
            # CompanyUser oluştur
            if self.company:
                CompanyUser.objects.create(
                    user=user,
                    company=self.company,
                    role=self.cleaned_data["role"]
                )
        return user


class CompanyUserEditForm(forms.ModelForm):
    """Kullanıcı düzenleme formu"""
    email = forms.EmailField(required=True, label="E-posta")
    first_name = forms.CharField(max_length=30, required=True, label="Ad")
    last_name = forms.CharField(max_length=30, required=True, label="Soyad")
    is_active = forms.BooleanField(required=False, label="Aktif")
    
    class Meta:
        model = CompanyUser
        fields = ['role', 'is_active']
        labels = {
            'role': 'Rol',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['is_active'].initial = self.instance.user.is_active
    
    def save(self, commit=True):
        company_user = super().save(commit=False)
        if commit:
            company_user.save()
            # User bilgilerini güncelle
            user = company_user.user
            user.email = self.cleaned_data["email"]
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.is_active = self.cleaned_data["is_active"]
            user.save()
        return company_user


class UserPermissionForm(forms.Form):
    """Kullanıcı yetki formu"""
    can_view_dashboard = forms.BooleanField(required=False, label="Dashboard Görüntüleme")
    can_export_data = forms.BooleanField(required=False, label="Veri Dışa Aktarma")
    can_manage_users = forms.BooleanField(required=False, label="Kullanıcı Yönetimi")
    can_view_reports = forms.BooleanField(required=False, label="Rapor Görüntüleme")
    can_edit_company_settings = forms.BooleanField(required=False, label="Şirket Ayarları")
    
    # Zaman sınırlaması
    access_start_time = forms.TimeField(required=False, label="Erişim Başlangıç Saati")
    access_end_time = forms.TimeField(required=False, label="Erişim Bitiş Saati")
    
    # IP sınırlaması
    allowed_ips = forms.CharField(
        required=False, 
        widget=forms.Textarea,
        label="İzin Verilen IP Adresleri (her satıra bir IP)",
        help_text="Boş bırakırsanız tüm IP'lerden erişim sağlanır"
    )
    
    # Geçerlilik tarihi
    valid_until = forms.DateField(required=False, label="Geçerlilik Tarihi")


class BulkUserCreationForm(forms.Form):
    """Toplu kullanıcı oluşturma formu"""
    users_data = forms.CharField(
        widget=forms.Textarea,
        label="Kullanıcı Bilgileri",
        help_text="Her satıra: kullanıcı_adı,email,ad,soyad,rol (virgülle ayrılmış)"
    )
    default_role = forms.ChoiceField(
        choices=CompanyUser.ROLE_CHOICES,
        initial='viewer',
        label="Varsayılan Rol"
    )
    
    def clean_users_data(self):
        data = self.cleaned_data['users_data']
        lines = [line.strip() for line in data.split('\n') if line.strip()]
        
        users = []
        for i, line in enumerate(lines, 1):
            parts = [part.strip() for part in line.split(',')]
            if len(parts) < 4:
                raise forms.ValidationError(f"Satır {i}: En az 4 alan gerekli (kullanıcı_adı,email,ad,soyad)")
            
            users.append({
                'username': parts[0],
                'email': parts[1],
                'first_name': parts[2],
                'last_name': parts[3],
                'role': parts[4] if len(parts) > 4 else self.cleaned_data['default_role']
            })
        
        return users


class CompanySettingsForm(forms.ModelForm):
    """Şirket ayarları formu"""
    class Meta:
        from .models import Company
        model = Company
        fields = ['name', 'address', 'contact_person', 'phone', 'kvkk_text', 'login_info_text', 'theme_color', 'allow_foreigners']
        widgets = {
            'kvkk_text': forms.Textarea(attrs={'rows': 5}),
            'login_info_text': forms.TextInput(attrs={'placeholder': 'Wi-Fi giriş açıklaması'}),
        }
        labels = {
            'name': 'Şirket Adı',
            'address': 'Adres',
            'contact_person': 'Yetkili Kişi',
            'phone': 'Telefon',
            'kvkk_text': 'KVKK Metni',
            'login_info_text': 'Giriş Açıklaması',
            'theme_color': 'Tema Rengi',
            'allow_foreigners': 'Yabancı Uyruklu İzni',
        }