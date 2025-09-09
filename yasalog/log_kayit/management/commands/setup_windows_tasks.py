"""
Windows Task Scheduler Kurulum Komutu
Otomatik zaman damgası imzalama için Windows görevleri oluşturur
"""

from django.core.management.base import BaseCommand
import os
import subprocess
import sys
from pathlib import Path

class Command(BaseCommand):
    help = 'Windows Task Scheduler için otomatik imzalama görevleri oluşturur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create',
            action='store_true',
            help='Windows görevlerini oluştur',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Windows görevlerini sil',
        )

    def handle(self, *args, **options):
        if options['create']:
            self.create_tasks()
        elif options['delete']:
            self.delete_tasks()
        else:
            self.show_help()

    def create_tasks(self):
        """Windows Task Scheduler görevlerini oluşturur"""
        self.stdout.write(
            self.style.SUCCESS('Windows Task Scheduler görevleri oluşturuluyor...')
        )
        
        # Proje yollarını al
        project_path = Path(__file__).resolve().parent.parent.parent.parent
        manage_py = project_path / 'yasalog' / 'manage.py'
        python_exe = sys.executable
        
        # Her 5 dakikada bir çalışacak görev
        task_name = "5651Log_AutoTimestamp"
        task_description = "5651 Loglama Sistemi - Otomatik Zaman Damgası İmzalama"
        
        # XML görev tanımı
        task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{task_description}</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT5M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2025-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>"{manage_py}" auto_timestamp</Arguments>
      <WorkingDirectory>{project_path / 'yasalog'}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
        
        # Geçici XML dosyası oluştur
        xml_file = project_path / 'temp_task.xml'
        try:
            with open(xml_file, 'w', encoding='utf-16') as f:
                f.write(task_xml)
            
            # Görevi oluştur
            cmd = f'schtasks /Create /TN "{task_name}" /XML "{xml_file}" /F'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Windows görevi başarıyla oluşturuldu: {task_name}')
                )
                self.stdout.write(
                    self.style.SUCCESS('📅 Görev her 5 dakikada bir otomatik olarak çalışacak')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Görev oluşturma hatası: {result.stderr}')
                )
            
            # Geçici dosyayı sil
            xml_file.unlink()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Görev oluşturma hatası: {str(e)}')
            )
            if xml_file.exists():
                xml_file.unlink()

    def delete_tasks(self):
        """Windows Task Scheduler görevlerini siler"""
        self.stdout.write(
            self.style.WARNING('Windows Task Scheduler görevleri siliniyor...')
        )
        
        task_name = "5651Log_AutoTimestamp"
        cmd = f'schtasks /Delete /TN "{task_name}" /F'
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Windows görevi başarıyla silindi: {task_name}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Görev silme hatası: {result.stderr}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Görev silme hatası: {str(e)}')
            )

    def show_help(self):
        """Yardım mesajını gösterir"""
        self.stdout.write(
            self.style.SUCCESS('Windows Task Scheduler Kurulum Komutu')
        )
        self.stdout.write('')
        self.stdout.write('Kullanım:')
        self.stdout.write('  python manage.py setup_windows_tasks --create    # Görevleri oluştur')
        self.stdout.write('  python manage.py setup_windows_tasks --delete    # Görevleri sil')
        self.stdout.write('')
        self.stdout.write('Bu komut Windows Task Scheduler kullanarak otomatik zaman damgası')
        self.stdout.write('imzalama görevlerini oluşturur veya siler.')
        self.stdout.write('')
        self.stdout.write('Not: Bu komut sadece Windows işletim sisteminde çalışır.')
