from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required, permission_required


urlpatterns = [
   #path('',views.HomeView.login,name='login'),
   path('dashboard', login_required(views.HomeView.dashboard), name='dashboard'),

   # path('logout', views.HomeView.pagelogout, name='logout'),



    
]
