from rest_framework import serializers

from accounts.models import Tags
from common.serializer import (
    AttachmentsSerializer,
    LeadCommentSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer
from leads.models import Lead
from companies.models import CompanyProfile


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class CompanySwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ("name",)


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ("id", "name", "email", "phone", "website")


class LeadSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)
    assigned_to = ProfileSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    lead_attachment = AttachmentsSerializer(read_only=True, many=True)
    lead_comments = LeadCommentSerializer(read_only=True, many=True)

    class Meta:
        model = Lead
        fields = (
            "id",
            "description",
            "link",
            "amount",
            "probability",
            "status",
            "lead_source",
            "notes",
            "assigned_to",
            "contact",
            "company",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "organization",
            "lead_attachment",
            "lead_comments",
        )


class LeadCreateSerializer(serializers.ModelSerializer):
    probability = serializers.IntegerField(max_value=100)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org

    # Removed validation methods for fields that no longer exist

    class Meta:
        model = Lead
        fields = (
            "description",
            "link",
            "amount",
            "probability",
            "status",
            "lead_source",
            "notes",
            "assigned_to",
            "contact",
            "company",
            "organization",
            "industry",
            "company",
            "organization",
            "probability",
            "close_date",
            # "lead_attachment",
        )


class LeadCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            "description",
            "link",
            "amount",
            "probability",
            "status",
            "lead_source",
            "notes",
            "assigned_to",
            "contact",
            "company",
            "organization",
            "lead_attachment",
        ]


class CreateLeadFromSiteSwaggerSerializer(serializers.Serializer):
    apikey = serializers.CharField()
    description = serializers.CharField()
    link = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    probability = serializers.IntegerField(required=False)
    status = serializers.CharField()
    lead_source = serializers.CharField()
    notes = serializers.CharField(required=False)


class LeadDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    lead_attachment = serializers.FileField()


class LeadCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()


class LeadUploadSwaggerSerializer(serializers.Serializer):
    leads_file = serializers.FileField()
