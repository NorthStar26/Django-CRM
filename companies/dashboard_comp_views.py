# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from django.db.models import Count, Q
# from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
# from common.swagger_params1 import organization_params
# from contacts.models import Contact
# from common.models import Org
# from companies.models import CompanyProfile
# from leads.models import Lead
# from common.utils import LEAD_STATUS

# @extend_schema(
#     tags=["Dashboard"],
#     parameters=[
#         *organization_params,
#         OpenApiParameter(
#             name="company",
#             description="Company ID to filter contacts by company",
#             required=False,
#             type=OpenApiTypes.UUID,
#         )
#     ],
#     responses={200: "Top job titles data"}
# )
# class JobTitlesDistributionView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """
#         Returns top 5 job titles distribution for contacts in the organization
#         Optionally filters by company ID
#         """
#         if not hasattr(request, "profile") or request.profile is None:
#             return Response(
#                 {"error": True, "message": "User profile not found or not authenticated."},
#                 status=401,
#             )

#         user = request.profile.user
#         profile = request.profile

#         is_admin = (
#             profile.role in ["ADMIN", "MANAGER"] or request.user.is_superuser
#         )
#         org_id = request.headers.get("org")
#         if not org_id:
#             return Response(
#                 {"error": True, "message": "Organization header 'org' is required."},
#                 status=401,
#             )
#         org = Org.objects.filter(id=org_id).first()
#         if not org:
#             return Response(
#                 {"error": True, "message": "Organization not found."},
#                 status=404,
#             )

#         # Get optional company filter
#         company_id = request.query_params.get("company")

#         # Base queryset for contacts in the organization
#         contacts_qs = Contact.objects.filter(org=org)

#         # Apply permissions filter
#         if not is_admin:
#             contacts_qs = contacts_qs.filter(Q(created_by=user) | Q(assigned_to=profile))

#         # Apply company filter if provided
#         if company_id:
#             try:
#                 company = CompanyProfile.objects.get(id=company_id, org=org)
#                 contacts_qs = contacts_qs.filter(company=company)
#                 company_name = company.name
#             except CompanyProfile.DoesNotExist:
#                 return Response(
#                     {"error": True, "message": "Company not found."},
#                     status=404,
#                 )
#         else:
#             company_name = "All Companies"

#         # Get top 5 job titles distribution
#         job_titles = (
#             contacts_qs.exclude(title__isnull=True)
#             .exclude(title__exact="")
#             .values('title')
#             .annotate(count=Count('id'))
#             .order_by('-count')[:5]
#         )

#         # Total number of contacts with titles
#         contacts_with_titles = sum(item['count'] for item in job_titles)

#         # Total number of contacts (including those without titles)
#         total_contacts = contacts_qs.count()

#         # Format response data
#         job_titles_data = [{
#             'title': item['title'],
#             'count': item['count'],
#             'percentage': round((item['count'] / total_contacts * 100), 1) if total_contacts > 0 else 0
#         } for item in job_titles]



#         # ----- LEADS INFORMATION -----
#         # Base queryset for leads in the organization
#         leads_qs = Lead.objects.select_related('company', 'contact').filter(organization=org)
#         # Apply permissions filter for leads
#         if not is_admin:
#             leads_qs = leads_qs.filter(Q(created_by=user) | Q(assigned_to=profile)).distinct()

#         # Apply company filter to leads if provided
#         if company_id and company:
#             leads_qs = leads_qs.filter(company=company)

#         # Get total leads count
#         total_leads = leads_qs.count()

#         # Group leads by status
#         leads_by_status = leads_qs.values("status").annotate(count=Count("id"))
#         leads_status = {item["status"]: item["count"] for item in leads_by_status}

#         # Format response data for leads by status
#         leads_status_data = []
#         for status_choice in LEAD_STATUS:
#             status_value = status_choice[0]
#             status_label = status_choice[1]
#             count = leads_status.get(status_value, 0)
#             percentage = round((count / total_leads * 100), 1) if total_leads > 0 else 0

#             leads_status_data.append({
#                 'status': status_value,
#                 'label': status_label,
#                 'count': count,
#                 'percentage': percentage
#             })

#         return Response({
#             "error": False,
#             "company": company_name,
#             "company_id": company_id if company else None,
#             "total_contacts": total_contacts,
#             "contacts_with_titles": contacts_with_titles,
#             "job_titles": job_titles_data,
#             "total_leads": total_leads,
#             "leads_by_status": leads_status_data,
#             "lead_status_choices": [
#                 {"value": choice[0], "label": choice[1]}
#                 for choice in LEAD_STATUS
#             ]
#         })
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from common.swagger_params1 import organization_params
from contacts.models import Contact
from common.models import Org
from companies.models import CompanyProfile
from leads.models import Lead
from common.utils import LEAD_STATUS

