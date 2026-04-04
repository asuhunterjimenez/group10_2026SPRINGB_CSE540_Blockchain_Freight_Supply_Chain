from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required, permission_required
urlpatterns = [
   path('update_user_password', login_required(views.Account_settings.update_user_password), name='update_user_password'),
   
]
