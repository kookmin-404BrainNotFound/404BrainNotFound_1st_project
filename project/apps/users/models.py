from django.db import models

# Create your models here.
class User(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=128)
    
    def __str__(self):
        return self.email

# 주거 성향.
class UserTendency(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_tendency")
    description = models.JSONField(default=dict)

