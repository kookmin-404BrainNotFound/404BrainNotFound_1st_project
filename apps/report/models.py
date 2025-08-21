from django.db import models

# Create your models here.

class Report(models.Model):
    pass

# 레포트 전 단계들을 임시 저장하기 위해 필요한 모델.
class ReportRun(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='running')

# 위험도 체크리스트
class DangerCheckList(models.Model):
    report_run = models.ForeignKey(ReportRun, on_delete=models.CASCADE, related_name='danger_checklists')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

