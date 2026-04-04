from django.contrib.auth.models import User
from django.db import models
from apps.Bookings.models import vehicle,goods
import os


# Create your models here.
#onboarding
class onboarding(models.Model):
    id=models.AutoField(primary_key=True)
    date_signed=models.CharField(max_length=35)
    time_signed=models.CharField(max_length=35)
    username=models.CharField(max_length=35,unique=True,null=False,default="default_username")
    gsa_signed=models.CharField(max_length=4,default='No')
    gsa_signed_date_time=models.DateTimeField(auto_now=True)
    loi_signed=models.CharField(max_length=4,default='No')
    loi_signed_date_time=models.DateTimeField(auto_now=True)
    credits_application_signed=models.CharField(max_length=4,default='No')
    credits_application_signed_date_time=models.DateTimeField(auto_now=True)
    class Meta:
        db_table='onboarding' 
#After creationof a new quoting table, delete the below new_quoting model
#new_quotings model
class new_quotings(models.Model):
    id = models.AutoField(primary_key=True)
    date_received = models.CharField(max_length=35)
    time_received = models.CharField(max_length=35)
    request_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=50, default='Guest')
    shipper_company_name = models.CharField(max_length=100, default='No Company')
    shipper_fullname = models.CharField(max_length=100, default='Guest')
    shipper_phone_number = models.CharField(max_length=50)
    shipper_email = models.EmailField(max_length=100)
    shipper_export_number = models.CharField(max_length=50, default='No Export Number')
    shipper_address = models.CharField(max_length=255)
    receiver_company_name = models.CharField(max_length=100, default='No Company')
    receiver_fullname = models.CharField(max_length=100)
    receiver_phone_number = models.CharField(max_length=50)
    receiver_email = models.EmailField(max_length=100,null=True, blank=True)
    receiver_tax_id = models.CharField(max_length=50, default='N/A')
    receiver_driver_lincence = models.CharField(max_length=50, default='N/A')
    receiver_passport_no = models.CharField(max_length=50, default='N/A')
    receiver_address = models.CharField(max_length=255)
    shipment_date = models.CharField(max_length=35)
    shipment_type = models.CharField(max_length=50)
    shipment_weight = models.DecimalField(max_digits=10, decimal_places=2)
    shipment_dimensions = models.CharField(max_length=100)
    resolution_code = models.CharField(max_length=35, default='Open')
    resolution_date = models.DateField(null=True, blank=True)
    resolution_time = models.TimeField(null=True, blank=True)
    convert_to_booking = models.CharField(max_length=7, default='False')
    message = models.TextField(max_length=300)
    locked_by = models.CharField(max_length=50, default='0')
    class Meta:
        db_table = 'new_quotings'

# Sea Additional Info Model
class sea_additional_info(models.Model):
    id = models.AutoField(primary_key=True)

    # One reference to 'id' of new_quotings
    #id_quoting_ref =models.CharField(max_length=255)
    id_quoting_ref = models.ForeignKey(new_quotings, on_delete=models.CASCADE, related_name='sea_info_by_id')
    # Another reference to 'request_id' of new_quotings
    booking_ref = models.CharField(max_length=255)
    
    place_of_receipt = models.CharField(max_length=255, default='N/A')
    port_of_loading = models.CharField(max_length=255, default='N/A')
    seal_number = models.CharField(max_length=100, default='N/A')
    container_number = models.CharField(max_length=100, default='N/A')
    vessel_number = models.CharField(max_length=100, default='N/A')
    port_of_discharge = models.CharField(max_length=255, default='N/A')
    cargo_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    desired_type_of_release = models.CharField(max_length=50, default='N/A')
    hs_code = models.CharField(max_length=50, default='N/A')
    cers = models.CharField(max_length=50, default='N/A')

    class Meta:
        db_table = 'sea_additional_info'


