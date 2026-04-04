from django.contrib.auth.decorators import login_required
from apps.Helpers.decorators import group_required
from django.shortcuts import render, redirect
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from apps.Login.models import (
    GSA_agreement_form_tbl,
    ocean_freight_tbl,
    air_freight_tbl,
    roro_tbl,
    customs_brokerage_tbl
)
from apps.Bookings.models import booking_freight_tbl, vehicle, goods
from django.contrib.contenttypes.models import ContentType
import json
import datetime

class BookingsView:

    @staticmethod
    @login_required
    @group_required(['clients_team','finance_team','sales_team'])
    def make_booking(request, request_id):
        user = request.user
        username = user.username
        user_email = user.email
        user_fullname = f"{user.first_name} {user.last_name}"

        #Fetch any quote type
        quote_request = None
        quote_model = None
        for model in [ocean_freight_tbl, air_freight_tbl, customs_brokerage_tbl, roro_tbl]:
            try:
                quote_request = model.objects.get(request_id=request_id)
                quote_model = model  # model type for GenericForeignKey
                break
            except model.DoesNotExist:
                continue

        if not quote_request:
            messages.error(request, "Quote request not found.")
            return redirect('quoting')

        # Fetch GSA agreement if linked
        gsa_agreement = getattr(quote_request, 'id_gsa_ref', None)

        if request.method == 'POST':
            quote_reference_number = request.POST.get('quote_request_id', 'N/A').strip()

            try:
                #Create booking using GenericForeignKey
                booking = booking_freight_tbl.objects.create(
                    date_received=datetime.date.today(),
                    time_received=datetime.datetime.now().time(),
                    service_type=request.POST.get('service_type', 'N/A').strip(),
                    content_type=ContentType.objects.get_for_model(quote_model),
                    object_id=quote_request.id, 
                    gsa_id_ref=gsa_agreement,
                    quote_reference_number=quote_reference_number,
                    shipper_export_number=request.POST.get('shipper_export_number', 'N/A').strip(),
                    receiver_company_name=request.POST['receiver_company_name'].strip(),
                    receiver_fullname=request.POST['receiver_fullname'].strip(),
                    receiver_phone_number=request.POST['receiver_phone_number'].strip(),
                    receiver_email=request.POST['receiver_email'],
                    receiver_tax_id=request.POST.get('receiver_tax_id', 'N/A').strip(),
                    receiver_driver_lincence_number=request.POST.get('receiver_driver_lincence_number', 'N/A').strip(),
                    receiver_passport_no=request.POST.get('receiver_passport_no', 'N/A').upper().strip(),
                    receiver_address=request.POST['receiver_address'].strip(),
                    desired_type_of_release='N/A',
                    booking_reference_number=request.POST.get('booking_reference_number', 'N/A').upper().strip(),
                    container_number=request.POST.get('container_number', 'N/A').strip(),
                    vessel_number=request.POST.get('vessel_number', 'N/A').strip(),
                )

                # Handle vehicles
                if getattr(quote_request, 'commodity_sub', '') == 'Vehicles':
                    vehicle_makes = [m.strip().upper() for m in request.POST.getlist('vehicle_make[]')]
                    vehicle_years = [y.strip() for y in request.POST.getlist('vehicle_year[]')]
                    vehicle_vins = [v.strip().upper() for v in request.POST.getlist('vehicle_vin[]')]
                    vehicle_costs = request.POST.getlist('vehicle_cost_in_CAD[]')
                    vehicle_colors = [c.strip().upper() for c in request.POST.getlist('vehicle_color[]')]

                    for make, year, vin, cost, color in zip(vehicle_makes, vehicle_years, vehicle_vins, vehicle_costs, vehicle_colors):
                        if make and year and vin and cost and color:
                            # Remove commas and convert to Decimal
                            try:
                                cleaned_cost = Decimal(cost.replace(',', '').strip())
                            except InvalidOperation:
                                cleaned_cost = Decimal(0)

                            vehicle.objects.create(
                                booking_id_ref=booking,
                                content_type=ContentType.objects.get_for_model(quote_request),
                                object_id=quote_request.id,
                                gsa_id_ref=gsa_agreement,
                                vehicle_year=year,
                                vehicle_make=make,
                                vehicle_vin=vin,
                                vehicle_cost_in_CAD=cleaned_cost,
                                vehicle_color=color
                            )

                # Handle goods
                else:
                    goods_descriptions = [d.strip().upper() for d in request.POST.getlist('goods_description[]')]
                    goods_qtys = request.POST.getlist('goods_qty[]')
                    goods_values = request.POST.getlist('goods_value_in_CAD[]')

                    for description, qty, value in zip(goods_descriptions, goods_qtys, goods_values):
                        if description and qty and value:
                            # Remove commas and convert to Decimal
                            try:
                                cleaned_value = Decimal(value.replace(',', '').strip())
                            except InvalidOperation:
                                cleaned_value = Decimal(0)

                            # Create goods using GenericForeignKey
                            goods.objects.create(
                                booking_id_ref=booking,
                                gsa_id_ref=gsa_agreement,
                                goods_description=description,
                                goods_quantity=int(qty),
                                goods_value_in_CAD=cleaned_value,
                                content_type=ContentType.objects.get_for_model(quote_model),
                                object_id=quote_request.id
                            )

                # Update request status
                customer_quoting_details = (
                    ocean_freight_tbl.objects.filter(request_id=quote_reference_number).first() or
                    air_freight_tbl.objects.filter(request_id=quote_reference_number).first() or
                    roro_tbl.objects.filter(request_id=quote_reference_number).first() or
                    customs_brokerage_tbl.objects.filter(request_id=quote_reference_number).first()
                )
                if customer_quoting_details:
                    customer_quoting_details.request_status = 'Approved Quote'
                    customer_quoting_details.save()

                # Send confirmation email
                email_subject = "Booking Confirmation - G10 Blockchain CRM"
                email_body = f"Dear {user_fullname},\n\nYour booking has been successfully created with the reference number {booking.booking_reference_number}.\n\nThank you for choosing G10 Blockchain CRM.\n\nBest regards,\nG10 Blockchain CRM Team"
                send_mail(
                    email_subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user_email],
                    fail_silently=False
                )

                messages.success(request, "Booking created successfully.")

                '''logic to check if Back office has sent customer whether to pay first deposit using
                the system.'''

                # logic is missing from here, it will be updated later

                return redirect(reverse('payments_booking', kwargs={'booking_id': booking.id}))

            except Exception as e:
                messages.error(request, f"Error creating booking: {str(e)}")
                return redirect('dashboard')

        return render(request, 'Bookings/booking_form.html', {
            'quote_request': quote_request,
            'booking_reference_number':quote_reference_number,
            'gsa_agreement': gsa_agreement
        })

    @staticmethod
    @login_required
    @group_required(['clients_team','finance_team','sales_team'])
    
    def payments_booking_view(request, booking_id):
        try:
            gsa_user_id = GSA_agreement_form_tbl.objects.get(username=request.user).id
            booking = booking_freight_tbl.objects.get(id=booking_id,gsa_id_ref_id=gsa_user_id)
            # if booking.service_type == 'Ocean Freight':
            #     currency_code = 'usd' # bussiness Rule: Ocean Freight is always in USD
            # else:   
            #     currency_code = 'cad' # bussiness Rule: Air Freight, RORO, Brokerage is always in CAD
            currency_code = 'eth' #NEW bussiness Rule: All payments are in ETH
            
        except booking_freight_tbl.DoesNotExist:
            messages.error(request, "Booking not found.")
            return redirect('dashboard')
        
        # select total_charges from any of the 4 quote tables based on the service type
        # get total charges to be paid for the booking to be used in the payment page and passed to the smart contract for payment processing
        total_charges = None
        quote_model = None

        for model in [ocean_freight_tbl, air_freight_tbl, customs_brokerage_tbl, roro_tbl]:
            try:
                instance = model.objects.get(request_id=booking.quote_reference_number)
                total_charges = instance.total_charges
                quote_model = model  # store model type if needed
                break
            except model.DoesNotExist:
                continue

        return render(request, 'Payments/payments_booking.html', {
            'customer_email': request.user.email,
            'quote_request': booking.quote_reference_number,
            'booking_reference_number': booking.booking_reference_number,
            'booking_id': booking.id,
            'currency_code': currency_code,
            'booking': booking,
            'total_charges': total_charges,
            # REQUIRED FOR METAMASK
            'contract_address': settings.PAYMENT_CONTRACT_ADDRESS,
            'contract_abi_json': json.dumps(settings.PAYMENT_CONTRACT_ABI),
        })