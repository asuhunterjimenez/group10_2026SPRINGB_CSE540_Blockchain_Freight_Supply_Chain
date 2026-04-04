from django.db import models
from django.contrib.auth.models import User
 
# Create your models here.

# class GSA_agreement_form_tbl(models.Model):
#     id = models.AutoField(primary_key=True)
#     date_received = models.DateField()
#     User_id_ref= models.CharField(max_length=100)
#     user_name = models.CharField(max_length=100)
#     sender_number = models.CharField(max_length=50,default='256702222224')
#     sender_name = models.CharField(max_length=50)
#     message = models.TextField(max_length=300)
#     locked_by = models.CharField(max_length=50, default='0')
# Metadata = {
#     'db_table': 'GSA_agreement_form_tbl',
#  }