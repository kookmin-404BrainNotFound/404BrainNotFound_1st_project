from django.db import models

from apps.users.models import User

class Contract(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="contract",
    )
    description = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Photo(id={self.id}, caption={self.caption})'
    

class ContractData(models.Model):
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name="contract_data",
    )
    description = models.JSONField(blank=True, default=dict)
