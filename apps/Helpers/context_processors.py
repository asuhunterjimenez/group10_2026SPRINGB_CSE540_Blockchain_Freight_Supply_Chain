from django.conf import settings
from apps.Login.models import onboarding

def onboarding_status(request):
    if request.user.is_authenticated:
        onboarding1 = onboarding.objects.filter(
            username=request.user.username, gsa_signed='Yes'
        ).count()
    else:
        onboarding1 = 0
    return {"onboarding1": onboarding1}

def locationiq_key(request):
    return {
        "API_KEY": settings.API_KEY
    }

