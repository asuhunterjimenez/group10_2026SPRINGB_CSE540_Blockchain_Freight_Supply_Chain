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
    customs_brokerage_tbl,
    new_quotings
)
from apps.Bookings.models import booking_freight_tbl, vehicle, goods
from apps.Payments.models import blockchain_payment
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
            'service_type': booking.service_type,
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
    
    # This view is for displaying booking details, it will be linked to the booking details page in the clients team dashboard
    # @staticmethod
    # @login_required
    # @group_required(['clients_team','finance_team','sales_team'])
    # def booking_details(request):
    #     user = request.user
    #     username = user.username
    #     user_email = user.email
    #     user_fullname = f"{user.first_name} {user.last_name}"

    #     gsa_user_id = GSA_agreement_form_tbl.objects.get(username=request.user).id
    #     bookings = booking_freight_tbl.objects.filter(gsa_id_ref_id=gsa_user_id,updated_by=0 and request_status=="Pending")

    #     return render(request, 'Bookings/booking_details.html', {
    #         'bookings': bookings,
    #         'request_id': booking_freight_tbl.id,
    #         "receiver_company_name": booking_freight_tbl.receiver_company_name,
    #         "receiver_fullname": booking_freight_tbl.receiver_fullname,
    #         "date_received": booking_freight_tbl.date_received,
    #         "time_received": booking_freight_tbl.time_received,
    #         "service_type": booking_freight_tbl.service_type,
    #         "quote_reference_number": booking_freight_tbl.quote_reference_number,
    #         "request_status": booking_freight_tbl.request_status,

    #     })

    #List all bookings for the logged in user, this will be used in the clients team dashboard to display all bookings for the logged in user, with a link to view booking details and make payment if booking is pending
    @staticmethod
    @login_required
    @group_required(['clients_team','finance_team','sales_team'])
    def booking_details(request):
        gsa_user_id = GSA_agreement_form_tbl.objects.get(
            username=request.user
        ).id

        bookings = (
            booking_freight_tbl.objects
            .filter(
                gsa_id_ref_id=gsa_user_id,
                request_status="Pending",
                quote_reference_number__in=blockchain_payment.objects.filter(
                    paid_amount__isnull=False
                ).values_list("quote_request_id", flat=True)
            )
            .order_by('-date_received', '-time_received')
        )

        return render(request, 'Bookings/booking_details.html', {
            'bookings': bookings
        })
        if not booking:
            messages.error(request, "Booking not found.")
            return redirect('Bookings/booking_details')

        return render(request, 'Bookings/booking_details.html', {
            'booking': booking,
            'request_id': booking.id,
            "receiver_company_name": booking.receiver_company_name,
            "receiver_fullname": booking.receiver_fullname,
            "date_received": booking.date_received,
            "time_received": booking.time_received,
            "service_type": booking.service_type,
            "quote_reference_number": booking.quote_reference_number,
            "request_status": booking.request_status,
        })
    
    @staticmethod
    @login_required
    @group_required(['finance_team','sales_team'])
    def booking_approvals(request):
       
        bookings = (
            booking_freight_tbl.objects
            .filter(
                request_status="Pending",
                quote_reference_number__in=blockchain_payment.objects.filter(
                    paid_amount__isnull=False
                ).values_list("quote_request_id", flat=True)
            )
            .order_by('-date_received', '-time_received')
        )

        return render(request, 'Bookings/booking_approvals_details.html', {
            'bookings': bookings
        })
        if not booking:
            messages.error(request, "Booking not found.")
            return redirect('Bookings/booking_approvals_details')

        return render(request, 'Bookings/booking_approvals_details.html', {
            'booking': booking,
            'request_id': booking.id,
            "receiver_company_name": booking.receiver_company_name,
            "receiver_fullname": booking.receiver_fullname,
            "date_received": booking.date_received,
            "time_received": booking.time_received,
            "service_type": booking.service_type,
            "quote_reference_number": booking.quote_reference_number,
            "request_status": booking.request_status,
        })
    #sales team accesses and converts Bookings to shipments
    @staticmethod
    @login_required
    @group_required(['sales_team'])
    def booking_approvals_details(request, id):
        try:
            booking = booking_freight_tbl.objects.get(id=id)
        except booking_freight_tbl.DoesNotExist:
            messages.error(request, "Booking not found.")
            return redirect('booking_approvals')
        # Get shipper details from GSA agreement using the foreign key relationship
        shipper_details = booking.gsa_id_ref   # direct FK object
        shipper_fullname = shipper_details.user_id_ref.get_full_name()
        # get quote Id for different freight modes using content type and object id
        air=air_freight_tbl.objects.filter(request_id=booking.quote_reference_number).first() if booking.content_type.model == 'air_freight_tbl' else None
        ocean=ocean_freight_tbl.objects.filter(request_id=booking.quote_reference_number).first() if booking.content_type.model == 'ocean_freight_tbl' else None
        roro=roro_tbl.objects.filter(request_id=booking.quote_reference_number).first() if booking.content_type.model == 'roro_tbl' else None
        customs=customs_brokerage_tbl.objects.filter(quote_request_id=booking.quote_reference_number).first() if booking.content_type.model == 'customs_brokerage_tbl' else None
        #for all selected fields but select one
        customer_quoting_details = air or ocean or roro or customs or None
        #selecting from blockchain_payment table
        blockchain_payment_details = blockchain_payment.objects.filter(quote_request_id=booking.quote_reference_number).first()

        return render(request, 'Bookings/change_from_bookings_to_Shipment.html', {
            'booking': booking,
            'request_id': booking.id,
            'shipper_details': shipper_details,
            'blockchain_payment_details': blockchain_payment_details,

            # shipper details
            "shipper_company_name": shipper_details.customer_registered_business_name,
            "shipper_fullname": shipper_fullname,
            "shipper_address": shipper_details.service_address,
            "shipper_export_number": shipper_details.corp_jur_number,
            "shipper_phone_number": shipper_details.telephone_number,
            "shipper_email": shipper_details.email_address,

            # receiver details
            "receiver_company_name": booking.receiver_company_name,
            "receiver_fullname": booking.receiver_fullname,
            "date_received": booking.date_received,
            "time_received": booking.time_received,
            "receiver_phone_number": booking.receiver_phone_number,
            "receiver_email": booking.receiver_email,
            "receiver_tax_id": booking.receiver_tax_id,
            "receiver_driver_lincence_number": booking.receiver_driver_lincence_number,
            "receiver_passport_no": booking.receiver_passport_no,
            "receiver_address": booking.receiver_address,
            "service_type": booking.service_type,
            "model_name": booking.service_type,
            "quote_reference_number": booking.quote_reference_number,
            "request_status": booking.request_status,
            #the below style prevents too much code clustering
            # bookings details for freight modes
            "air": air,
            "ocean": ocean,
            "roro": roro,
            "customs": customs,
            "customer_quoting_details": customer_quoting_details,
            #blockchain payment details:
            "blockchain_payment_details": blockchain_payment_details
           
        })

    @staticmethod
    @login_required
    @group_required(['sales_team'])
    def convert_booking_to_shipment(request, id):
        try:
            booking = booking_freight_tbl.objects.get(id=id)
            # Here you would add logic to convert the booking to a shipment, such as creating a new shipment object and copying relevant data from the booking
            # For example:
            # shipment = Shipment.objects.create(
            #     booking_reference_number=booking.booking_reference_number,
            #     receiver_company_name=booking.receiver_company_name,
            #     receiver_fullname=booking.receiver_fullname,
            #     date_received=booking.date_received,
            #     time_received=booking.time_received,
            #     service_type=booking.service_type,
            #     quote_reference_number=booking.quote_reference_number,
            #     request_status='Converted to Shipment'
            # )
            booking.request_status = 'Converted to Shipment'
            booking.save()
            messages.success(request, "Booking has been converted to shipment successfully.")
        except booking_freight_tbl.DoesNotExist:
            messages.error(request, "Booking not found.")
        
        return redirect('booking_approvals')