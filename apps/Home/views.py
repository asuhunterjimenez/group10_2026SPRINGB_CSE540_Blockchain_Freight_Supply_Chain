from django.contrib.auth import (login as auth_login,  authenticate,logout)

from django.contrib.auth.decorators import login_required, permission_required

from apps.Helpers.decorators import group_required

from django.shortcuts import render,redirect

from django.http import HttpResponseRedirect

from django.urls import reverse

from apps.Login.models import onboarding

from django.conf import settings

from django.http import JsonResponse

from apps.Login.models import ocean_freight_tbl,air_freight_tbl,roro_tbl,customs_brokerage_tbl,GSA_agreement_form_tbl

from django.db.models.functions import TruncMonth # for analytics

from django.db.models import Count # for analytics

from collections import defaultdict # for analytics
from django.utils import timezone
from django.db.models import Q

# Get current year and month
now = timezone.now()
current_year = now.year
current_month = now.month


class HomeView:


    @login_required

    @group_required(['admin','clients_team','finance_team','sales_team','ware_house'])

    def dashboard(request):

        user = request.user  # logged-in user

        # all these are clients

        # Ocean Freight

        ocean_data = (

            ocean_freight_tbl.objects.filter(id_gsa_ref__username=user.username)

            .annotate(month=TruncMonth("date_received"))

            .values("month")

            .annotate(count=Count("id"))

            .order_by("month")
        )


        # Air Freight

        air_data = (

            air_freight_tbl.objects.filter(id_gsa_ref__username=user.username)

            .annotate(month=TruncMonth("date_received"))

            .values("month")

            .annotate(count=Count("id"))

            .order_by("month")
        )


        # RORO

        roro_data = (

            roro_tbl.objects.filter(id_gsa_ref__username=user.username)

            .annotate(month=TruncMonth("date_received"))

            .values("month")

            .annotate(count=Count("id"))

            .order_by("month")
        )


        # Customs Brokerage

        customs_data = (

            customs_brokerage_tbl.objects.filter(id_gsa_ref__username=user.username)

            .annotate(month=TruncMonth("date_received"))

            .values("month")

            .annotate(count=Count("id"))

            .order_by("month")
        )
        
        #Quote Count by  Freight
        # Get the most recent month's count, or 0 if no data
        # Quote Count by Freight
        ocean_last = ocean_data.last()
        ocean_count_monthly = ocean_last["count"] if ocean_last else 0

        air_last = air_data.last()
        air_count_monthly = air_last["count"] if air_last else 0

        roro_last = roro_data.last()
        roro_count_monthly = roro_last["count"] if roro_last else 0

        customs_last = customs_data.last()
        customs_count_monthly = customs_last["count"] if customs_last else 0

        total_quotes_monthly = (
            ocean_count_monthly + air_count_monthly + roro_count_monthly + customs_count_monthly
        )

        # Calculate Percentages safely
        ocean_monthly_percentage   = (ocean_count_monthly / total_quotes_monthly * 100) if total_quotes_monthly else 0
        air_monthly_percentage     = (air_count_monthly / total_quotes_monthly * 100) if total_quotes_monthly else 0
        roro_monthly_percentage    = (roro_count_monthly / total_quotes_monthly * 100) if total_quotes_monthly else 0
        customs_monthly_percentage = (customs_count_monthly / total_quotes_monthly * 100) if total_quotes_monthly else 0


      #pending

        # Count pending cases separately

        ocean_pending = ocean_freight_tbl.objects.filter(

            id_gsa_ref__username=user.username, request_status="Draft"
        ).count()


        air_pending = air_freight_tbl.objects.filter(

            id_gsa_ref__username=user.username, request_status="Draft"
        ).count()


        roro_pending = roro_tbl.objects.filter(

            id_gsa_ref__username=user.username, request_status="Draft"
        ).count()


        customs_pending = customs_brokerage_tbl.objects.filter(

            id_gsa_ref__username=user.username, request_status="Draft"
        ).count()


        # Total pending from all tables

        total_pending = ocean_pending + air_pending + roro_pending + customs_pending
      

        #accepted Quotes per month
        # Count accepted quotes for current month
        ocean_count_accepted = ocean_freight_tbl.objects.filter(
            id_gsa_ref__username=user.username,
            request_status="Approved Quote",
            updated_date_time__year=current_year,
            updated_date_time__month=current_month
        ).count()

        air_count_accepted = air_freight_tbl.objects.filter(
            id_gsa_ref__username=user.username,
            request_status="Approved Quote",
            updated_date_time__year=current_year,
            updated_date_time__month=current_month
        ).count()

        roro_count_accepted = roro_tbl.objects.filter(
            id_gsa_ref__username=user.username,
            request_status="Approved Quote",
            updated_date_time__year=current_year,
            updated_date_time__month=current_month
        ).count()

        customs_count_accepted = customs_brokerage_tbl.objects.filter(
            id_gsa_ref__username=user.username,
            request_status="Approved Quote",
            updated_date_time__year=current_year,
            updated_date_time__month=current_month
        ).count()

        # Total accepted quotes this month
        total_accepted_monthly = ocean_count_accepted + air_count_accepted + roro_count_accepted + customs_count_accepted

        #monthly rejected Quotes counts
        ocean_count_rejected = ocean_freight_tbl.objects.filter(
            id_gsa_ref__username=user.username,
            request_status="Rejected Quote",
            updated_date_time__year=current_year,
            updated_date_time__month=current_month
        ).count()

        air_count_rejected = air_freight_tbl.objects.filter(
            id_gsa_ref__username=user.username,
            request_status="Rejected Quote",
            updated_date_time__year=current_year,
            updated_date_time__month=current_month
        ).count()

        roro_count_rejected = roro_tbl.objects.filter(
            id_gsa_ref__username=user.username,
            request_status="Rejected Quote",
            updated_date_time__year=current_year,
            updated_date_time__month=current_month
        ).count()

        customs_count_rejected = customs_brokerage_tbl.objects.filter(
            id_gsa_ref__username=user.username,
            request_status="Rejected Quote",
            updated_date_time__year=current_year,
            updated_date_time__month=current_month
        ).count()

        # Total rejected quotes this month
        total_rejected_monthly = ocean_count_rejected + air_count_rejected + roro_count_rejected + customs_count_rejected

        return render(
            request,
            "Home/dashboard.html",
            {   "now":now,
                "ocean_data": list(ocean_data),
                "air_data": list(air_data),
                "roro_data": list(roro_data),
                "customs_data": list(customs_data),
                "total_pending": total_pending,
                "total_accepted_monthly":total_accepted_monthly,
                "total_rejected_monthly":total_rejected_monthly,
                "ocean_count_monthly":ocean_count_monthly,
                "air_count_monthly":air_count_monthly,
                "roro_count_monthly":roro_count_monthly,
                "customs_count_monthly":customs_count_monthly,
                "ocean_monthly_percentage":ocean_monthly_percentage,

            },
        )

    #return render(request, 'Home/dashboard.html')


    #def analytics(request):
        
        