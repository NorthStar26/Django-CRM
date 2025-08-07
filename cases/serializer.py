from rest_framework import serializers
from cases.models import Case
from common.serializer import OrganizationSerializer, ProfileSerializer, UserSerializer
from contacts.serializer import ContactSerializer
from teams.serializer import TeamsSerializer
from opportunity.serializer import OpportunitySerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class CaseSerializer(serializers.ModelSerializer):
    account = serializers.SerializerMethodField()
    contacts = ContactSerializer(many=True, read_only=True)
    assigned_to = ProfileSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    teams = TeamsSerializer(many=True, read_only=True)
    org = OrganizationSerializer(read_only=True)
    opportunity = OpportunitySerializer(read_only=True)
    created_on_arrow = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = (
            "id",
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "description",
            "reason",
            "created_by",
            "created_at",
            "is_active",
            "account",
            "contacts",
            "teams",
            "assigned_to",
            "org",
            "created_on_arrow",
            "opportunity",
            "contract",
            "reason",
        )

    def get_created_on_arrow(self, obj):
        return obj.created_on_arrow if hasattr(obj, "created_on_arrow") else None

    def get_account(self, obj):
        if obj.account:
            from accounts.serializer import AccountSerializer

            return AccountSerializer(obj.account).data
        return None


class CaseListSerializer(serializers.ModelSerializer):
    priority = serializers.CharField()
    account_name = serializers.CharField(source="account.name", read_only=True)
    opportunity_name = serializers.CharField(source="opportunity.name", read_only=True)
    opportunity_data = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)
    expected_revenue = serializers.DecimalField(
        source="opportunity.expected_revenue",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Case
        fields = "__all__"

    def get_opportunity_data(self, obj):
        if obj.opportunity:
            return {
                "id": obj.opportunity.id,
                "name": obj.opportunity.name,
                "stage": obj.opportunity.stage,
                "amount": obj.opportunity.amount,
                "lead": {
                    "id": obj.opportunity.lead.id if obj.opportunity.lead else None,
                    "name": obj.opportunity.lead.lead_title
                    if obj.opportunity.lead
                    else None,
                    "contact": {
                        "id": obj.opportunity.lead.contact.id
                        if obj.opportunity.lead and obj.opportunity.lead.contact
                        else None,
                        "name": f"{obj.opportunity.lead.contact.first_name} {obj.opportunity.lead.contact.last_name}"
                        if obj.opportunity.lead and obj.opportunity.lead.contact
                        else None,
                    }
                    if obj.opportunity.lead
                    else None,
                    "company": {
                        "id": obj.opportunity.lead.company.id
                        if obj.opportunity.lead and obj.opportunity.lead.company
                        else None,
                        "name": obj.opportunity.lead.company.name
                        if obj.opportunity.lead and obj.opportunity.lead.company
                        else None,
                        "industry": obj.opportunity.lead.company.industry
                        if obj.opportunity.lead and obj.opportunity.lead.company
                        else None,
                    }
                    if obj.opportunity.lead
                    else None,
                }
                if obj.opportunity.lead
                else None,
            }
        return None


class CaseSwaggerUISerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["name", "industry", "contact", "org"]


class CaseCreateSerializer(serializers.ModelSerializer):
    closed_on = serializers.DateField()

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org

    def validate_name(self, name):
        if self.instance:
            if (
                Case.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Case already exists with this name")
        else:
            if Case.objects.filter(name__iexact=name, org=self.org).exists():
                raise serializers.ValidationError("Case already exists with this name")
        return name

    class Meta:
        model = Case
        fields = (
            "name",
            "status",
            "priority",
            "description",
            "reason",
            "created_by",
            "created_at",
            "is_active",
            "account",
            "org",
            "created_on_arrow",
        )


class CaseCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = (
            "name",
            "status",
            "priority",
            "case_type",
            "closed_on",
            "teams",
            "assigned_to",
            "account",
            "case_attachment",
            "contacts",
            "description",
            "reason",
        )


class CaseDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    case_attachment = serializers.FileField()


class CaseCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