# GSA Agreement Form Model
# GSA_agreement_form_tbl reference to 1:many(ocean_freight_tbl,air_freight_tbl,customs_brokerage_tbl,roro_tbl)--relationship 
class GSA_agreement_form_tbl(models.Model):
    id = models.AutoField(primary_key=True)
    date_received = models.DateField()

    # Reference to User table
    user_id_ref = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, editable=False,unique=True)
    # Other fields
    customer_registered_business_name = models.CharField(max_length=100, default='N/A')
    corp_jur_number = models.CharField(max_length=50)
    service_address = models.TextField(max_length=300)
    billing_address = models.TextField(max_length=300)
    GST_HST = models.CharField(max_length=100)
    business_form = models.CharField(max_length=50)
    auth_contact_number = models.CharField(max_length=50)
    telephone_number = models.CharField(max_length=100)
    fax_number = models.CharField(max_length=100, default='N/A')
    email_address = models.EmailField(max_length=100)
    bank_name = models.CharField(max_length=100, default='N/A')
    branch_id = models.CharField(max_length=100, default='N/A')
    bank_address = models.TextField(max_length=300, default='N/A')
    bank_account_number = models.CharField(max_length=100, default='N/A')
    title = models.CharField(max_length=50)
    locked_by = models.CharField(max_length=50, default='0')

    class Meta:
        db_table = 'GSA_agreement_form_tbl'

# Quoting details - Ocean Freight Model
class ocean_freight_tbl(models.Model):
    id = models.AutoField(primary_key=True)
    request_id = models.CharField(max_length=100, unique=True)
    date_received = models.DateField()
    time_received = models.TimeField()

    # Reference to GSA table
    id_gsa_ref = models.ForeignKey(GSA_agreement_form_tbl, on_delete=models.CASCADE, related_name='ocean_freight_by_id')

    # Other fields
    place_of_receipt = models.TextField(max_length=300 , default="Unknown")
    port_of_loading = models.TextField(max_length=300 , default="Unknown")
    country_of_loading = models.TextField(max_length=70 , default="Unknown")
    port_of_discharge = models.TextField(max_length=300 , default="Unknown")
    country_of_discharge = models.TextField(max_length=70 ,default="Unknown")
    tracking=models.CharField(max_length=10, default="No")
    door_delivery_address=models.CharField(max_length=300, default="N/A")
    hazardous=models.CharField(max_length=5,default="No")
    equipment_size = models.CharField(max_length=10)
    estimated_shipping_date = models.CharField(max_length=30)
    commodity_cat=models.CharField(max_length=100, null=True, blank=True)
    commodity_sub=models.CharField(max_length=100 ,null=True, blank=True)
    additional_info = models.TextField(max_length=300)
    # fields for charges,handled by sales/finance team
    currency_type = models.CharField(max_length=10, default='CAD')# choose from CAD, USD, EUR, etc.
    freight_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    #door_delivery_charges=models.DecimalField(max_digits=10, decimal_places=2, default=0.00)#if yes is chosen
    fuel_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    customs_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    validity_date = models.CharField(max_length=30)
    comments = models.TextField(max_length=300, default='N/A')
    updated_by = models.CharField(max_length=50, default='0')
    updated_date_time = models.DateTimeField(auto_now=True)
    # end of charges fields
    ''' Status can be Draft (drafted by customer), Responded To(sent from sales/finance team),
    Approved,Rejected(approved or rejected by customer), Expired (if not approved within validity date)
    '''
    request_status = models.CharField(max_length=20, default='Draft') # Draft, Responded To, Approved, Rejected,Expired
    locked_by = models.CharField(max_length=50, default='0')

    class Meta:
        db_table = 'ocean_freight_tbl'

