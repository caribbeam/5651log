import datetime
from django.http import HttpResponse
try:
    import openpyxl
except ImportError:
    openpyxl = None
try:
    from reportlab.pdfgen import canvas
except ImportError:
    canvas = None
import zipfile
import io

def export_as_excel(queryset):
    if not openpyxl:
        return None, "openpyxl yüklü değil!"
    from openpyxl import Workbook
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.append(["TC No", "Ad Soyad", "IP", "MAC", "Giriş Zamanı", "SHA256 Hash"])
    for obj in queryset:
        ws.append([obj.tc_no, obj.ad_soyad, obj.ip_adresi, obj.mac_adresi, obj.giris_zamani.strftime('%Y-%m-%d %H:%M:%S'), obj.sha256_hash])
    wb.save(output)
    output.seek(0)
    return output, None

def export_as_pdf(queryset):
    if not canvas:
        return None, "reportlab yüklü değil!"
    output = io.BytesIO()
    p = canvas.Canvas(output)
    y = 800
    p.setFont("Helvetica", 10)
    p.drawString(30, y, "TC No | Ad Soyad | IP | MAC | Giriş Zamanı | SHA256 Hash")
    y -= 20
    for obj in queryset:
        line = f"{obj.tc_no} | {obj.ad_soyad} | {obj.ip_adresi} | {obj.mac_adresi} | {obj.giris_zamani.strftime('%Y-%m-%d %H:%M:%S')} | {obj.sha256_hash}"
        p.drawString(30, y, line)
        y -= 18
        if y < 40:
            p.showPage()
            y = 800
    p.save()
    output.seek(0)
    return output, None

def export_as_zip(queryset, password=None):
    excel_output, _ = export_as_excel(queryset)
    pdf_output, _ = export_as_pdf(queryset)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('loglar.xlsx', excel_output.getvalue())
        zip_file.writestr('loglar.pdf', pdf_output.getvalue())
    # Şifreli zip için ek kütüphane gerekebilir (ör: pyzipper), burada temel zip örneği var.
    zip_buffer.seek(0)
    return zip_buffer 