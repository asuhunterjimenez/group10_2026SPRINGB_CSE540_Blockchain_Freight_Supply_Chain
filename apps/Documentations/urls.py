from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from django.urls import include, path
from django.contrib.auth.decorators import login_required, permission_required
urlpatterns = [
   
   #path('',views.HomeView.login,name='login'),
   path('documentation_details', login_required(views.DocumentationsView.documentation_list), name='documentation_details'),
   path('view/<int:pk>/', login_required(views.DocumentationsView.documentation_view), name='documentation_view'),
   path('update/<int:pk>/', login_required(views.DocumentationsView.documentation_update), name='documentation_update'),
   path('upload/', login_required(views.DocumentationsView.upload_file), name='upload_file'),
   #path('upload/', views.upload_file, name='upload_file'),
   path('delete/', login_required(views.DocumentationsView.delete_file), name='delete_file'),
   path('onboarding_LOI_form/',login_required(views.DocumentationsView.onboarding_LOI_form),name='onboarding_LOI_form'),
   path('credit_application_form/',login_required(views.DocumentationsView.credit_application_form),name='credit_application_form'),
   path('apps/Documentations/LOI/', login_required(views.DocumentationsView.loi_form), name='loi_form'),
   #new
   path('upload_documents/',login_required(views.DocumentationsView.upload_documents),name='upload_documents'),
   path('get_user_files/', login_required(views.DocumentationsView.get_user_files), name='get_user_files'),
   


   
   

]
   # path('logout', views.HomeView.pagelogout, name='logout'),
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)