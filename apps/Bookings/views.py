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
from apps.Bookings.models import booking_freight_tbl, vehicle, goods,TrackingPoint
from apps.Payments.models import blockchain_payment
from django.contrib.contenttypes.models import ContentType
import json
import datetime
#from datetime import datetime
from web3 import Web3

#for image access
import os
from django.http import JsonResponse


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
                blockchain_tx_receipt ="0",
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
        # for image access in the views to temlate
        username=booking.gsa_id_ref.username
        folder_path = os.path.join(settings.MEDIA_ROOT, "uploads", username)
        files = []

        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_url = f"{settings.MEDIA_URL}uploads/{username}/{filename}"
                files.append({
                    "name": filename,
                    "url": file_url
                })
        #selecting goods or vehicles based on the commodity type in the quote request
        vehicles = vehicle.objects.filter(booking_id_ref=booking.id)
        goods_list = goods.objects.filter(booking_id_ref=booking.id)

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
            "blockchain_payment_details": blockchain_payment_details,
            #files for image access
            "files": files,
            #goods and vehicles
            "vehicles": vehicles,
            "goods": goods_list
           
        })

    @login_required
    @group_required(['sales_team','ware_house'])
    @staticmethod
    def convert_booking_to_shipment(request, request_id):

        if request.method != "POST":
            messages.error(request, "Invalid request method.")
            return redirect('booking_approvals')

        try:
            # 1. GET BOOKING DETAILS
            booking = booking_freight_tbl.objects.get(id=request_id)
            service_type = request.POST.get("service_type")

            # 2. CONNECT TO GANACHE 
            w3 = Web3(Web3.HTTPProvider(settings.GANACHE_URL))

            if not w3.is_connected():
                messages.error(request, "Ganache not connected.")
                return redirect('booking_approvals')

            account = w3.eth.accounts[0]

            # 3. LOAD CONTRACT ABI
            shipment_abi_path = os.path.join(
                settings.BASE_DIR,
                "blockchain",
                "abi",
                "ShipmentABI.json"
            )

            with open(shipment_abi_path, "r") as abi_file:
                shipment_abi = json.load(abi_file)

            contract_address = Web3.to_checksum_address(
                settings.SHIPMENT_CONTRACT_ADDRESS
            )

            contract = w3.eth.contract(
                address=contract_address,
                abi=shipment_abi
            )

            # 4. EXTRACT COMMON DATA
            shipper_name = request.POST.get("shipper_fullname")
            receiver_name = request.POST.get("receiver_fullname")
            quote_ref = request.POST.get("quote_reference_number")

            # 5. ROUTE LOGIC
            route = ""

            if service_type == "Air Freight":
                route = f"{request.POST.get('departure')} -> {request.POST.get('destination')}"

            elif service_type == "Ocean Freight":
                route = f"{request.POST.get('port_of_loading')} -> {request.POST.get('port_of_discharge')}"

            elif service_type == "RORO Freight":
                route = f"{request.POST.get('departure')} -> {request.POST.get('destination')}"

            elif service_type == "Customs Brokerage":
                route = f"{request.POST.get('port_of_loading')} -> {request.POST.get('port_of_discharge')}"

            else:
                route = "Unknown"

            # 6. DETERMINE CARGO TYPE
            cargo_type = "GOODS"

            if request.POST.get("commodity_sub") == "Vehicles":
                cargo_type = "VEHICLE"

            # 7. SEND TO BLOCKCHAIN

            shipper = (
                request.POST.get("shipper_company_name", ""),
                request.POST.get("shipper_fullname", ""),
                request.POST.get("shipper_telephone_number", ""),
                request.POST.get("shipper_email", ""),
                request.POST.get("shipper_address", "")
            )

            receiver = (
                request.POST.get("receiver_company_name", ""),
                request.POST.get("receiver_fullname", ""),
                request.POST.get("receiver_phone_number", ""),
                request.POST.get("receiver_email", ""),
                request.POST.get("receiver_address", "")
            )

            paid_amount = request.POST.get("paid_amount", "0")
            paid_amount_wei = w3.to_wei(float(paid_amount), "ether")

            gas_fee_wei = 0
            tx_hash_placeholder = "PENDING"

            tx = contract.functions.createShipment(
                booking.id,
                quote_ref,
                service_type,
                route,
                tx_hash_placeholder,
                paid_amount_wei,
                gas_fee_wei,
                shipper,
                receiver
            ).transact({
                "from": account,
                "gas": 3000000
            })

            tx_receipt = w3.eth.wait_for_transaction_receipt(tx)
            # Update booking with shipment details in postgree
            booking.updated_by = request.user.username
            booking.booking_reference_number = booking.quote_reference_number
            booking.blockchain_tx_receipt=tx_receipt.transactionHash.hex()
            if service_type == "Ocean Freight":
                booking.desired_type_of_release=request.POST.get("desired_type_of_release")
                booking.container_number=request.POST.get("container_number")
                booking.vessel_number=request.POST.get("vessel_number")
                booking.cers=request.POST.get("cers")
                booking.save()
            else:
            #Update bookings with shipment details for other freight modes
                booking.save()
            
            # ==============================
            # TRACKING GENERATION
            # ==============================
            try:
                if service_type == "Air Freight":
                    departure = request.POST.get("departure", "").strip().upper()
                    origin = request.POST.get("air_departure_country", "").strip().lower()
                    destination = request.POST.get("air_destination_country", "").strip().lower()

                    first_point = None
                    use_vancouver_hub = False

                    # ------------------------------
                    # DEPARTURE LOGIC
                    # ------------------------------
                    if departure == "CAKWL KELOWNA":
                        first_point = ("Kelowna Airport", 1, 49.9561, -119.3778)
                        use_vancouver_hub = True

                    elif departure in ["CACAL CALGARY", "CAYYC CALGARY APT"]:
                        first_point = ("Calgary Airport", 1, 51.1139, -114.0203)

                    elif departure == "CATOR TORONTO":
                        first_point = ("Toronto Pearson Airport", 1, 43.6777, -79.6248)

                    elif departure == "CAYVR VANCOUVER":
                        first_point = ("Vancouver Airport", 1, 49.1967, -123.1815)

                    elif departure in ["CAMTR MONTREAL", "CAYUL MONTREAL-DORVAL APT"]:
                        first_point = ("Montreal Airport", 1, 45.4706, -73.7408)

                    # ------------------------------
                    # DESTINATION ROUTING LOGIC
                    # ------------------------------
                    hub = None
                    final = None

                    if destination == "nigeria":
                        hub = ("London Heathrow Airport", None, 51.4700, -0.4543)
                        final = ("Murtala Muhammed Airport", None, 6.5774, 3.3212)

                    elif destination == "united arab emirates":
                        hub = ("Frankfurt Airport", None, 50.0379, 8.5622)
                        final = ("Dubai International Airport", None, 25.2532, 55.3657)

                    elif destination == "united states":
                        hub = ("John F. Kennedy Airport", None, 40.6413, -73.7781)
                        final = ("Los Angeles Airport", None, 33.9416, -118.4085) 

                    elif destination == "india":
                        hub = ("Singapore Changi Airport", None, 1.3644, 103.9915)
                        final = ("Indira Gandhi Airport", None, 28.5562, 77.1000)

                    # ------------------------------
                    # BUILD ROUTE
                    # ------------------------------
                    if origin == "canada" and first_point and hub and final:

                        points = [first_point]
                        seq = 2

                        # Vancouver hub only for Kelowna
                        if use_vancouver_hub:
                            points.append(("Vancouver Airport", seq, 49.1967, -123.1815))
                            seq += 1

                        # Add hub
                        points.append((hub[0], seq, hub[2], hub[3]))
                        seq += 1

                        # Add final destination
                        points.append((final[0], seq, final[2], final[3]))

                        # ------------------------------
                        # SAVE
                        # ------------------------------
                        TrackingPoint.objects.bulk_create([
                            TrackingPoint(
                                booking=booking,
                                booking_reference_number=booking.quote_reference_number,
                                location=loc,
                                sequence=seq,
                                status="current" if seq == 1 else "pending",
                                latitude=lat,
                                longitude=lng
                            )
                            for loc, seq, lat, lng in points
                        ])
                               
                    else:
                        messages.info(request, "No Live Tracking available for this origin and destination combination.")

                elif service_type == "Ocean Freight":
                    origin = request.POST.get("ocean_loading_country", "").strip().lower()
                    destination = request.POST.get("ocean_discharge_country", "").strip().lower()


                else:
                     messages.info(request, "Tracking not saved for origin and destination for this freight mode.")
                
                #saving to the database
                tracking_point = TrackingPoint.objects.create(
                    booking=booking,
                    location=origin,
                    sequence=1,
                    status="pending",
                    latitude=0.0, # to handle test cases
                    longitude=0.0 # to handle test cases
                )


            except Exception as e:
                print("Tracking generation failed:", str(e))
                
            #Email Notifications
            

            tracking_link = request.build_absolute_uri( reverse('track_shipment', args=[booking.id]) )
            shipper_name = request.POST.get("shipper_fullname") or "Customer"
            receiver_name = request.POST.get("receiver_fullname") or "N/A"
            send_mail(
                "Your Shipment has been Created - G10 Blockchain CRM",
                f"Dear {shipper_name},\n\n"
                f"Your shipment has been successfully created on our blockchain freight platform.\n\n"
                f"Shipment Details:\n"
                f"-------------------------\n"
                f"Shipment ID: {booking.id}\n"
                f"Booking Reference: {quote_ref}\n"
                f"Service Type: {service_type}\n"
                f"Route: {route}\n"
                f"Receiver Name: {receiver_name}\n"
                f"Paid Amount (ETH): {paid_amount}\n\n"
                f"Blockchain Tracking Details:\n"
                f"-------------------------\n"
                f"Transaction Hash: {tx_receipt.transactionHash.hex()}\n"
                f"Block Number: {tx_receipt.blockNumber}\n"
                f"Network: Ganache Local Blockchain\n"
                f"Track Shipment: {tracking_link}\n\n"
                f"Thank you for choosing G10 Blockchain CRM.\n\n"
                f"Best regards,\n"
                f"G10 Blockchain CRM Team",
                settings.DEFAULT_FROM_EMAIL,
                [
                    request.POST.get("receiver_email"),
                    request.POST.get("shipper_email")
                ],
                fail_silently=False
            )
            messages.success(
                request,
                f"Shipment created successfully. TX: {tx_receipt.transactionHash.hex()}"
            )

        except booking_freight_tbl.DoesNotExist:
            messages.error(request, "Booking not found.")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('booking_approvals')

    def track_shipment(request, booking_id):
        booking = booking_freight_tbl.objects.get(id=booking_id)

        # Connect to Ganache
        w3 = Web3(Web3.HTTPProvider(settings.GANACHE_URL))

        if not w3.is_connected():
            return HttpResponse("Ganache not connected")

        # Load ABI
        shipment_abi_path = os.path.join(
            settings.BASE_DIR,
            "blockchain",
            "abi",
            "ShipmentABI.json"
        )

        with open(shipment_abi_path, "r") as abi_file:
            shipment_abi = json.load(abi_file)

        contract = w3.eth.contract(
            address=Web3.to_checksum_address(settings.SHIPMENT_CONTRACT_ADDRESS),
            abi=shipment_abi
        )

        # get shipment + parties
        shipment_data = contract.functions.shipments(booking_id).call()
        party_data = contract.functions.parties(booking_id).call()

        # get booking
        booking_details = booking_freight_tbl.objects.get(id=booking_id)

        # determine cargo type
        if booking_details.content_type.model == 'vehicle':
            cargo_type = "VEHICLE"
            cargo_details = vehicle.objects.filter(booking_id_ref=booking_id)
        else:
            cargo_type = "GOODS"
            cargo_details = goods.objects.filter(booking_id_ref=booking_id)
        # get tracking points
        points = TrackingPoint.objects.filter( booking=booking_id ).order_by("sequence")
        route = []

        for p in points:
            route.append({
                "id": p.id,
                "location": p.location,
                "sequence": p.sequence,
                "status": p.status,
                "lat": p.latitude,
                "lng": p.longitude,
                "arrival": str(p.arrival_time) if p.arrival_time else None,
                "departure": str(p.departure_time) if p.departure_time else None,
            })

        current = points.filter(status="current").first()
        # context
        context = {
            "shipment_data": shipment_data,
            "party_data": party_data,
            "cargo_type": cargo_type,
            "cargo_details": cargo_details,
            "date_time": datetime.datetime.fromtimestamp(shipment_data[7]),
            "txt_hash": booking_details.blockchain_tx_receipt,

            # ADDED (safe injection)
            "route": route,
            "current_location": current.location if current else None,
        }
        return render(request, "Tracking/shipment_tracking.html", context)