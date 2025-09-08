#!/usr/bin/env python3
"""
5651 Log Uygulaması Kurulum Scripti
Bu script, uygulamayı hızlıca kurmanıza yardımcı olur.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Komut çalıştırır ve sonucu döndürür"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, cwd=cwd)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_python_version():
    """Python versiyonunu kontrol eder"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 veya üzeri gerekli!")
        print(f"   Mevcut versiyon: {sys.version}")
        return False
    print(f"✅ Python versiyonu uygun: {sys.version}")
    return True

def create_virtual_environment():
    """Sanal ortam oluşturur"""
    if os.path.exists("venv"):
        print("✅ Sanal ortam zaten mevcut")
        return True
    
    print("🔧 Sanal ortam oluşturuluyor...")
    success, output = run_command("python -m venv venv")
    if success:
        print("✅ Sanal ortam oluşturuldu")
        return True
    else:
        print(f"❌ Sanal ortam oluşturulamadı: {output}")
        return False

def install_dependencies():
    """Bağımlılıkları yükler"""
    print("📦 Bağımlılıklar yükleniyor...")
    
    # Sanal ortamı aktifleştir
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Linux/Mac
        pip_path = "venv/bin/pip"
    
    success, output = run_command(f"{pip_path} install -r requirements.txt")
    if success:
        print("✅ Bağımlılıklar yüklendi")
        return True
    else:
        print(f"❌ Bağımlılıklar yüklenemedi: {output}")
        return False

def setup_database():
    """Veritabanını hazırlar"""
    print("🗄️ Veritabanı hazırlanıyor...")
    
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Linux/Mac
        python_path = "venv/bin/python"
    
    # Django ayarlarını kontrol et
    if not os.path.exists("yasalog/yasalog/settings.py"):
        print("❌ Django projesi bulunamadı!")
        return False
    
    # Migrate işlemi
    success, output = run_command(f"{python_path} manage.py migrate", cwd="yasalog")
    if success:
        print("✅ Veritabanı hazırlandı")
        return True
    else:
        print(f"❌ Veritabanı hazırlanamadı: {output}")
        return False

def create_superuser():
    """Süper kullanıcı oluşturur"""
    print("👤 Süper kullanıcı oluşturuluyor...")
    print("   (Varsayılan: admin/admin123)")
    
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Linux/Mac
        python_path = "venv/bin/python"
    
    # Otomatik süper kullanıcı oluştur
    create_user_script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yasalog.settings')
django.setup()

from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Süper kullanıcı oluşturuldu: admin/admin123')
else:
    print('Süper kullanıcı zaten mevcut')
"""
    
    with open("yasalog/create_admin.py", "w") as f:
        f.write(create_user_script)
    
    success, output = run_command(f"{python_path} create_admin.py", cwd="yasalog")
    if success:
        print("✅ Süper kullanıcı oluşturuldu")
        os.remove("yasalog/create_admin.py")
        return True
    else:
        print(f"❌ Süper kullanıcı oluşturulamadı: {output}")
        return False

def create_env_file():
    """Environment dosyası oluşturur"""
    env_content = """# Django Settings
SECRET_KEY=django-insecure-your-secret-key-change-this-in-production
DEBUG=True

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Static and Media Files
STATIC_URL=/static/
MEDIA_URL=/media/

# Language and Timezone
LANGUAGE_CODE=tr
TIME_ZONE=Europe/Istanbul

# Email Settings (for password reset)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ .env dosyası oluşturuldu")
    else:
        print("✅ .env dosyası zaten mevcut")

def main():
    """Ana kurulum fonksiyonu"""
    print("🚀 5651 Log Uygulaması Kurulum Scripti")
    print("=" * 50)
    
    # Python versiyonunu kontrol et
    if not check_python_version():
        sys.exit(1)
    
    # Sanal ortam oluştur
    if not create_virtual_environment():
        sys.exit(1)
    
    # Bağımlılıkları yükle
    if not install_dependencies():
        sys.exit(1)
    
    # Veritabanını hazırla
    if not setup_database():
        sys.exit(1)
    
    # Süper kullanıcı oluştur
    if not create_superuser():
        sys.exit(1)
    
    # Environment dosyası oluştur
    create_env_file()
    
    print("\n" + "=" * 50)
    print("🎉 Kurulum tamamlandı!")
    print("\n📋 Sonraki adımlar:")
    print("1. Sanal ortamı aktifleştirin:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Linux/Mac
        print("   source venv/bin/activate")
    
    print("2. Uygulamayı çalıştırın:")
    print("   cd yasalog")
    print("   python manage.py runserver")
    
    print("\n🌐 Erişim adresleri:")
    print("   - Admin Panel: http://127.0.0.1:8000/admin/")
    print("   - Yönetici Giriş: http://127.0.0.1:8000/yonetici/login/")
    print("   - Kullanıcı Adı: admin")
    print("   - Şifre: admin123")
    
    print("\n📚 Daha fazla bilgi için README.md dosyasını okuyun.")
    print("=" * 50)

if __name__ == "__main__":
    main() 