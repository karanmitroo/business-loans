from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
# Create your models here.

class UserData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class CompanyData(models.Model):
    business = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.TextField()
    tax_reg_no = models.CharField(max_length=50)
    date_of_registration = models.DateTimeField(auto_now=False, auto_now_add=False)
    revenue = models.IntegerField()
    pan = models.CharField(max_length=10)
    misc_data = JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
