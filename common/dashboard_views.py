from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from companies.models import CompanyProfile
from contacts.models import Contact
from leads.models import Lead
from opportunity.models import Opportunity
from opportunity.serializer import OpportunitySerializer
from leads.serializer import LeadSerializer, LeadDashboardSerializer
from opportunity.serializer import OpportunityDashboardSerializer
from common.swagger_params1 import organization_params
from django.db.models import Count, Sum, Q, Max
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from common.models import Org
from datetime import datetime, timedelta
from common.utils import LEAD_STATUS
from common.utils import LEAD_STATUS
from accounts.models import Account

OPPORTUNITY_STAGES = [
    ("QUALIFICATION", "QUALIFICATION"),
    ("IDENTIFY_DECISION_MAKERS", "Identify Decision Makers"),
    ("PROPOSAL", "Proposal"),
    ("NEGOTIATION", "Negotiation"),
]


@extend_schema(
    tags=["Dashboard"],
    parameters=organization_params,
    responses={200: "Dashboard summary data"}
)
class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        lead_status = request.query_params.get("lead_status")
        opportunity_stage = request.query_params.get("opportunity_stage")
        days = request.query_params.get("days")

        # --- фильтры для дат ---
        date_filter = {}
        if days:
            try:
                days = int(days)
                date_from = datetime.now() - timedelta(days=days)
                date_filter = {"created_at__gte": date_from}
            except Exception:
                pass

        if is_admin:
            company_filter = {}
            contact_filter = {}
            lead_filter = {}
            opportunity_filter = {}
        else:
            company_filter = {"created_by": user}
            contact_filter = {"created_by": user}
            lead_filter = Q(created_by=user) | Q(assigned_to=profile)
            opportunity_filter = Q(created_by=user) | Q(assigned_to=profile)

        # --- Companies ---
        companies_count = CompanyProfile.objects.filter(org=org, **company_filter, **date_filter).count()
        # --- Contacts ---
        contacts_count = Contact.objects.filter(org=org, **contact_filter, **date_filter).count()
        # --- Accounts ---
        accounts_qs = Account.objects.filter(org=org, **date_filter)
        if not is_admin:
            accounts_qs = accounts_qs.filter(Q(created_by=user) | Q(assigned_to=profile)).distinct()
        accounts_count = accounts_qs.count()
        # --- Leads ---
        leads_qs = Lead.objects.filter(organization=org, **date_filter)
        if not is_admin:
            leads_qs = leads_qs.filter(lead_filter).distinct()
        if lead_status:
            leads_qs = leads_qs.filter(status=lead_status)
        leads_count = leads_qs.count()
        # --- Opportunities ---
        opps_qs = Opportunity.objects.filter(org=org, **date_filter)
        if not is_admin:
            opps_qs = opps_qs.filter(opportunity_filter).distinct()
        if opportunity_stage:
            opps_qs = opps_qs.filter(stage=opportunity_stage)
        opportunities_count = opps_qs.count()

        # Recent Leads
        recent_leads_qs = leads_qs.order_by("-updated_at")[:5]
        recent_leads = LeadDashboardSerializer(recent_leads_qs, many=True).data
        # Recent Opportunities
        recent_opps_qs = opps_qs.order_by("-updated_at")[:5]
        recent_opps = OpportunityDashboardSerializer(recent_opps_qs, many=True).data

        # Pipeline Value (total)
        total_pipeline_value = opps_qs.aggregate(total=Sum("expected_revenue"))["total"] or 0
        total_pipeline_value = round(total_pipeline_value, 3)

        # Leads by Status
        leads_by_status = (
            leads_qs.values("status").annotate(count=Count("id"))
        )
        leads_status = {item["status"]: item["count"] for item in leads_by_status}

        # Opportunities by Stage
        opps_by_stage = (
            opps_qs.values("stage").annotate(count=Count("id"))
        )
        opps_stage = {item["stage"]: item["count"] for item in opps_by_stage}

        return Response({
    "companies_count": companies_count,
    "contacts_count": contacts_count,
    "accounts_count": accounts_count,
    "leads_count": leads_count,
    "opportunities_count": opportunities_count,
    "total_pipeline_value": total_pipeline_value,
    "leads_by_status": leads_status,
    "opportunities_by_stage": opps_stage,
    "recent_leads": recent_leads,
    "recent_opportunities": recent_opps,
    "lead_status_choices": [
        {"value": choice[0], "label": choice[1]}
        for choice in LEAD_STATUS
    ],    "opportunity_stage_choices": [
        {"value": choice[0], "label": choice[1]}
        for choice in OPPORTUNITY_STAGES
    ],
})