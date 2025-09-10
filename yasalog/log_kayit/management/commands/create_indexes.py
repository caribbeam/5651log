from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Kritik performans indexlerini oluşturur'

    def handle(self, *args, **options):
        self.stdout.write('Kritik indexler oluşturuluyor...')
        
        # Kritik indexler
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_logkayit_company_created ON log_kayit_logkayit (company_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_logkayit_tc_created ON log_kayit_logkayit (tc_no, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_logkayit_suspicious ON log_kayit_logkayit (suspicious, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_logkayit_ip_created ON log_kayit_logkayit (ip_address, created_at)",
            
            "CREATE INDEX IF NOT EXISTS idx_auditlog_user_time ON audit_logging_auditlog (user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_auditlog_company_time ON audit_logging_auditlog (company_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_auditlog_action_time ON audit_logging_auditlog (action, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_auditlog_severity_time ON audit_logging_auditlog (severity, timestamp)",
            
            "CREATE INDEX IF NOT EXISTS idx_company_slug_active ON log_kayit_company (slug, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_companyuser_user_company ON log_kayit_companyuser (user_id, company_id)",
            
            "CREATE INDEX IF NOT EXISTS idx_alarmevent_company_triggered ON alarm_integration_alarmevent (company_id, triggered_at)",
            "CREATE INDEX IF NOT EXISTS idx_alarmevent_status_triggered ON alarm_integration_alarmevent (status, triggered_at)",
            
            "CREATE INDEX IF NOT EXISTS idx_logflowmonitor_company_created ON log_flow_monitoring_logflowmonitor (company_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_evidencereport_company_created ON evidence_reports_evidencereport (company_id, created_at)",
        ]
        
        with connection.cursor() as cursor:
            for sql in indexes:
                try:
                    cursor.execute(sql)
                    index_name = sql.split('idx_')[1].split(' ')[0]
                    self.stdout.write(f"  ✅ idx_{index_name}")
                except Exception as e:
                    self.stdout.write(f"  ❌ {sql}: {e}")
        
        self.stdout.write(self.style.SUCCESS('✅ Kritik indexler oluşturuldu!'))