@extend_schema(
    tags=["Dashboard"],
    parameters=[
        *organization_params,
        OpenApiParameter(
            name="company",
            description="Company ID to filter contacts by company",
            required=False,
            type=OpenApiTypes.UUID,
        ),
        OpenApiParameter(
            name="limit",
            description="Limit for number of job titles to return (default is 5)",
            required=False,
            type=OpenApiTypes.INT,
        )
    ],
    responses={200: "Company dashboard data"}
)
class JobTitlesDistributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns job titles distribution for contacts in the organization
        and leads information grouped by status for the selected company.
        You can specify the number of job titles to return with the 'limit' parameter.
        """
        if not hasattr(request, "profile") or request.profile is None:
            return Response(
                {"error": True, "message": "User profile not found or not authenticated."},
                status=401,
            )

        user = request.profile.user
        profile = request.profile

        is_admin = (
            profile.role in ["ADMIN", "MANAGER"] or request.user.is_superuser
        )
        org_id = request.headers.get("org")
        if not org_id:
            return Response(
                {"error": True, "message": "Organization header 'org' is required."},
                status=401,
            )
        org = Org.objects.filter(id=org_id).first()
        if not org:
            return Response(
                {"error": True, "message": "Organization not found."},
                status=404,
            )

        # Get optional company filter
        company_id = request.query_params.get("company")

        # Get optional limit parameter (default is 5)
        try:
            limit = int(request.query_params.get("limit", 5))
            if limit < 1:
                limit = 5  # Min limit is 1
            elif limit > 50:
                limit = 50  # Max limit is 50 to prevent performance issues
        except (ValueError, TypeError):
            limit = 5

        # Base queryset for contacts in the organization
        contacts_qs = Contact.objects.select_related('company').filter(org=org)

        # Apply permissions filter
        if not is_admin:
            contacts_qs = contacts_qs.filter(Q(created_by=user) | Q(assigned_to=profile))

        # Apply company filter if provided
        company = None
        if company_id:
            try:
                company = CompanyProfile.objects.get(id=company_id, org=org)
                contacts_qs = contacts_qs.filter(company=company)
                company_name = company.name
            except CompanyProfile.DoesNotExist:
                return Response(
                    {"error": True, "message": "Company not found."},
                    status=404,
                )
        else:
            company_name = "All Companies"

        # Get job titles distribution with dynamic limit
        job_titles = (
            contacts_qs.exclude(title__isnull=True)
            .exclude(title__exact="")
            .values('title')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]  # Use the limit parameter
        )

        # Total number of contacts with titles
        contacts_with_titles = sum(item['count'] for item in job_titles)

        # Total number of contacts (including those without titles)
        total_contacts = contacts_qs.count()

        # Format response data
        job_titles_data = [{
            'title': item['title'],
            'count': item['count'],
            'percentage': round((item['count'] / total_contacts * 100), 1) if total_contacts > 0 else 0
        } for item in job_titles]

        # ----- LEADS INFORMATION -----
        # Base queryset for leads in the organization
        leads_qs = Lead.objects.select_related('company', 'contact').filter(organization=org)
        # Apply permissions filter for leads
        if not is_admin:
            leads_qs = leads_qs.filter(Q(created_by=user) | Q(assigned_to=profile)).distinct()

        # Apply company filter to leads if provided
        if company_id and company:
            leads_qs = leads_qs.filter(company=company)

        # Get total leads count
        total_leads = leads_qs.count()

        # Group leads by status
        leads_by_status = leads_qs.values("status").annotate(count=Count("id"))
        leads_status = {item["status"]: item["count"] for item in leads_by_status}

        # Format response data for leads by status
        leads_status_data = []
        for status_choice in LEAD_STATUS:
            status_value = status_choice[0]
            status_label = status_choice[1]
            count = leads_status.get(status_value, 0)
            percentage = round((count / total_leads * 100), 1) if total_leads > 0 else 0

            leads_status_data.append({
                'status': status_value,
                'label': status_label,
                'count': count,
                'percentage': percentage
            })

        return Response({
            "error": False,
            "company": company_name,
            "company_id": company_id if company else None,
            "total_contacts": total_contacts,
            "contacts_with_titles": contacts_with_titles,
            "job_titles_limit": limit,  # Return the used limit
            "job_titles": job_titles_data,
            "total_leads": total_leads,
            "leads_by_status": leads_status_data,
            "lead_status_choices": [
                {"value": choice[0], "label": choice[1]}
                for choice in LEAD_STATUS
            ]
        })