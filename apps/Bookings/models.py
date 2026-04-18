from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Booking Freight Table
class booking_freight_tbl(models.Model):
    id = models.AutoField(primary_key=True)
    date_received = models.DateField()
    time_received = models.TimeField()
    service_type = models.CharField(max_length=50)  # Ocean Freight, Air Freight, RORO, Brokerage
    
    # 🔹 Generic relation to any quote type
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    quote_request = GenericForeignKey('content_type', 'object_id')

    # Reference to GSA table
    gsa_id_ref = models.ForeignKey(
        'Login.GSA_agreement_form_tbl',
        on_delete=models.CASCADE,
        related_name='booking_freight_gsa_by_id'
    )

    # Other fields
    shipper_export_number = models.TextField(max_length=300, default="N/A")
    receiver_company_name = models.CharField(max_length=100)
    receiver_fullname = models.CharField(max_length=100)
    receiver_phone_number = models.CharField(max_length=30)
    receiver_email = models.CharField(max_length=100)
    receiver_tax_id = models.CharField(max_length=50, default="N/A")
    receiver_driver_lincence_number = models.CharField(max_length=50, default="N/A")
    receiver_passport_no = models.CharField(max_length=50, default="N/A")
    receiver_address = models.TextField(max_length=300)
    desired_type_of_release = models.CharField(max_length=100)
    booking_reference_number = models.CharField(max_length=50, default='N/A')
    quote_reference_number = models.CharField(max_length=50, default='N/A')
    container_number = models.CharField(max_length=50, default='N/A')
    vessel_number = models.CharField(max_length=10, default='N/A')
    hs_code = models.CharField(max_length=20, default='N/A')
    cers = models.IntegerField(default=0)
    comments = models.TextField(max_length=300, default='N/A')
    updated_by = models.CharField(max_length=50, default='0')
    updated_date_time = models.DateTimeField(auto_now=True)
    request_status = models.CharField(max_length=20, default='Pending')
    locked_by = models.CharField(max_length=50, default='0')
    blockchain_tx_receipt=models.CharField(max_length=100, default='0')

    class Meta:
        db_table = 'booking_freight_tbl'


# Vehicle Model (can remain tied to ocean_freight_tbl or adjust similarly)
class vehicle(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id_ref = models.ForeignKey(
        'Bookings.booking_freight_tbl',
        on_delete=models.CASCADE,
        related_name='vehicle_booking_id_ref'
    )
    # Generic relation to any quote request
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    quote_request = models.CharField(max_length=50, blank=True, null=True)

    gsa_id_ref = models.ForeignKey(
        'Login.GSA_agreement_form_tbl',
        on_delete=models.CASCADE,
        related_name='vehicle_gsa_by_id'
    )
    vehicle_year = models.CharField(max_length=4)
    vehicle_make = models.CharField(max_length=100)
    vehicle_vin = models.CharField(max_length=100, unique=True)
    vehicle_cost_in_CAD = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    vehicle_color = models.CharField(max_length=50)

    class Meta:
        db_table = 'vehicle'

# Goods Model
class goods(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id_ref = models.ForeignKey(
        'Bookings.booking_freight_tbl',
        on_delete=models.CASCADE,
        related_name='goods_booking_id_ref'
    )
    gsa_id_ref = models.ForeignKey(
        'Login.GSA_agreement_form_tbl',
        on_delete=models.CASCADE,
        related_name='goods_gsa_by_id'
    )
    goods_quantity = models.IntegerField(default=1)
    goods_description = models.CharField(max_length=255)
    goods_value_in_CAD = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    # 🔹 Generic relation to any quote type
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    quote_request = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'goods'
