from django.db import models
from apps.report.models import ReportRun

# Create your models here.

class TempAddress(models.Model):
    report_run = models.ForeignKey(ReportRun, on_delete=models.CASCADE, related_name='temp_addresses')

    road_address = models.CharField(max_length=255)
    bd_nm = models.CharField(max_length=100, blank=True, null=True)
    adm_cd = models.CharField(max_length=10, blank=True, null=True)
    sgg_nm = models.CharField(max_length=100, blank=True, null=True)
    mt_yn = models.CharField(max_length=1, default='0')
    lnbr_mnnm = models.CharField(max_length=20, blank=True, null=True)
    lnbr_slno = models.CharField(max_length=20, blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.road_address

class TempPrice(models.Model):
    report_run = models.ForeignKey(ReportRun, on_delete=models.CASCADE, related_name='temp_prices')
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.temp_address.road_address} - {self.price} on {self.date}"
