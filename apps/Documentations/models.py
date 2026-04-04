from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class credit_application(models.Model):
    id=models.AutoField(primary_key=True)
    date_received=models.DateField(auto_now=True)
    username=models.ForeignKey(User,on_delete=models.CASCADE,related_name="credit_app_user")
    legal_trading_name=models.CharField(max_length=100,null=False,blank=False)
    operating_as=models.CharField(max_length=100,default="N/a")
    business_location=models.CharField(max_length=100,null=False,blank=False)
    telephone=models.CharField(max_length=12,null=False,blank=False)
    length_in_business=models.CharField(max_length=30,default="Less than 1 Year")
    type_of_business=models.CharField(max_length=100,null=False,blank=False)
    bank_name=models.CharField(max_length=100,null=False,blank=False)
    account_number=models.CharField(max_length=30,null=False,blank=False)
    bank_address=models.CharField(max_length=200,null=False,blank=False)
    bank_fax=models.CharField(max_length=30,default="N/a")
    importer=models.CharField(max_length=30,default="N/a")
    class Meta:
            db_table = "credit_application"

#Credit References table
class credit_references(models.Model):
    id =models.AutoField(primary_key=True)
    date_received=models.DateField(auto_now=True)
    id_reference_cred_app_table=models.ForeignKey(credit_application,on_delete=models.CASCADE,related_name="id_reference_credit_app_table")
    referee_name=models.CharField(max_length=30,null=False,blank=False)
    referee_address=models.CharField(max_length=200,null=False,blank=False)
    referee_phone=models.CharField(max_length=30,null=False,blank=False)
    class Meta:
          db_table="credit_references"

#address of  owner(s) officer(s)
class address_of_owner_officer(models.Model):
    id=models.AutoField(primary_key=True)
    date_received=models.DateField(auto_now=True)
    id_reference_cred_app_table=models.ForeignKey(credit_application,on_delete=models.CASCADE,related_name="id_address_owner_credit_app_table")
    owner_name=models.CharField(max_length=50,default="N/a")
    owner_title=models.CharField(max_length=50,null=False,blank=False)
    owner_address=models.CharField(max_length=200)
    owner_phone=models.CharField(max_length=30)
    class Meta:
          db_table="address_of_owner_officer"
