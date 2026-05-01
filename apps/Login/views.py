from django.contrib.auth import (login as auth_login,  authenticate,logout)
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User #importing django default auth_user table
from django.contrib.auth.hashers import make_password #hashing password
from apps.Helpers.decorators import group_required
from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.mail import send_mail #sending email
from django.conf import settings # import local_settings like emails,Apis accounts
import re #validations
from django.core.validators import validate_email #validations
from django.core.exceptions import ValidationError #validations
from django.db import connection
from django.contrib import messages
from datetime import date, timedelta, datetime
from django.db import IntegrityError, transaction, connection # check intergity during user creation
import datetime
import string
import random
#setting time,date and time zone for create_client_user]
from django.utils import timezone
now1 = timezone.localtime()  # uses settings.TIME_ZONE automatically


#setting current date and time
today = date.today()
formatted_date = today.strftime("%d/%B/%Y")
now = datetime.datetime.now()
formatted_time = now.strftime("%H:%M:%S")
#setting date_joined
formatted_time2 = now.strftime("%Y-%m-%d %H:%M:%S%z")
#  Generate a unique request 
def generate_request_id():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # e.g. 20250727144532
    random_part = random.randint(1000, 9999)  # 4-digit random number
    return f"REQ{timestamp}{random_part}"
request_id = generate_request_id()

@login_required
@group_required(['admin','clients_team','finance_team','sales_team','ware_house'])
def dashboard(request):
   return render(request, 'Home/dashboard.html')


def login(request):
    _message = 'Please sign in'
    if request.method == 'POST':
        _username = request.POST.get('username', '').strip()
        _password = request.POST.get('password', '').strip()

        # Prevent empty username/password
        if not _username or not _password:
            messages.error(request, "Username and password are required.")
            return render(request, 'Login/login.html', {"message": _message})

        user = authenticate(username=_username, password=_password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Your account is not activated')
                messages.info(request,'Contact G10 Blockchain Freight for account activation via Email or on call')
        else:
            messages.error(request,'Invalid login, please try again.')
            messages.info(request, "If you don't remember your password, Click forgot password Or Sign Up for a new account")

    return render(request, 'Login/login.html', {"message": _message})


def pagelogout(request):
    auth_logout(request)  # make sure session clears
    return redirect('login')  # redirect instead of render


#generate temprarily password
def generate_temp_password(length=10):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

##Picks data from guests on the login page
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get("client_email", "").strip()

        # Prevent empty email submission
        if not email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request,"⚠️ Email Not Sent")
                messages.error(request,"⚠️ Email is required.")
            return redirect('/')  # redirect back to forgot password page

        # Generate a random temporary password
        temp_password = generate_temp_password()

        try:
            user = User.objects.get(email=email)
            # Set a new password
            user.set_password(temp_password)  # Django will hash automatically
            user.save()

            # Success message
            messages.success(request, "Password has been reset. Please check your email.")

            # Sending User accounts for clients on their email accounts
            subject = 'G10 Blockchain Freight : Account Password Reset'
            recipient = [email]

            # HTML formatted message
            html_message = f"""
                <p>Dear {user.first_name.capitalize()},</p>
                <p>Your account password has been successfully reset.</p>
                <p><font color=red>Please change your password to a desirable one in 
                <b>Account Settings → Password Reset</b></font></p>
                <p>
                    Username: <b>{user.username}</b><br>
                    Temporary Password: <b>{temp_password}</b><br>
                    CRM URL: <a href="{settings.APP_URL}">Click Here</a>
                </p>
                <p>Thank you for choosing G10 Blockchain Freight.</p>
                <p>Contact details:<br>
                customerservice@G10BlockchainFreight.com<br>
                sales@G10BlockchainFreight.com<br>
                3571 52nd Street SE, Level 1,<br>
                Calgary, Alberta T2B 3R3,<br>
                Canada
                </p>
            """

            send_mail(
                subject,
                "",  # plain text fallback
                settings.EMAIL_HOST_USER,
                recipient,
                fail_silently=False,
                html_message=html_message
            )

            return redirect('/')  # redirect to login page
        except User.DoesNotExist:
            messages.error(request, "Email does not exist.")
            return redirect('/')  # redirect back to forgot password page

    return render(request, 'Login/forgot_password.html')  # render forgot password page

def Create_client_user(request):
    if request.method == "POST":
        # --- Collect inputs ---
        first_name = request.POST.get("first_name", "").strip()
        second_name = request.POST.get("second_name", "").strip()
        username = request.POST.get("username", "").strip().lower()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()

        # --- Validations ---
        if not all([first_name, second_name, username, email, password]):
            messages.error(request, "⚠️ All fields are required!")
            return redirect("/")

        if not re.match(r'^[A-Za-z ]+$', first_name):
            messages.error(request, "⚠️ First Name should only contain letters.")
            return redirect("/")

        if not re.match(r'^[A-Za-z ]+$', second_name):
            messages.error(request, "⚠️ Second Name should only contain letters.")
            return redirect("/")

        if len(username) < 5:
            messages.error(request, "⚠️ Username must be at least 5 characters long.")
            return redirect("/")

        if len(password) < 5:
            messages.error(request, "⚠️ Password must be at least 5 characters long.")
            return redirect("/")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "⚠️ Enter a valid Email address.")
            return redirect("/")

        # --- Check duplicates (case-insensitive) ---
        username_exists = User.objects.filter(username__iexact=username).exists()
        email_exists = User.objects.filter(email__iexact=email).exists()

        if username_exists and email_exists:
            messages.error(request, "❌ Username and Email already exist.")
            return redirect("/")
        elif username_exists:
            messages.error(request, "❌ Username already exists. Choose another.")
            return redirect("/")
        elif email_exists:
            messages.error(request, "❌ Email already exists. Choose another.")
            return redirect("/")

        # --- Create user safely ---
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=second_name,
                    is_active=True,
                )

                # --- Add to group manually ---
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO auth_user_groups (user_id, group_id) VALUES (%s, %s)",
                        [user.id, 3]
                    )

        except IntegrityError:
            messages.error(request, "❌ Username or Email already exists.")
            return redirect("/")

        # --- Send email ---
        subject = 'G10 Blockchain Freight : Account Creation'
        recipient = [email]
        html_message = f"""
            <p>Dear {first_name.capitalize()},</p>
            <p>Your account has been created successfully. Login to complete the process and send quotes.</p>
            <p>
                Username: <b>{username}</b><br>
                Password: <b>{password}</b><br>
                CRM URL: <a href="{settings.APP_URL}">Click Here</a>
            </p>
            <p>Thank you for choosing G10 Blockchain Freight.</p>
            <p>Contact details:<br>
            customerservice@G10BlockchainFreight.com<br>
            sales@G10BlockchainFreight.com<br>
            3571 52nd Street SE, Level 1,<br>
            Calgary, Alberta T2B 3R3,<br>
            Canada
            </p>
        """

        send_mail(
            subject,
            "",  # plain fallback
            settings.EMAIL_HOST_USER,
            recipient,
            fail_silently=False,
            html_message=html_message
        )

        messages.success(request, "✅ User Created Successfully!")
        messages.success(request, "📧 Email Sent! Check your inbox for username and password.")
        return redirect("/")

    # Fallback for GET
    return render(request, "/")
