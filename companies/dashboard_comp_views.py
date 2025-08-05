from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from common.swagger_params1 import organization_params
from contacts.models import Contact
from common.models import Org
from companies.models import CompanyProfile

@extend_schema(
    tags=["Dashboard"],
    parameters=[
        *organization_params,
        OpenApiParameter(
            name="company",
            description="Company ID to filter contacts by company",
            required=False,
            type=OpenApiTypes.UUID,
        )
    ],
    responses={200: "Top job titles data"}
)
class JobTitlesDistributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns top 5 job titles distribution for contacts in the organization
        Optionally filters by company ID
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

        # Base queryset for contacts in the organization
        contacts_qs = Contact.objects.filter(org=org)

        # Apply permissions filter
        if not is_admin:
            contacts_qs = contacts_qs.filter(Q(created_by=user) | Q(assigned_to=profile))

        # Apply company filter if provided
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

        # Get top 5 job titles distribution
        job_titles = (
            contacts_qs.exclude(title__isnull=True)
            .exclude(title__exact="")
            .values('title')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
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

        return Response({
            "error": False,
            "company": company_name,
            "total_contacts": total_contacts,
            "contacts_with_titles": contacts_with_titles,
            "job_titles": job_titles_data
        })