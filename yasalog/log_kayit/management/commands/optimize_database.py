from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Database optimizasyonu yapar - indexler, query analizi, performans iyileştirmeleri'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Sadece analiz yap, değişiklik yapma',
        )
        parser.add_argument(
            '--create-indexes',
            action='store_true',
            help='Eksik indexleri oluştur',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Database Optimizasyonu Başlatılıyor...'))
        
        if options['analyze']:
            self.analyze_database()
        
        if options['create_indexes']:
            self.create_missing_indexes()
        
        # Genel optimizasyonlar
        self.optimize_queries()
        self.vacuum_analyze()
        
        self.stdout.write(self.style.SUCCESS('✅ Database optimizasyonu tamamlandı!'))

    def analyze_database(self):
        """Database analizi yap"""
        self.stdout.write('\n📊 Database Analizi...')
        
        with connection.cursor() as cursor:
            # Tablo boyutları
            self.stdout.write('\n📋 Tablo Boyutları:')
            cursor.execute("""
                SELECT name
                FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
            """)
            
            for table_name, in cursor.fetchall():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"  {table_name}: {count:,} kayıt")
                except:
                    pass
            
            # Index bilgileri
            self.stdout.write('\n🔍 Mevcut Indexler:')
            cursor.execute("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type='index' 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            """)
            
            current_table = None
            for index_name, table_name, sql in cursor.fetchall():
                if table_name != current_table:
                    self.stdout.write(f"\n  📊 {table_name}:")
                    current_table = table_name
                self.stdout.write(f"    - {index_name}")

    def create_missing_indexes(self):
        """Eksik indexleri oluştur"""
        self.stdout.write('\n🔧 Kritik Indexler Oluşturuluyor...')
        
        # Önemli indexler
        indexes = [
            # LogKayit tablosu - en kritik
            ("log_kayit_logkayit_company_created", "log_kayit_logkayit", ["company_id", "created_at"]),
            ("log_kayit_logkayit_tc_created", "log_kayit_logkayit", ["tc_no", "created_at"]),
            ("log_kayit_logkayit_suspicious", "log_kayit_logkayit", ["suspicious", "created_at"]),
            ("log_kayit_logkayit_ip_created", "log_kayit_logkayit", ["ip_address", "created_at"]),
            
            # AuditLog tablosu
            ("audit_logging_auditlog_user_time", "audit_logging_auditlog", ["user_id", "timestamp"]),
            ("audit_logging_auditlog_company_time", "audit_logging_auditlog", ["company_id", "timestamp"]),
            ("audit_logging_auditlog_action_time", "audit_logging_auditlog", ["action", "timestamp"]),
            ("audit_logging_auditlog_severity_time", "audit_logging_auditlog", ["severity", "timestamp"]),
            
            # Company tablosu
            ("log_kayit_company_slug_active", "log_kayit_company", ["slug", "is_active"]),
            
            # CompanyUser tablosu
            ("log_kayit_companyuser_user_company", "log_kayit_companyuser", ["user_id", "company_id"]),
            
            # AlarmEvent tablosu
            ("alarm_integration_alarmevent_company_triggered", "alarm_integration_alarmevent", ["company_id", "triggered_at"]),
            ("alarm_integration_alarmevent_status_triggered", "alarm_integration_alarmevent", ["status", "triggered_at"]),
            
            # LogFlowMonitor tablosu
            ("log_flow_monitoring_logflowmonitor_company_created", "log_flow_monitoring_logflowmonitor", ["company_id", "created_at"]),
            
            # EvidenceReport tablosu
            ("evidence_reports_evidencereport_company_created", "evidence_reports_evidencereport", ["company_id", "created_at"]),
        ]
        
        with connection.cursor() as cursor:
            for index_name, table_name, columns in indexes:
                try:
                    # Index var mı kontrol et
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                        (index_name,)
                    )
                    
                    if not cursor.fetchone():
                        # Index oluştur
                        columns_str = ', '.join(columns)
                        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
                        cursor.execute(sql)
                        self.stdout.write(f"  ✅ {index_name} oluşturuldu")
                    else:
                        self.stdout.write(f"  ⚪ {index_name} zaten mevcut")
                        
                except Exception as e:
                    self.stdout.write(f"  ❌ {index_name} oluşturulamadı: {e}")

    def optimize_queries(self):
        """Query optimizasyonları"""
        self.stdout.write('\n⚡ Query Optimizasyonları...')
        
        with connection.cursor() as cursor:
            # SQLite optimizasyonları
            optimizations = [
                ("PRAGMA optimize", "Query planner optimizasyonu"),
                ("PRAGMA analysis_limit=1000", "Analiz limiti ayarı"),
                ("PRAGMA cache_size=10000", "Cache boyutu artırma"),
                ("PRAGMA temp_store=MEMORY", "Geçici veriler için RAM kullanımı"),
                ("PRAGMA journal_mode=WAL", "Write-Ahead Logging aktif"),
                ("PRAGMA synchronous=NORMAL", "Sync modu optimizasyonu"),
                ("PRAGMA mmap_size=268435456", "Memory-mapped I/O (256MB)"),
            ]
            
            for sql, description in optimizations:
                try:
                    cursor.execute(sql)
                    self.stdout.write(f"  ✅ {description}")
                except Exception as e:
                    self.stdout.write(f"  ❌ {description}: {e}")

    def vacuum_analyze(self):
        """VACUUM ve ANALYZE işlemleri"""
        self.stdout.write('\n🧹 Database Temizleme ve Analiz...')
        
        with connection.cursor() as cursor:
            try:
                # VACUUM - database dosyasını optimize et
                cursor.execute("VACUUM")
                self.stdout.write("  ✅ VACUUM tamamlandı")
                
                # ANALYZE - istatistikleri güncelle
                cursor.execute("ANALYZE")
                self.stdout.write("  ✅ ANALYZE tamamlandı")
                
            except Exception as e:
                self.stdout.write(f"  ❌ Temizleme hatası: {e}")

    def show_performance_tips(self):
        """Performans ipuçları göster"""
        self.stdout.write('\n💡 Performans İpuçları:')
        
        tips = [
            "1. select_related() kullanarak N+1 query problemini önleyin",
            "2. prefetch_related() ile many-to-many ilişkileri optimize edin",
            "3. only() ve defer() ile gereksiz field'ları yüklemeyin",
            "4. Cache sistemi ile sık kullanılan verileri önbelleğe alın",
            "5. Database connection pooling kullanın",
            "6. Büyük dataset'ler için pagination kullanın",
            "7. Raw SQL sadece gerektiğinde kullanın",
            "8. Bulk operations için bulk_create() ve bulk_update() kullanın",
        ]
        
        for tip in tips:
            self.stdout.write(f"  {tip}")
        
        self.stdout.write('\n📈 Monitoring:')
        monitoring = [
            "- django-debug-toolbar ile query'leri izleyin",
            "- django.db.backends logger ile SQL query'leri logla",
            "- Connection pool monitoring ekleyin",
            "- Slow query detection kurun",
        ]
        
        for item in monitoring:
            self.stdout.write(f"  {item}")
