from django.db import models
from apps.report.models import Report

from external.address.address_manager import AddressManager

# Create your models here.

# 임시로 주소를 저장한다.
class Address(models.Model):
    report = models.OneToOneField(Report, on_delete=models.CASCADE, related_name='address')

    road_address = models.CharField(max_length=255)
    bd_nm = models.CharField(max_length=100, blank=True, null=True)
    adm_cd = models.CharField(max_length=10, blank=True, null=True)
    sgg_nm = models.CharField(max_length=100, blank=True, null=True)
    mt_yn = models.CharField(max_length=1, default='0')
    lnbr_mnnm = models.CharField(max_length=20, blank=True, null=True)
    lnbr_slno = models.CharField(max_length=20, blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    def to_address_manager(self) -> AddressManager:
        return AddressManager(
            roadAddr=self.road_address,
            bdNm=self.bd_nm,
            admCd=self.adm_cd,
            sggNm=self.sgg_nm,
            mtYn=self.mt_yn,
            lnbrMnnm=self.lnbr_mnnm,
            lnbrSlno=self.lnbr_slno,
            details=self.details,
        )
    
    def __str__(self):
        return self.road_address

# 임시로 사용자의 전월세가를 저장한다.
class UserPrice(models.Model):
    report = models.OneToOneField(Report, on_delete=models.CASCADE, related_name='user_price')
    # 전세인가?
    is_year_rent = models.BooleanField(null=False)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

# 평균값 저장 DB
class AvgPrice(models.Model):
    report = models.OneToOneField(Report, on_delete=models.CASCADE, related_name='avg_price')
    avg_year_price = models.FloatField(default=0.0)
    avg_month_security_price = models.FloatField(default=0.0)
    avg_month_rent = models.FloatField(default=0.0)
    
# 건축물대장부 저장.
class BuildingInfo(models.Model):
    report = models.OneToOneField(
        Report,
        on_delete=models.CASCADE,
        related_name="building_info",
    )
    # buildingInfo의 string data.
    description = models.TextField(blank=False, null=False)

# 등기부등본 저장
class PropertyRegistry(models.Model):
    report = models.OneToOneField(
        Report,
        on_delete=models.CASCADE,
        related_name="property_registry",
    )
    pdf = models.FileField(upload_to='files/%Y/%m/%d/')
    created = models.DateTimeField(auto_now_add=True)
    
