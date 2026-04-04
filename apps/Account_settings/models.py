from django.db import models
 
# Create your models here.

""" 
class crm_incomming(models.Model):
    id = models.AutoField(primary_key=True)
    date_received = models.DateField()
    resolution_code = models.CharField(max_length=100)
    sender_number = models.CharField(max_length=50,default='256702222224')
    sender_name = models.CharField(max_length=50)
    message = models.TextField(max_length=300)
    locked_by = models.CharField(max_length=50, default='0')
 """