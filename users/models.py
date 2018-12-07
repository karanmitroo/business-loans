from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from business_loans.settings import SECTORS
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

    Agri = 'Agri'
    Fin = 'Fin'
    Retail = 'Retail'
    Med = 'Med'
    Infra = 'Infra'
    Oth = 'Oth'
    SECTOR_CHOICES = (
        (Agri, SECTORS[0]),
        (Fin, SECTORS[1]),
        (Retail, SECTORS[2]),
        (Med, SECTORS[3]),
        (Infra, SECTORS[4]),
        (Oth,SECTORS[5]),)
    sector = models.CharField(max_length=15, choices=SECTOR_CHOICES, default=Oth)
