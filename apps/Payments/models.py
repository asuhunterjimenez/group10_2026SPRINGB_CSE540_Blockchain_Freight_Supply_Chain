from django.contrib.auth.models import User
from django.db import models
from apps.Bookings.models import vehicle, goods, booking_freight_tbl

class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey(
        booking_freight_tbl,
        on_delete=models.CASCADE,
        null=True,
        related_name='booking_id_ref_payment_tbl_fk'
    )
    quote_request_id = models.CharField(max_length=100, null=True)
    session_id = models.CharField(max_length=255)
    transaction_id = models.CharField(max_length=255)  # PaymentIntent ID
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # store base_amount here
    fx_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    settled_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # actual Stripe net
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_email_sent = models.BooleanField(default=False)
    email_retry_count = models.PositiveIntegerField(default=0)
    service_availability=models.CharField(max_length=15,default="Unavailable")
    customer_card_status=models.CharField(max_length=25,default="Card not Charged")


    class Meta:
        db_table = 'Payment'

class blockchain_payment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.CharField(max_length=255)
    quote_request_id = models.CharField(max_length=100, null=True)
    transaction_id = models.CharField(max_length=255)  # PaymentIntent ID
    total_charges = models.DecimalField(max_digits=20, decimal_places=8,null=True)  # Store in Ether (or Wei)
    paid_amount = models.DecimalField(max_digits=20, decimal_places=8,null=True)  # Store in Ether (or Wei)
    balance = models.DecimalField(max_digits=20, decimal_places=8,null=True)  # Store in Ether (or Wei)
    blockchain_gas_fees = models.DecimalField(max_digits=20, decimal_places=8,null=True)  # Store in Ether (or Wei)
    date_created = models.DateTimeField(default=None, null=True)
    class Meta:
        db_table = 'blockchain_payment'
