from django.db import models

from external.address.address_manager import AddressManager

from apps.users.models import User

# Create your models here.

# 임시로 주소를 저장한다.
class Address(models.Model):
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
    # 전세인가?
    is_year_rent = models.BooleanField(null=False)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

# 평균값 저장 DB
class AvgPrice(models.Model):
    avg_year_price = models.FloatField(default=0.0)
    avg_month_security_price = models.FloatField(default=0.0)
    avg_month_rent = models.FloatField(default=0.0)
    
# 건축물대장부 저장.
class BuildingInfo(models.Model):
    # buildingInfo의 string data.
    description = models.JSONField(default=dict)

# 등기부등본 저장
class PropertyRegistry(models.Model):
    pdf = models.FileField(upload_to='files/%Y/%m/%d/')
    created = models.DateTimeField(auto_now_add=True)
    
# 공기질 데이터 저장.
# 등기부등본 저장
class AirCondition(models.Model):
    data = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

# 침수 데이터 저장.
class Flood(models.Model):
    data = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

# 공통 묶음: 같은 주소/시세/건물정보를 한 덩어리로
class PropertyBundle(models.Model):
    address = models.OneToOneField(Address, on_delete=models.PROTECT, related_name='bundle',
                                   null=True, blank=True)
    avg_price = models.OneToOneField(AvgPrice, on_delete=models.PROTECT, related_name='bundle',
                                     null=True, blank=True)
    building_info = models.OneToOneField(BuildingInfo, on_delete=models.PROTECT, related_name='bundle',
                                         null=True, blank=True)
    user_price = models.OneToOneField(UserPrice, on_delete=models.PROTECT, related_name='bundle',
                                      null=True, blank=True)
    property_registry = models.OneToOneField(PropertyRegistry, on_delete=models.PROTECT, related_name='bundle',
                                             null=True, blank=True)
    air_condition = models.OneToOneField(AirCondition, on_delete=models.PROTECT, related_name='bundle',
                                         null=True, blank=True)

    flood = models.OneToOneField(Flood, on_delete=models.PROTECT, related_name='bundle',
                                         null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bundles')
    created = models.DateTimeField(auto_now_add=True)