#quoting details - Air Freight Model
class air_freight_tbl(models.Model):
    id = models.AutoField(primary_key=True)
    request_id = models.CharField(max_length=100, unique=True)
    date_received = models.DateField()
    time_received = models.TimeField()

    # Reference to GSA table
    id_gsa_ref = models.ForeignKey(GSA_agreement_form_tbl, on_delete=models.CASCADE, related_name='air_freight_by_id')

    # Other fields
    place_of_receipt = models.TextField(max_length=300 ,default="Unknown")
    departure = models.TextField(max_length=300 ,default="Unknown")
    country_of_departure = models.TextField(max_length=70 ,default="Unknown")
    destination = models.TextField(max_length=300 ,default="Unknown")
    country_of_destination = models.TextField(max_length=70 ,default="Unknown")
    tracking=models.CharField(max_length=10, default="No")
    door_delivery_address=models.CharField(max_length=300, default="N/A")
    hazardous=models.CharField(max_length=5,default="No")
    estimated_shipping_date = models.CharField(max_length=30)
    additional_info = models.TextField(max_length=300)
    commodity_cat=models.CharField(max_length=100 , null=True, blank=True)
    commodity_sub=models.CharField(max_length=100 , null=True, blank=True)
    #units measurement can be in kg,lbs,centimeters,inches
    number_of_units = models.IntegerField(default=1)
    length = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    width = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    height = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unit_of_measurement_L_W_H = models.CharField(max_length=15, default='Centimeters') # Inches or Centimeters
    unit_of_measurement_weight = models.CharField(max_length=10, default='Kgs') # Kgs or Lbs
    # fields for charges,handled by sales/finance team
    currency_type = models.CharField(max_length=10, default='CAD')# choose from CAD, USD, EUR, etc.
    freight_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    #door_delivery_charges=models.DecimalField(max_digits=10, decimal_places=2, default=0.00)#if yes is chosen
    fuel_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    customs_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if 
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    validity_date = models.CharField(max_length=30)
    comments = models.TextField(max_length=300, default='N/A')
    updated_by = models.CharField(max_length=50, default='0')
    updated_date_time = models.DateTimeField(auto_now=True)
    # end of charges 
    ''' Status can be Draft (drafted by customer), Sent(sent from sales/finance team),
    Approved,Rejected(approved or rejected by customer), Expired (if not approved within validity date)
    '''
    request_status = models.CharField(max_length=20, default='Draft') # Draft, Sent, Approved, Rejected,Expired
    locked_by = models.CharField(max_length=50, default='0')

    class Meta:
        db_table = 'air_freight_tbl'

# customs brokerage table model
class customs_brokerage_tbl(models.Model):
    id = models.AutoField(primary_key=True)
    request_id = models.CharField(max_length=100, unique=True)
    date_received = models.DateField()
    time_received = models.TimeField()

    # Reference to GSA table
    id_gsa_ref = models.ForeignKey(GSA_agreement_form_tbl, on_delete=models.CASCADE, related_name='customs_brokerage_by_id')

    # Other fields
    place_of_receipt = models.TextField(max_length=300 ,default="Unknown")
    port_of_loading = models.TextField(max_length=300 ,default="Unknown")
    country_of_loading = models.TextField(max_length=70 ,default="Unknown")
    port_of_discharge = models.TextField(max_length=300 ,default="Unknown")
    country_of_discharge = models.TextField(max_length=70 ,default="Unknown")
    tracking=models.CharField(max_length=10, default="No")
    door_delivery_address=models.CharField(max_length=300, default="N/A")
    hazardous=models.CharField(max_length=5,default="No")
    estimated_shipping_date = models.CharField(max_length=30)
    commodity_cat=models.CharField(max_length=100,null=True, blank=True)
    commodity_sub=models.CharField(max_length=100 , null=True, blank=True)
    # invoice_packing_list_upload = models.CharField(max_length=100, null=True, blank=True)# will create a file upload field later
    additional_info = models.TextField(max_length=300)
    # fields for charges,handled by sales/finance team
    currency_type = models.CharField(max_length=10, default='CAD')# choose from CAD, USD, EUR, etc.
    brokerage_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    #door_delivery_charges=models.DecimalField(max_digits=10, decimal_places=2, default=0.00)#if yes is chosen
    customs_duties = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    validity_date = models.CharField(max_length=30)
    comments = models.TextField(max_length=300, default='N/A')
    updated_by = models.CharField(max_length=50, default='0')
    updated_date_time = models.DateTimeField(auto_now=True)
    # end of charges fields
    ''' Status can be Draft (drafted by customer), Sent(sent from sales/finance team),
    Approved,Rejected(approved or rejected by customer), Expired (if not approved within validity date)
    '''
    release_status = models.CharField(max_length=20, choices=[("Pending","Pending"),("Released","Released"),("On Hold","On Hold")], default="Pending")
    request_status = models.CharField(max_length=20, default='Draft') # Draft, Sent, Approved, Rejected,Expired
    release_date = models.DateField(blank=True, null=True)
    locked_by = models.CharField(max_length=50, default='0')

    class Meta:
        db_table = 'customs_brokerage_tbl'

