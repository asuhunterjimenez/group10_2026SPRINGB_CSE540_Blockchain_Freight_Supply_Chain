from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from apps.Helpers.decorators import *
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from apps.Login.models import new_quotings, onboarding, GSA_agreement_form_tbl,ocean_freight_tbl, air_freight_tbl,customs_brokerage_tbl,CustomsBrokerageFile,roro_tbl
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, datetime
import datetime
import random
import string
import os#files handling
from django.conf import settings#files handling
from django.core.files.storage import FileSystemStorage#files handling
from django.http import FileResponse#files handling
from django.core.mail import send_mail #sending email
from django.conf import settings # import local_settings like emails,Apis accounts
import uuid
from django.db import transaction # handles exception and roll back
import os
from django.http import HttpResponse, Http404 # handles file download and preview
from django.utils.encoding import smart_str # handles file download and preview
from decimal import Decimal
from urllib.parse import urlencode # for building query strings# for redirect with params# LOI agreement form

#setting current date and time
today = date.today()
# formatted_date = datetime.datetime.now().date()
# now = datetime.datetime.now()
# formatted_time = now.strftime("%H:%M:%S")
# #setting date_joined
# formatted_time2 = now.strftime("%Y-%m-%d %H:%M:%S%z")


class QuotingView:
    @login_required
    @group_required(['clients_team','finance_team','sales_team'])
    def quoting_list(request):
        user = request.user
        quotes = []
        inbox_quotes = []
        client_inbox_quotes = []
        client_completed_quotes = []

        # ---- GSA access ----
        if user.groups.filter(name='clients_team').exists():
            gsa_forms = GSA_agreement_form_tbl.objects.filter(user_id_ref=user).select_related('user_id_ref')
        else:
            gsa_forms = GSA_agreement_form_tbl.objects.select_related('user_id_ref').all()

        # ---- Helper: common freight collector ----
        def format_freights(user_obj, freight_type, queryset):
            return [
                {
                    "model_obj": f,
                    "date_received": f.date_received,
                    "time_received": f.time_received,
                    "request_id": f.request_id,
                    "freight_type": freight_type,
                    "first_name": user_obj.first_name,
                    "last_name": user_obj.last_name,
                    "updated_date_time": f.updated_date_time,
                    "request_status": f.request_status, # for client_completed_quotes.html
                }
                for f in queryset
            ]

        # ---- Staff/Sales: collect quotes ----views in the table
        for gsa in gsa_forms:
            user_obj = gsa.user_id_ref
            freight_types = [
                ("Ocean Freight", gsa.ocean_freight_by_id.filter(updated_by='0', locked_by='0').order_by('updated_date_time')),
                ("Air Freight", gsa.air_freight_by_id.filter(updated_by='0', locked_by='0').order_by('updated_date_time')),
                ("Customs Brokerage", gsa.customs_brokerage_by_id.filter(updated_by='0', locked_by='0').order_by('updated_date_time')),
                ("RORO", gsa.roro_by_id.filter(updated_by='0', locked_by='0').order_by('updated_date_time')),
            ]
            for f_type, qs in freight_types:
                quotes.extend(format_freights(user_obj, f_type, qs))

        quotes.sort(key=lambda x: x["updated_date_time"])

        # ---- Booking cases (only for finance/sales) ----
        book_cases_access = user.groups.filter(name__in=['finance_team', 'sales_team']).exists()
        if request.method == "POST" and request.POST.get("book_queries_limit") and book_cases_access:
            x_limit = int(request.POST["book_queries_limit"])
            if x_limit > 0:
                to_book = quotes[:x_limit]
                for q in to_book:
                    obj = q["model_obj"]
                    if obj.locked_by == "0":
                        obj.locked_by = user.username
                        obj.save()
                messages.success(request, f"{len(to_book)} Records have been booked.", extra_tags="success_booked_queries")
                return redirect("quoting")
            else:
                messages.info(request, "No records Selected.", extra_tags="failed_booked_queries")
                return redirect("messages_view")

        # ---- Staff/Finance inbox ---- only access
        elif book_cases_access:
            for gsa in gsa_forms:
                user_obj = gsa.user_id_ref
                freight_types = [
                    ("Ocean Freight", gsa.ocean_freight_by_id.filter(updated_by='0', locked_by=user.username).order_by('updated_date_time')),
                    ("Air Freight", gsa.air_freight_by_id.filter(updated_by='0', locked_by=user.username).order_by('updated_date_time')),
                    ("Customs Brokerage", gsa.customs_brokerage_by_id.filter(updated_by='0', locked_by=user.username).order_by('updated_date_time')),
                    ("RORO", gsa.roro_by_id.filter(updated_by='0', locked_by=user.username).order_by('updated_date_time')),
                ]
                for f_type, qs in freight_types:
                    inbox_quotes.extend(format_freights(user_obj, f_type, qs))
            inbox_quotes.sort(key=lambda x: x["updated_date_time"])

        # ---- Client inbox ----
        else:  # clients_team only
            for gsa in gsa_forms:
                user_obj = gsa.user_id_ref
                #for clients inbox
                freight_inbox = [
                    ("Ocean Freight", gsa.ocean_freight_by_id.filter(request_status='Responded To', id_gsa_ref=gsa).order_by('-updated_date_time')),
                    ("Air Freight", gsa.air_freight_by_id.filter(request_status='Responded To', id_gsa_ref=gsa).order_by('-updated_date_time')),
                    ("Customs Brokerage", gsa.customs_brokerage_by_id.filter(request_status='Responded To', id_gsa_ref=gsa).order_by('-updated_date_time')),
                    ("RORO", gsa.roro_by_id.filter(request_status='Responded To', id_gsa_ref=gsa).order_by('-updated_date_time')),
                ]
                # for clients completed quotes
                freight_completed = [
                    ("Ocean Freight", gsa.ocean_freight_by_id.filter(request_status__in=['Approved Quote','Rejected Quote'], id_gsa_ref=gsa).order_by('-updated_date_time')),
                    ("Air Freight", gsa.air_freight_by_id.filter(request_status__in=['Approved Quote','Rejected Quote'], id_gsa_ref=gsa).order_by('-updated_date_time')),
                    ("Customs Brokerage", gsa.customs_brokerage_by_id.filter(request_status__in=['Approved Quote','Rejected Quote'], id_gsa_ref=gsa).order_by('-updated_date_time')),
                    ("RORO", gsa.roro_by_id.filter(request_status__in=['Approved Quote','Rejected Quote'], id_gsa_ref=gsa).order_by('-updated_date_time')),
                ]
                #for clients inbox
                for f_type, qs in freight_inbox:
                    client_inbox_quotes.extend(format_freights(user_obj, f_type, qs))
                # for clients completed quotes
                for f_type, qs in freight_completed:
                    client_completed_quotes.extend(format_freights(user_obj, f_type, qs))

            #for both client inbox and completed quotes
            client_inbox_quotes.sort(key=lambda x: x["updated_date_time"], reverse=True)
            client_completed_quotes.sort(key=lambda x: x["updated_date_time"], reverse=True)
        # ---- Render ----
        return render(
            request,
            "Quotings/quoting.html",
            {
                "quotes": quotes,
                "book_cases_access": book_cases_access,
                "inbox_quotes": inbox_quotes,
                "client_inbox_quotes": client_inbox_quotes,
                "client_completed_quotes": client_completed_quotes,  # for client_completed_quotes.html
            }
        )

    
    #locking or booking one user at a time
    @login_required
    @group_required(['finance_team', 'sales_team'])
    def single_lock_case(request):
        if request.method == 'POST':
            request_id_single = request.POST.get('request_id', '').strip()
            username_single = request.POST.get('username_single', '').strip()
            # ensure current user matches
            if request.user.username == username_single:
                try:
                    with transaction.atomic(): # handles exceptions on error and roll back
                        ocean_freight_tbl.objects.filter(
                            request_id=request_id_single,
                            locked_by='0'
                        ).update(locked_by=username_single)

                        air_freight_tbl.objects.filter(
                            request_id=request_id_single,
                            locked_by='0'
                        ).update(locked_by=username_single)

                        customs_brokerage_tbl.objects.filter(
                            request_id=request_id_single,
                            locked_by='0'
                        ).update(locked_by=username_single)

                        roro_tbl.objects.filter(
                            request_id=request_id_single,
                            locked_by='0'
                        ).update(locked_by=username_single)

                        messages.success(request,"Case has been Booked in your Inbox")
                        messages.info(request,"Navigate to your Inbox Quotes to access")
                except Exception as e:
                    # rollback happens automatically if an exception occurs
                    print(f"Locking failed: {e}")
                    messages.error(request,"Case is not Booked in your Inbox")
                    return redirect("quoting")

            return redirect("quoting")

        return redirect("quoting")  


    @staticmethod
    @login_required
    @group_required(['clients_team', 'finance_team', 'sales_team'])
    def GSA_agreement_form(request):
        user = request.user
        today = timezone.localdate()       # date object for DateField
        now = timezone.localtime()         # datetime object for time

        if request.method == 'POST':
            # Check if user has a username
            if not user.username:
                messages.error(request, "Username is required.")
                return render(request, 'Quotings/GSA_agreement_form.html')

            # Check if GSA already signed
            if onboarding.objects.filter(username=user.username, gsa_signed='Yes').exists():
                messages.error(request, "GSA agreement already signed.")
                return render(request, 'Quotings/GSA_agreement_form.html')

            # Create GSA agreement form entry
            GSA = GSA_agreement_form_tbl.objects.update_or_create(
                date_received=today,
                user_id_ref=user,
                username=user.username,
                customer_registered_business_name=request.POST.get('customer_registered_business_name', '').capitalize().strip(),
                corp_jur_number=request.POST.get('corp_jur_number', '').capitalize().strip(),
                service_address=request.POST.get('service_address', '').capitalize().strip(),
                billing_address=request.POST.get('billing_address', '').capitalize().strip(),
                GST_HST=request.POST.get('GST_HST', '').capitalize().strip(),
                business_form=request.POST.get('business_form', '').capitalize().strip(),
                auth_contact_number=request.POST.get('auth_contact_number', 'N/A').strip(),
                telephone_number=request.POST.get('telephone_number', '').strip(),
                fax_number=request.POST.get('fax_number', 'N/A').strip(),
                email_address=request.POST.get('email_address', '').strip(),
                #commented this out, not needed at this stage
                # bank_name=request.POST.get('bank_name', 'N/A').capitalize().strip(),
                # branch_id=request.POST.get('branch_id', 'N/A').capitalize().strip(),
                # bank_address=request.POST.get('branch_address', 'N/A').capitalize().strip(),
                # bank_account_number=request.POST.get('account_number', 'N/A').strip(),
                title=request.POST.get('title', 'N/A').capitalize().strip(),
                locked_by='0'
            )

            # Save to onboarding table
            onboarding_GSA = onboarding.objects.update_or_create(
                date_signed=today,
                time_signed=now.time(),       # store as TimeField
                username=user.username,
                gsa_signed='Yes',
                gsa_signed_date_time=now
            )

            messages.success(request, "GSA agreement form submitted successfully.")
            # messages.info(request, " Log-out, re-login.")
            # return redirect(reverse('login'))
            return redirect(reverse('dashboard'))

        return render(request, 'Quotings/GSA_agreement_form.html')
    
    @staticmethod
    @login_required
    @group_required(['clients_team', 'finance_team', 'sales_team'])
    def quoting_request(request):
        gsa_instance = GSA_agreement_form_tbl.objects.get(username=request.user.username)

        def generate_unique_request_id():
            """Generate a unique request ID across all freight tables."""
            while True:
                request_id = f"REQ{uuid.uuid4().hex[:10]}".upper()
                exists = (
                    ocean_freight_tbl.objects.filter(request_id=request_id).exists() or
                    air_freight_tbl.objects.filter(request_id=request_id).exists() or
                    customs_brokerage_tbl.objects.filter(request_id=request_id).exists() or
                    roro_tbl.objects.filter(request_id=request_id).exists()
                )
                if not exists:
                    return request_id

        if request.method == 'POST':

            # refresh date & time each request
            now = datetime.datetime.now()
            formatted_date = now.date()
            formatted_time = now.strftime("%H:%M:%S")
            formatted_time2 = now.strftime("%Y-%m-%d %H:%M:%S%z")

            service_type = request.POST.get('service_type_hidden')

            # Ocean Freight
            if service_type == 'Ocean Freight':
                request_id = generate_unique_request_id()
                ocean_freight_tbl.objects.create(
                    request_id=request_id + str(gsa_instance.id),
                    date_received=formatted_date,
                    time_received=formatted_time,
                    id_gsa_ref=gsa_instance,
                    place_of_receipt=request.POST.get('place_of_receipt', '').strip(),
                    port_of_loading=request.POST.get('port_of_loading', '').strip(),
                    country_of_loading=request.POST.get('country_of_loading', '').split(':')[-1].strip(),
                    tracking=request.POST.get('tracking','').strip(),
                    door_delivery_address=request.POST.get('door_delivery_address','N/A').strip(),
                    hazardous=request.POST.get('hazardous','').strip(),
                    port_of_discharge=request.POST.get('port_of_discharge', '').strip(),
                    country_of_discharge=request.POST.get('country_of_discharge', '').split(':')[-1].strip(),
                    equipment_size=request.POST.get('equipment_size', '').strip(),
                    estimated_shipping_date=request.POST.get('estimated_shipping_date', '').strip(),
                    commodity_cat=request.POST.get('commodity_cat', '').strip(),
                    commodity_sub=request.POST.get('commodity_sub', '').strip(),
                    additional_info=request.POST.get('additional_information', 'N/A').strip().capitalize()
                )
                messages.success(request, "Ocean Freight: Quoting request submitted successfully.")
                messages.info(request, "A G10 Blockchain Freight Staff will get back to you shortly.")
                return redirect(reverse('quoting'))

            # Air Freight
            elif service_type == 'Air Freight':
                request_id = generate_unique_request_id()
                air_freight_tbl.objects.create(
                    request_id=request_id + str(gsa_instance.id),
                    date_received=formatted_date,
                    time_received=formatted_time,
                    id_gsa_ref=gsa_instance,
                    place_of_receipt=request.POST.get('place_of_receipt', '').strip(),
                    departure=request.POST.get('departure', '').strip(),
                    country_of_departure=request.POST.get('country_of_departure', '').split(':')[-1].strip(),
                    destination=request.POST.get('destination', '').strip(),
                    country_of_destination=request.POST.get('country_of_discharge', '').split(':')[-1].strip(),
                    estimated_shipping_date=request.POST.get('estimated_shipping_date', '').strip(),
                    tracking=request.POST.get('tracking','').strip(),
                    door_delivery_address=request.POST.get('door_delivery_address','N/A').strip(),
                    hazardous=request.POST.get('hazardous','').strip(),
                    additional_info=request.POST.get('additional_info', 'N/A').strip().capitalize(),
                    number_of_units=request.POST.get('number_of_units', '').strip(),
                    length=request.POST.get('length', '').strip(),
                    width=request.POST.get('width', '').strip(),
                    height=request.POST.get('height', '').strip(),
                    weight=request.POST.get('weight', '').strip(),
                    unit_of_measurement_L_W_H=request.POST.get('unit_of_measurement_L_W_H', '').strip(),
                    unit_of_measurement_weight=request.POST.get('unit_of_measurement_weight', '').strip(),
                    commodity_cat=request.POST.get('commodity_cat', '').strip(),
                    commodity_sub=request.POST.get('commodity_sub', '').strip()
                )
                messages.success(request, "Air Freight: Quoting request submitted successfully.")
                messages.info(request, "A G10 Blockchain Freight Staff will get back to you shortly.")
                return redirect(reverse('quoting'))

            # RORO Freight
            elif service_type == 'RORO Freight':
                request_id = generate_unique_request_id()
                roro_tbl.objects.create(
                    request_id=request_id + str(gsa_instance.id),
                    date_received=formatted_date,
                    time_received=formatted_time,
                    id_gsa_ref=gsa_instance,
                    estimated_shipping_date=request.POST.get('estimated_shipping_date', '').strip(),
                    vehicle_pickup_address=request.POST.get('pickup_address', '').strip(),
                    vehicle_delivery_address=request.POST.get('drop_off_address', '').strip(),
                    tracking=request.POST.get('tracking','').strip(),
                    door_delivery_address=request.POST.get('door_delivery_address','N/A').strip(),
                    hazardous=request.POST.get('hazardous','').strip(),
                    additional_info=request.POST.get('additional_info', 'N/A').strip().capitalize(),
                    number_of_units=request.POST.get('number_of_units', '').strip(),
                    length=request.POST.get('length', '').strip(),
                    width=request.POST.get('width', '').strip(),
                    height=request.POST.get('height', '').strip(),
                    weight=request.POST.get('weight', '').strip(),
                    unit_of_measurement_L_W_H=request.POST.get('unit_of_measurement_L_W_H', '').strip(),
                    unit_of_measurement_weight=request.POST.get('unit_of_measurement_weight', '').strip(),
                    commodity_cat=request.POST.get('commodity_cat', '').strip(),
                    commodity_sub=request.POST.get('commodity_sub', '').strip()
                )
                messages.success(request, "RORO Freight: Quoting request submitted successfully.")
                messages.info(request, "A G10 Blockchain Freight Staff will get back to you shortly.")
                return redirect(reverse('quoting'))

            # Customs Brokerage
            elif service_type == 'Customs Brokerage':
                request_id = generate_unique_request_id()
                customs_brokerage = customs_brokerage_tbl.objects.create(
                    request_id=request_id + str(gsa_instance.id),
                    date_received=formatted_date,
                    time_received=formatted_time,
                    id_gsa_ref=gsa_instance,
                    place_of_receipt=request.POST.get('place_of_receipt', '').strip(),
                    port_of_loading=request.POST.get('port_of_loading', '').strip(),
                    country_of_loading=request.POST.get('country_of_departure', '').split(':')[-1].strip(),
                    port_of_discharge=request.POST.get('port_of_discharge', '').strip(),
                    country_of_discharge=request.POST.get('country_of_discharge', '').split(':')[-1].strip(),
                    tracking=request.POST.get('tracking','').strip(),
                    door_delivery_address=request.POST.get('door_delivery_address','N/A').strip(),
                    hazardous=request.POST.get('hazardous','').strip(),
                    estimated_shipping_date=request.POST.get('estimated_shipping_date', '').strip(),
                    additional_info=request.POST.get('additional_info', 'N/A').strip().capitalize(),
                    commodity_cat=request.POST.get('commodity_cat', '').strip(),
                    commodity_sub=request.POST.get('commodity_sub', '').strip()
                )

                # Handle multiple file uploads
                files = request.FILES.getlist("upload_invoice_packaging_list")
                for f in files:
                    CustomsBrokerageFile.objects.create(
                        brokerage=customs_brokerage,
                        file=f
                    )

                messages.success(request, "Customs Brokerage: Quoting request submitted successfully.")
                messages.info(request, "A G10 Blockchain Freight Staff will get back to you shortly.")
                return redirect(reverse('quoting'))

            else:
                messages.error(request, "Invalid service type or data not submitted.")
                return render(request, 'Quotings/quoting_request.html')

        # GET request: render the quoting form
        return render(request, 'Quotings/quoting_request.html')


    # Update / respond Quotes
    @login_required
    @group_required(['finance_team', 'sales_team'])
    def update_quote(request, request_id):
        record = None
        model_name = None
        gsa = None
        gsa_user = None  

        # Get record from all freight tables
        try:
            record = ocean_freight_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
            model_name = "Ocean Freight"
        except ocean_freight_tbl.DoesNotExist:
            try:
                record = air_freight_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
                model_name = "Air Freight"
            except air_freight_tbl.DoesNotExist:
                try:
                    record = customs_brokerage_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
                    model_name = "Customs Brokerage"
                except customs_brokerage_tbl.DoesNotExist:
                    try:
                        record = roro_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
                        model_name = "RORO Freight"
                    except roro_tbl.DoesNotExist:
                        raise Http404("No record found for this request ID in any freight table.")

        # Extract related GSA + User info
        gsa = record.id_gsa_ref
        gsa_user = gsa.user_id_ref if gsa else None

        # 📂 Load files from media folder
        folder_path = os.path.join(settings.MEDIA_ROOT, "customs_brokerage", str(request_id))
        files = []
        if os.path.exists(folder_path):
            for f in os.listdir(folder_path):
                # Build correct URL using MEDIA_URL
                file_url = os.path.join(settings.MEDIA_URL, "customs_brokerage", str(request_id), f)
                files.append({"name": f, "url": file_url})

        return render(
            request,
            "Quotings/update_quotes.html",
            {
                "record": record,
                "model_name": model_name,
                "gsa": gsa,
                "gsa_user": gsa_user,
                "current_user": request.user,
                "files": files,  # pass file info to template
            },
        )
    # Update / respond to Quotes
    
    #file download
    @login_required
    @group_required(['finance_team', 'sales_team'])
    def download_file(request, request_id, filename):
        # Build full file path
        file_path = os.path.join(settings.MEDIA_ROOT, "customs_brokerage", str(request_id), filename)

        if not os.path.exists(file_path):
            raise Http404("File does not exist")

        # Open the file in binary mode
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{smart_str(filename)}"'
            return response

    # call helper function to safely parse floats:from apps.Helpers.decorators import safe_float
    #file being handled
    @login_required
    @group_required(['finance_team', 'sales_team'])
    def update_quotes_response(request):
        if request.method == "POST":
            service_type = request.POST.get("service_type_hidden")
            request_id = request.POST.get("request_id_hidden")
            first_hidden = request.POST.get("first_hidden")
            user_email_hidden = request.POST.get("user_email_hidden")
            company_email_hidden = request.POST.get("company_email_hidden")
            full_name = request.POST.get("full_name")

            if service_type == "Ocean Freight":
                try:
                    record = ocean_freight_tbl.objects.get(request_id=request_id)

                    # Update text fields
                    record.currency_type = request.POST.get("currency_type", "").strip()
                    record.validity_date = request.POST.get("validity_date", "").strip() or None
                    record.comments = request.POST.get("comments", "").strip()
                    record.updated_by = request.user.username
                    record.request_status = "Responded To"

                    # Validate numeric inputs
                    freight = safe_float(request.POST.get("freight_charges"))
                    fuel = safe_float(request.POST.get("fuel_surcharge"))
                    customs = safe_float(request.POST.get("customs_charges"))
                    other = safe_float(request.POST.get("other_charges"))

                    # Check required freight charges
                    if freight is None:
                        messages.error(request, "Freight charges is required and must be a valid number.")
                        return redirect('quoting')

                    # Check other optional numeric fields
                    for val, name in zip([fuel, customs, other], ["Fuel Surcharge", "Customs Charges", "Other Charges"]):
                        if val is not None and not isinstance(val, float):
                            messages.error(request, f"{name} must be a valid number if provided.")
                            return redirect('quoting')

                    # Save numeric fields
                    record.freight_charges = freight
                    record.fuel_surcharge = fuel or 0
                    record.customs_charges = customs or 0
                    record.other_charges = other or 0

                    # Calculate total charges
                    record.total_charges = (
                        record.freight_charges +
                        record.fuel_surcharge +
                        record.customs_charges +
                        record.other_charges
                    )

                    record.save()

                    messages.success(request, f"Request Id: {request_id}.")
                    messages.info(request, "Ocean Freight request has been updated and Email Sent to client")

                    # Send email notification
                    send_quote_email(
                        record,
                        service_type,
                        request_id,
                        first_hidden.capitalize(),
                        user_email_hidden,
                        company_email_hidden
                    )

                    return redirect('quoting')

                except ocean_freight_tbl.DoesNotExist:
                    messages.error(request, f"No Ocean Freight record found for request {request_id}.")
                    return redirect("quoting")
            
            elif service_type == "Air Freight":
                try:
                    record = air_freight_tbl.objects.get(request_id=request_id)

                    # Update text fields
                    record.currency_type = request.POST.get("currency_type", "").strip()
                    record.validity_date = request.POST.get("validity_date", "").strip() or None
                    record.comments = request.POST.get("comments", "").strip()
                    record.updated_by = request.user.username
                    record.request_status = "Responded To"

                    # Validate numeric inputs
                    freight = safe_float(request.POST.get("freight_charges"))
                    fuel = safe_float(request.POST.get("fuel_surcharge"))
                    customs = safe_float(request.POST.get("customs_charges"))
                    other = safe_float(request.POST.get("other_charges"))

                    # Check required freight charges
                    if freight is None:
                        messages.error(request, "Freight charges is required and must be a valid number.")
                        return redirect('quoting')

                    # Check other optional numeric fields
                    for val, name in zip([fuel, customs, other], ["Fuel Surcharge", "Customs Charges", "Other Charges"]):
                        if val is not None and not isinstance(val, float):
                            messages.error(request, f"{name} must be a valid number if provided.")
                            return redirect('quoting')

                    # Save numeric fields
                    record.freight_charges = freight
                    record.fuel_surcharge = fuel or 0
                    record.customs_charges = customs or 0
                    record.other_charges = other or 0

                    # Calculate total charges
                    record.total_charges = (
                        record.freight_charges +
                        record.fuel_surcharge +
                        record.customs_charges +
                        record.other_charges
                    )

                    record.save()

                    messages.success(request, f"Request Id: {request_id}.")
                    messages.info(request, "Air Freight request has been updated and Email Sent to client")

                    # Send email notification
                    # Send email notification
                    send_quote_email(
                        record,
                        service_type,
                        request_id,
                        first_hidden.capitalize(),
                        user_email_hidden,
                        company_email_hidden
                    )


                    return redirect('quoting')

                except air_freight_tbl.DoesNotExist:
                    messages.error(request, f"No Air Freight record found for request {request_id}.")
                    return redirect("quoting")

            elif service_type == "RORO Freight":
                try:
                    record = roro_tbl.objects.get(request_id=request_id)

                    # Update text fields
                    record.currency_type = request.POST.get("currency_type", "").strip()
                    record.validity_date = request.POST.get("validity_date", "").strip() or None
                    record.comments = request.POST.get("comments", "").strip()
                    record.updated_by = request.user.username
                    record.request_status = "Responded To"

                    # Validate numeric inputs
                    freight = safe_float(request.POST.get("freight_charges"))
                    fuel = safe_float(request.POST.get("fuel_surcharge"))
                    customs = safe_float(request.POST.get("customs_charges"))
                    other = safe_float(request.POST.get("other_charges"))

                    # Check required freight charges
                    if freight is None:
                        messages.error(request, "Freight charges is required and must be a valid number.")
                        return redirect('quoting')

                    # Check other optional numeric fields
                    for val, name in zip([fuel, customs, other], ["Fuel Surcharge", "Customs Charges", "Other Charges"]):
                        if val is not None and not isinstance(val, float):
                            messages.error(request, f"{name} must be a valid number if provided.")
                            return redirect('quoting')

                    # Save numeric fields
                    record.freight_charges = freight
                    record.fuel_surcharge = fuel or 0
                    record.customs_charges = customs or 0
                    record.other_charges = other or 0

                    # Calculate total charges
                    record.total_charges = (
                        record.freight_charges +
                        record.fuel_surcharge +
                        record.customs_charges +
                        record.other_charges
                    )

                    record.save()

                    messages.success(request, f"Request Id: {request_id}.")
                    messages.info(request, "RORO Freight request has been updated and Email Sent to client")

                    # Send email notification
                    send_quote_email(
                        record,
                        service_type,
                        request_id,
                        first_hidden.capitalize(),
                        user_email_hidden,
                        company_email_hidden
                    )

                    return redirect('quoting')

                except roro_tbl.DoesNotExist:
                    messages.error(request, f"No RORO Freight record found for request {request_id}.")
                    return redirect("quoting")
                

            elif service_type == "Customs Brokerage":
                try:
                    record = customs_brokerage_tbl.objects.get(request_id=request_id)

                    # Update text fields
                    record.currency_type = request.POST.get("currency_type", "").strip()
                    record.validity_date = request.POST.get("validity_date", "").strip() or None
                    record.comments = request.POST.get("comments", "").strip()
                    record.updated_by = request.user.username
                    record.request_status = "Responded To"

                    # Parse numeric inputs (safe_float should return float or None)
                    brokerage_fee = safe_float(request.POST.get("brokerage_fee"))
                    taxes = safe_float(request.POST.get("taxes"))
                    customs_duties = safe_float(request.POST.get("customs_duties"))  # form field may be 'customs_fees'
                    other = safe_float(request.POST.get("other_charges"))

                    # Check required brokerage_fee (was checking `freight` before which wasn't defined)
                    if brokerage_fee is None:
                        messages.error(request, "Brokerage fee is required and must be a valid number.")
                        return redirect('quoting')

                    # Validate optional numeric fields
                    for val, name in zip([taxes, customs_duties, other],
                                        ["Taxes", "Customs fees", "Other Charges"]):
                        if val is not None and not isinstance(val, (int, float)):
                            messages.error(request, f"{name} must be a valid number if provided.")
                            return redirect('quoting')

                    # Convert floats to Decimal for DecimalField assignment (safer precision)
                    def to_decimal(v):
                        return Decimal(str(v)) if v is not None else Decimal("0.00")

                    record.brokerage_fee = to_decimal(brokerage_fee)
                    record.taxes = to_decimal(taxes)
                    record.customs_duties = to_decimal(customs_duties)
                    record.other_charges = to_decimal(other)

                    # Calculate total_charges using the correct model fields
                    record.total_charges = (
                        record.brokerage_fee +
                        record.taxes +
                        record.customs_duties +
                        record.other_charges
                    )

                    record.save()

                    messages.success(request, f"Request Id: {request_id}.")
                    messages.info(request, "Customs Brokerage Freight request has been updated and Email Sent to client")
                    # send Email with attachment
                    # Send email notification
                    send_quote_email(
                        record,
                        service_type,
                        request_id,
                        first_hidden.capitalize(),
                        user_email_hidden,
                        company_email_hidden
                    ) 

                    return redirect('quoting')

                except customs_brokerage_tbl.DoesNotExist:
                    messages.error(request, f"No Customs Brokerage Freight record found for request {request_id}.")
                    return redirect("quoting")

            else:
                messages.error(request, "Unsupported freight type for update.")
                return redirect('quoting')

        return redirect('quoting')

    #clients respond to Quotes either accept/Reject the Quote
    @login_required
    @group_required(['clients_team'])
    def client_update_quote(request, request_id):
        record = None
        model_name = None
        gsa = None
        gsa_user = None  

        # Get record from all freight tables
        try:
            record = ocean_freight_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
            model_name = "Ocean Freight"
        except ocean_freight_tbl.DoesNotExist:
            try:
                record = air_freight_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
                model_name = "Air Freight"
            except air_freight_tbl.DoesNotExist:
                try:
                    record = customs_brokerage_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
                    model_name = "Customs Brokerage"
                except customs_brokerage_tbl.DoesNotExist:
                    try:
                        record = roro_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
                        model_name = "RORO Freight"
                    except roro_tbl.DoesNotExist:
                        raise Http404("No record found for this request ID in any freight table.")

        # Extract related GSA + User info
        gsa = record.id_gsa_ref
        gsa_user = gsa.user_id_ref if gsa else None

        # 📂 Load files from media folder
        folder_path = os.path.join(settings.MEDIA_ROOT, "customs_brokerage", str(request_id))
        files = []
        if os.path.exists(folder_path):
            for f in os.listdir(folder_path):
                # Build correct URL using MEDIA_URL
                file_url = os.path.join(settings.MEDIA_URL, "customs_brokerage", str(request_id), f)
                files.append({"name": f, "url": file_url})

        return render(
            request,
            "Quotings/update_client_quotes.html",
            {
                "record": record,
                "model_name": model_name,
                "gsa": gsa,
                "gsa_user": gsa_user,
                "current_user": request.user,
                "files": files,  # pass file info to template
            },
        )

    # Update client respond Quotes
    @login_required
    @group_required(['clients_team'])
    def update_client_quotes_response(request):
        if request.method == "POST":
            service_type = request.POST.get("service_type_hidden")
            request_id = request.POST.get("request_id_hidden")
            new_status = request.POST.get("request_status", "").strip()

            # Mapping of service type to model
            service_model_map = {
                "Ocean Freight": ocean_freight_tbl,
                "Air Freight": air_freight_tbl,
                "RORO Freight": roro_tbl,
                "Customs Brokerage": customs_brokerage_tbl,
            }

            model = service_model_map.get(service_type)

            # get customer details from GSA_table
            customer_details=GSA_agreement_form_tbl.objects.get(username=request.user.username)
            #get customer quoting details from quoting tables
            customer_quoting_details=(
                ocean_freight_tbl.objects.filter(request_id=request_id).first() or \
                air_freight_tbl.objects.filter(request_id=request_id).first() or \
                roro_tbl.objects.filter(request_id=request_id).first() or \
                customs_brokerage_tbl.objects.filter(request_id=request_id).first()
            )

            if not model:
                messages.error(request, f"Unknown service type: {service_type}")
                return redirect("quoting")

            if new_status == "Approved Quote":
                # Do not save in DB, procceed to Booking stage
                set_message = "Your Quote has been escalated to Booking-Stage."
                messages.success(request, "Prepare your Booking and Submit.")
                messages.info(request, set_message)
                
                return render(request, "Bookings/booking_update_details.html", {
                    "service_type": service_type,
                    "request_id": request_id,
                    "new_status": new_status,
                    "customer_details": customer_details,
                    "customer_quoting_details": customer_quoting_details,
                    
                })

            else:
                # Save in DB for other statuses
                try:
                    record = model.objects.get(request_id=request_id)
                    record.request_status = new_status
                    record.save()

                    set_message = "No further action is needed, thank you for choosing G10 Blockchain Freight."
                    messages.success(request, f"Quote {request_id} has been {new_status}.")
                    messages.info(request, set_message)

                except model.DoesNotExist:
                    messages.error(request, f"No {service_type} record found for request {request_id}.")

                return redirect("quoting")

        # For GET requests just redirect back
        return redirect("quoting")

    #View clients accepted/rejected Quotes
    @login_required
    @group_required(['clients_team'])
    def client_view_quote(request, request_id):
        record = None
        model_name = None
        gsa = None
        gsa_user = None  

        # Get record from all freight tables
        try:
            record = ocean_freight_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
            model_name = "Ocean Freight"
        except ocean_freight_tbl.DoesNotExist:
            try:
                record = air_freight_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
                model_name = "Air Freight"
            except air_freight_tbl.DoesNotExist:
                try:
                    record = customs_brokerage_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
                    model_name = "Customs Brokerage"
                except customs_brokerage_tbl.DoesNotExist:
                    try:
                        record = roro_tbl.objects.select_related("id_gsa_ref__user_id_ref").get(request_id=request_id)
                        model_name = "RORO Freight"
                    except roro_tbl.DoesNotExist:
                        raise Http404("No record found for this request ID in any freight table.")

        # Extract related GSA + User info
        gsa = record.id_gsa_ref
        gsa_user = gsa.user_id_ref if gsa else None

        # 📂 Load files from media folder
        folder_path = os.path.join(settings.MEDIA_ROOT, "customs_brokerage", str(request_id))
        files = []
        if os.path.exists(folder_path):
            for f in os.listdir(folder_path):
                # Build correct URL using MEDIA_URL
                file_url = os.path.join(settings.MEDIA_URL, "customs_brokerage", str(request_id), f)
                files.append({"name": f, "url": file_url})

        return render(
            request,
            "Quotings/view_client_quotes.html",
            {
                "record": record,
                "model_name": model_name,
                "gsa": gsa,
                "gsa_user": gsa_user,
                "current_user": request.user,
                "files": files,  # pass file info to template
            },
        )

 