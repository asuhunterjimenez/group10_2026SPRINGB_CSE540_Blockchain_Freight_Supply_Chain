# apps/Documentations/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.Helpers.decorators import group_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.conf import settings
from decimal import Decimal, InvalidOperation
from apps.Login.models import new_quotings, sea_additional_info, vehicle, goods,onboarding
from apps.Documentations.models import credit_application, credit_references, address_of_owner_officer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
from django.utils import timezone
from django.contrib import messages

now = timezone.localtime()         # datetime object for time


class DocumentationsView:

    @staticmethod
    @login_required
    @group_required(['clients_team', 'finance_team', 'sales_team'])
    def documentation_list(request):
        user = request.user
        if user.groups.filter(name='sales_team').exists():
           documentations = new_quotings.objects.filter(convert_to_booking="True").order_by('id')
        elif user.groups.filter(name='clients_team').exists():
           documentations = new_quotings.objects.filter(convert_to_booking="True", username=user.username).order_by('id')
        #    onboarding1 = onboarding.objects.filter(username=request.user.username, gsa_signed='Yes').count()
        #    return render(request, 'Documentations/documentation_details.html',{'onboarding1': onboarding1})
           return render(request, 'Documentations/documentation_details.html')

        elif user.groups.filter(name='finance_team').exists():
            documentations = new_quotings.objects.filter(convert_to_booking="True").order_by('id')
        else:
            documentations=[]

        return render(request, 'Documentations/documentation_details.html', {'documentations': documentations})

    @staticmethod
    @login_required
    @group_required(['clients_team', 'finance_team', 'sales_team'])
    def documentation_view(request, pk):
        documentation = get_object_or_404(new_quotings, id=pk)
        return render(request, 'Documentations/documentation_view.html', {'documentation': documentation})

    @staticmethod
    @login_required
    def documentation_update(request, pk):
        documentation = get_object_or_404(new_quotings, id=pk)

        try:
            sea_info = documentation.sea_info_by_id.get()
        except ObjectDoesNotExist:
            sea_info = None

        if request.method == 'POST':
            # Update new_quotings fields
            quoting_fields = [
                'request_id', 'shipper_company_name', 'shipper_fullname', 'shipper_phone_number',
                'shipper_email', 'shipper_export_number', 'shipper_address',
                'receiver_company_name', 'receiver_fullname', 'receiver_phone_number',
                'receiver_email', 'receiver_tax_id', 'receiver_driver_lincence',
                'receiver_passport_no', 'receiver_address', 'shipment_type'
            ]
            for field in quoting_fields:
                setattr(documentation, field, request.POST.get(field, getattr(documentation, field)))
            documentation.save()

            with transaction.atomic():
                # Sea Additional Info
                try:
                    cargo_weight = Decimal(request.POST.get('cargo_weight', '0.00'))
                except InvalidOperation:
                    cargo_weight = Decimal('0.00')

                sea_data = {
                    'place_of_receipt': request.POST.get('place_of_receipt', 'N/A'),
                    'port_of_loading': request.POST.get('port_of_loading', 'N/A'),
                    'seal_number': request.POST.get('seal_number', 'N/A'),
                    'container_number': request.POST.get('container_number', 'N/A'),
                    'vessel_number': request.POST.get('vessel_number', 'N/A'),
                    'port_of_discharge': request.POST.get('port_of_discharge', 'N/A'),
                    'cargo_weight': cargo_weight,
                    'desired_type_of_release': request.POST.get('desired_type_of_release', 'N/A'),
                    'hs_code': request.POST.get('hs_code', 'N/A'),
                    'cers': request.POST.get('cers', 'N/A'),
                    'id_quoting_ref': documentation,
                    'booking_ref': documentation.request_id, 
                }

                if sea_info is None:
                    sea_info = sea_additional_info(**sea_data)
                else:
                    for field, value in sea_data.items():
                        setattr(sea_info, field, value)
                sea_info.save()

                # Vehicles (char field)
                vehicle.objects.filter(quoting_id=documentation.id).delete()
                years = request.POST.getlist('vehicle_year[]')
                makes = request.POST.getlist('vehicle_make[]')
                vins = request.POST.getlist('vehicle_vin[]')
                costs = request.POST.getlist('vehicle_cost[]')
                colors = request.POST.getlist('vehicle_color[]')

                for year, make, vin, cost, color in zip(years, makes, vins, costs, colors):
                    if year and vin:
                        vehicle.objects.create(
                            quoting_id=str(documentation.id),  
                            booking_ref=documentation.request_id, 
                            vehicle_year=year.strip(),
                            vehicle_make=make.strip(),
                            vehicle_vin=vin.strip(),
                            vehicle_cost=cost.strip(),
                            vehicle_color=color.strip()
                        )

                # Goods (char field)
                goods.objects.filter(quoting_id=documentation.id).delete()
                qtys = request.POST.getlist('goods_qty[]')
                descriptions = request.POST.getlist('goods_description[]')
                values = request.POST.getlist('goods_value[]')

                for qty, desc, val in zip(qtys, descriptions, values):
                    if desc:
                        try:
                            goods_value = float(val or 0.00)
                        except ValueError:
                            goods_value = 0.00
                        goods.objects.create(
                            quoting_id=str(documentation.id), 
                            booking_ref=documentation.request_id, 
                            goods_quantity=int(qty or 1),
                            goods_description=desc.strip(),
                            goods_value=goods_value
                        )

            #return redirect('documentation_details')
            #success message
            messages.success(request, 'Data Successfully Updated..Please Upload required Files.')
            #re-route to Upload documents page
            return render(request, 'Documentations/documentation_upload_details.html', {'documentation': documentation, 'sea_info': sea_info})

        # GET request
        context = {
            'documentation': documentation,
            'sea_info': sea_info,
            'vehicles': vehicle.objects.filter(quoting_id=documentation.id),
            'goods': goods.objects.filter(quoting_id=documentation.id),
        }
        return render(request, 'Documentations/documentation_update_details.html', context)
        #return render(request, 'Documentations/documentation_upload_details.html', context)

    #upload documents functions
    @csrf_exempt
    @login_required
    def upload_file(request):
        if request.method == 'POST' and request.FILES.get('file'):
            uploaded_file = request.FILES['file']
            file_name = uploaded_file.name

            # Get logged-in username
            user = request.user
            username = user.username

            # Get request_id from POST data (ensure it's passed from frontend)
            

            # Construct user/request_id folder path
            base_dir = 'media/uploads'
            user_folder = os.path.join(base_dir, username)
            request_folder = os.path.join(user_folder)

            # Create folders if they don't exist
            os.makedirs(request_folder, exist_ok=True)

            # Full path to save the file
            file_path = os.path.join(request_folder, file_name)

            # Save the file
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Return relative URL to use in frontend
            file_url = f'/media/uploads/{username}/{file_name}'
            return JsonResponse({'file_name': file_name, 'file_url': file_url})

        return JsonResponse({'error': 'Invalid request'}, status=400)

    #view loaded files by users
    @login_required
    def get_user_files(request):
        username = request.user.username
        user_folder = os.path.join(settings.MEDIA_ROOT, 'uploads', username)

        files_list = []

        if os.path.exists(user_folder):
            for filename in os.listdir(user_folder):
                files_list.append({
                    "name": filename,
                    "url": f"/media/uploads/{username}/{filename}"
                })

        return JsonResponse({"files": files_list})

    @csrf_exempt
    def delete_file(request):
        if request.method == 'POST':
            file_name = request.POST.get('file_name')
            username = request.user.username
            # request_id = request.POST.get('request_id')

            if not (file_name and username):
                return JsonResponse({'error': 'Missing parameters'}, status=400)

            file_path = os.path.join('media/uploads', username, file_name)

            if os.path.exists(file_path):
                os.remove(file_path)
                return JsonResponse({'status': 'deleted'})
            return JsonResponse({'error': 'File not found'}, status=404)

        return JsonResponse({'error': 'Invalid request'}, status=400)
    
        # Delete empty folders after file deletion
        if os.path.exists(file_path):
            os.remove(file_path)

        # Optional: delete empty folders
        try:
            os.removedirs(os.path.dirname(file_path))
        except OSError:
            pass  # Folder not empty, do nothing

    #Documents to be signed
    # LOI agreement form view
    @login_required
    @group_required(['clients_team'])
    def onboarding_LOI_form(request):
        user = request.user

        if request.method == 'POST':
            new_status=request.POST.get("request_status").strip()

            # Ensure user has a username
            if not user.username:
                messages.error(request, "Username is required.")
                return render(request, 'Quotings/GSA_agreement_form.html')

            # Check if LOI already signed
            if onboarding.objects.filter(username=user.username, gsa_signed='Yes', loi_signed='Yes').exists():
                messages.success(request, "LOI agreement already signed.")
                messages.info(request, "Redirecting to Credit Application Form.")
                return redirect('Documentations/credit_application.html')

            # Accept Agreement
            if new_status == "Accept Agreement" and onboarding.objects.filter(
                username=user.username, gsa_signed='Yes', loi_signed='No'
            ).exists():
                onboarding.objects.filter(username=user.username, gsa_signed='Yes', loi_signed='No').update(
                    loi_signed='Yes',
                    loi_signed_date_time=now
                )

                messages.success(request, "LOI agreement form submitted successfully.")
                #redirect to Credit application Documents
                return render(request,'Documentations/credit_application.html')

            # Reject Agreement
            elif new_status == "Reject Agreement":
                # Update relevant tables to mark rejected quote
                if service_type=="Ocean Freight":
                    ocean_freight_tbl.objects.filter(request_id=request_id_post).update(request_status="Rejected Quote")
                    messages.info(request, "You have rejected the LOI agreement. No further action is needed.")
                    return redirect('quoting')
                elif service_type=="Air Freight":
                    air_freight_tbl.objects.filter(request_id=request_id_post).update(request_status="Rejected Quote")
                    messages.info(request, "You have rejected the LOI agreement. No further action is needed.")
                    return redirect('quoting')
                elif service_type=="RORO Freight":
                    roro_tbl.objects.filter(request_id=request_id_post).update(request_status="Rejected Quote")
                    messages.info(request, "You have rejected the LOI agreement. No further action is needed.")
                    return redirect('quoting')
                elif service_type=="Customs Brokerage":
                    customs_brokerage_tbl.objects.filter(request_id=request_id_post).update(request_status="Rejected Quote")
                    messages.info(request, "You have rejected the LOI agreement. No further action is needed.")
                    return redirect('quoting')
                else:
                    messages.error(request, "Unknown service type.")
                    return redirect('quoting')

            else:
                #messages.error(request, "Please sign the GSA agreement form first.")
                return redirect('quoting')

        # Default GET or fallback
        messages.success(request, "LOI agreement already signed.")
        messages.info(request, "Redirecting to Credit Application Form.")
        return redirect('credit_application_form')

    @login_required
    def loi_form(request):
        """Always allow access to LOI form, independent of credit status."""
        return render(request, "Documentations/LOI.html")

    @login_required
    def credit_application_form(request):
        user = request.user
        onboarding_status = onboarding.objects.filter(username=user).first()

        # Extract flags
        credit_signed = onboarding_status.credits_application_signed == "Yes" if onboarding_status else False
        loi_signed = onboarding_status.loi_signed == "Yes" if onboarding_status else False

        # ⚠️ Priority: Credit must be signed first if both are 'No'
        if not credit_signed and not loi_signed:
            messages.warning(request, "⚠️ Please complete the Credit Application before signing the LOI.")
            return render(request, "Documentations/credit_application.html")

        # Case: LOI not signed but Credit already signed → show LOI form
        if credit_signed and not loi_signed:
            messages.info(request, "ℹ️ Credit Application completed. Please complete the LOI Agreement next.")
            return render(request, "Documentations/LOI.html")

        # Case: Both LOI and Credit signed → show signed details
        if credit_signed and loi_signed:
            messages.info(request, "ℹ️ Credit Application and LOI Agreement are already completed.")
            return render(request, "Documentations/credit_application_signed_details.html")

        # Case: Credit not signed but LOI signed (unlikely, but possible) → allow credit form
        if not credit_signed and loi_signed:
            messages.warning(request, "⚠️ Credit Application is not yet submitted. Please complete it.")
            # Continue to show the credit form

        # Handle POST → submit Credit Application
        if request.method == "POST":
            already_submitted = credit_application.objects.filter(username=user).exists()
            if not already_submitted:
                credit_app = credit_application.objects.create(
                    username=user,
                    legal_trading_name=request.POST.get('legal_trading_name', '').capitalize().strip(),
                    operating_as=request.POST.get('operating_as', 'N/A').capitalize().strip(),
                    business_location=request.POST.get('business_location', '').capitalize().strip(),
                    telephone=request.POST.get('telephone', '').strip(),
                    length_in_business=request.POST.get('length_in_business', 'Less than 1 Year'),
                    type_of_business=request.POST.get('type_of_business', '').strip(),
                    bank_name=request.POST.get('bank_name', '').capitalize().strip(),
                    account_number=request.POST.get('account_number', '').strip(),
                    bank_address=request.POST.get('bank_address', '').strip(),
                    bank_fax=request.POST.get('bank_fax', 'N/A').strip(),
                    importer=request.POST.get('importer', 'N/A').strip()
                )

                # Insert multiple credit references
                referee_names = [name.capitalize().strip() for name in request.POST.getlist('referee_name[]')]
                referee_addresses = [addr.strip() for addr in request.POST.getlist('referee_address[]')]
                referee_phones = [phone.strip() for phone in request.POST.getlist('referee_phone[]')]
                for name, addr, phone in zip(referee_names, referee_addresses, referee_phones):
                    if name:
                        credit_references.objects.create(
                            id_reference_cred_app_table=credit_app,
                            referee_name=name,
                            referee_address=addr,
                            referee_phone=phone
                        )

                # Insert owner/officer addresses
                owner_names = [name.capitalize().strip() for name in request.POST.getlist('owner_name[]')]
                owner_titles = [title.strip() for title in request.POST.getlist('owner_title[]')]
                owner_addresses = [addr.strip() for addr in request.POST.getlist('owner_address[]')]
                owner_phones = [phone.strip() for phone in request.POST.getlist('owner_phone[]')]
                for name, title, addr, phone in zip(owner_names, owner_titles, owner_addresses, owner_phones):
                    if name:
                        address_of_owner_officer.objects.create(
                            id_reference_cred_app_table=credit_app,
                            owner_name=name,
                            owner_title=title,
                            owner_address=addr,
                            owner_phone=phone
                        )

                onboarding.objects.filter(username=user).update(
                    credits_application_signed="Yes"
                )

                messages.success(request, "✅ Credit Application submitted successfully!")
                return redirect("credit_application_form")

            else:
                messages.info(request, "ℹ️ You have already submitted this application. You can only update details.")
                return redirect("credit_application_form")

        # Default GET → Load credit application form
        return render(request, "Documentations/credit_application.html")

    @login_required
    def upload_documents(request):
        return render(request,"Documentations/documentation_upload_details.html")

