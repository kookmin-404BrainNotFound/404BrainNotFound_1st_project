from django.db import models

# Create your models here.

# 레포트 모델.
class Report(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='running')
    
# 위험도 혹은 적합도 레포트.
class ReportData(models.Model):
    TYPE_CHOICES = [
        ("danger", "Danger"),
        ("fit", "Fit"),
    ]

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE, 
        related_name="report_data"
    )
    score = models.IntegerField(blank=True, default="")
    description = models.TextField(blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default="danger"
    )

    def __str__(self):
        return f"{self.report.id} - {self.type} ({self.score})"
    
