from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
   #path('',views.HomeView.login,name='login'),
   path('quoting', login_required(views.QuotingView.quoting_list), name='quoting'),
   path('GSA_agreement_form',login_required(views.QuotingView.GSA_agreement_form),name='GSA_agreement'),
   path('quoting_request', login_required(views.QuotingView.quoting_request), name='quoting_request'),
   path('download/<str:request_id>/<str:filename>/', views.QuotingView.download_file, name='download_file'),
   path("quotes/update/<str:request_id>/", views.QuotingView.update_quote, name="update_quote"),
   path('single_lock_case', login_required(views.QuotingView.single_lock_case), name='lock_single_case'),
   path("apps/Quotings/quotes/update/", views.QuotingView.update_quotes_response, name="update_quotes_response"),
   path("apps/Quotings/quotes_client/update/", views.QuotingView.update_client_quotes_response, name="update_client_quotes_response"),
   path("quotes/client_update/<str:request_id>/", views.QuotingView.client_update_quote, name="client_update_quote"),
   path("quotes/client_view/<str:request_id>/", views.QuotingView.client_view_quote, name="client_view_quote"),
   # path('onboarding_LOI_form/',login_required(views.QuotingView.onboarding_LOI_form),name='onboarding_LOI_form'),
   


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

