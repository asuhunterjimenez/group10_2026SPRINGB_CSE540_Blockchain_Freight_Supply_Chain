from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required, permission_required
urlpatterns = [
 path('',views.login,name='login'), # Login URL
 path('', views.pagelogout, name='logout'), # Logout URL
 path('forgot-password', views.forgot_password, name='forgot_password'),
 path('create-client-user/',views.Create_client_user,name='Create_client_user'),

    
]
