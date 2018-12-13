from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Packages(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    tenure_years = models.IntegerField()
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    selected = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
