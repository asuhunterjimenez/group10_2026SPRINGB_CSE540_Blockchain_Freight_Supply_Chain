from django.contrib.auth.decorators import login_required
from apps.Helpers.decorators import group_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.conf import settings # import local_settings like emails,Apis accounts
from django.core.mail import send_mail #sending email


class Account_settings:

    @staticmethod
    @login_required
    @group_required(['clients_team', 'finance_team', 'sales_team'])
    def update_user_password(request):
        if request.method == 'POST':
            new_password = request.POST.get("new_password")
            user = request.user
            try:
                user.set_password(new_password)
                user.save()

                # sending USer accounts for clients on their email accounts
                subject = 'G10 Blockchain : Account Password Reset'
                recipient = [user.email]
                # HTML content formating message
                html_message = f"""
                    <p>Dear {user.first_name.capitalize()},</p>
                    <p>Your account password has been Successfully Reset.</p>
                    <p><font color=red>Change your password to a desirable one in Account settings >> Password Reset</font></p>
                    <p>
                        Username: <b>{user.username}</b><br>
                        Temporary Password: <b>{new_password}</b><br>
                        CRM URL: <a href="{settings.APP_URL}">Click Here</a>
                    </p>
                    <p>Thank you for choosing G10 Blockchain.</p>
                    <p>Contact details:<br>
                    Group team 10: Supply Chain based-Project<br>
                    CSE 540: Engr Blockchain Applications<br>
                    Semester: 2026 Spring B<br>
                    Arizona State University<br>
                    Tempe, AZ 85281<br>
                    USA
                    </p>
                    """

                plain_message = ""
                send_mail(
                    subject,
                    plain_message,
                    settings.EMAIL_HOST_USER,
                    recipient,
                    fail_silently=False,
                    html_message=html_message  # this will render HTML in email
                )

                messages.success(request, "Password updated successfully. Check Your Email Address Inbox Or Spam")
                #return render(request, 'Home/dashboard.html')
                return redirect(reverse('login'))
            except Exception as e:
                
                messages.error(request, f"Error updating password: {e}")
                return render(request, 'Account_settings/update_user_password.html')

        return render(request, 'Account_settings/update_user_password.html')