#file upload in customs_brokerage
def upload_to_request(instance, filename):
    request_id_val = str(instance.brokerage.request_id) + str(instance.brokerage.id)
    return os.path.join("customs_brokerage", request_id_val, filename)

class CustomsBrokerageFile(models.Model):
    brokerage = models.ForeignKey(
        'customs_brokerage_tbl',
        on_delete=models.CASCADE,
        related_name='files'
    )
    file = models.FileField(upload_to=upload_to_request)

    class Meta:
        db_table = 'CustomsBrokerageFile'

# RORO Model
class roro_tbl(models.Model):
    id = models.AutoField(primary_key=True)
    request_id = models.CharField(max_length=100, unique=True)
    date_received = models.DateField()
    time_received = models.TimeField()

    # Reference to GSA table
    id_gsa_ref = models.ForeignKey(GSA_agreement_form_tbl, on_delete=models.CASCADE, related_name='roro_by_id')

    # Other fields
    vehicle_pickup_address = models.TextField(max_length=300)
    vehicle_delivery_address = models.TextField(max_length=300)
    tracking=models.CharField(max_length=10, default="No")
    door_delivery_address=models.CharField(max_length=300, default="N/A")
    hazardous=models.CharField(max_length=5,default="No")
    estimated_shipping_date = models.CharField(max_length=30)
    additional_info = models.TextField(max_length=300)
    commodity_cat=models.CharField(max_length=100,null=True, blank=True)
    commodity_sub=models.CharField(max_length=100 , null=True, blank=True)
    #units measurement can be in kg,lbs,centimeters,inches
    unit_of_measurement_L_W_H = models.CharField(max_length=15, default='Centimeters') # Inches or Centimeters
    unit_of_measurement_weight = models.CharField(max_length=10, default='Kgs') # Kgs or Lbs
    number_of_units = models.IntegerField(default=1)
    length = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    width = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    height = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # fields for charges,handled by sales/finance team
    currency_type = models.CharField(max_length=10, default='CAD')# choose from CAD, USD, EUR, etc.
    freight_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    #door_delivery_charges=models.DecimalField(max_digits=10, decimal_places=2, default=0.00)#if yes is chosen
    fuel_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    customs_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if 
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # if any
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    validity_date = models.CharField(max_length=30)
    comments = models.TextField(max_length=300, default='N/A')
    updated_by = models.CharField(max_length=50, default='0')
    updated_date_time = models.DateTimeField(auto_now=True)
    # end of charges fields
    ''' Status can be Draft (drafted by customer), Sent(sent from sales/finance team),
    Approved,Rejected(approved or rejected by customer), Expired (if not approved within validity date)
    '''
    request_status = models.CharField(max_length=20, default='Draft') # Draft, Sent, Approved, Rejected,Expired
    locked_by = models.CharField(max_length=50, default='0')

    class Meta:
        db_table = 'roro_tbl'





