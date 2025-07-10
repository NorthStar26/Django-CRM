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


class LeadListSerializer(serializers.ModelSerializer):
    # Map "Lead Name" to the existing 'description' field
    lead_name = serializers.CharField(source='description', read_only=True)
    contact_name = serializers.CharField(source='contact.first_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    assigned_to_email = serializers.CharField(source='assigned_to.user.email', read_only=True)
    created_date = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = (
            'id',
            'lead_name',  # Now directly maps to description
            'contact_name',
            'company_name',
            'lead_source', 
            'status',
            'created_date',
            'assigned_to_email',
        )

    def get_created_date(self, obj):
        # Format: "March 12, 2023,"
        return obj.created_at.strftime("%B %d, %Y,") if obj.created_at else None
    
    

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
    assigned_to = serializers.UUIDField()  # Accept UUID for assigned_to

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org
        self.request_obj = request_obj

    def create(self, validated_data):
        # Convert 'org' to 'organization' if present
        if "org" in validated_data:
            validated_data["organization"] = validated_data.pop("org")

        # Convert assigned_to UUID to Profile instance
        if "assigned_to" in validated_data:
            from common.models import Profile

            assigned_to_id = validated_data.pop("assigned_to")
            try:
                profile = Profile.objects.get(
                    id=assigned_to_id, org=self.request_obj.profile.org
                )
                validated_data["assigned_to"] = profile
            except Profile.DoesNotExist:
                raise serializers.ValidationError(
                    {"assigned_to": ["Invalid profile ID"]}
                )

        return super().create(validated_data)

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
            # "lead_attachment",
        )


class LeadCreateSwaggerSerializer(serializers.ModelSerializer):
    description = serializers.CharField(help_text="Description of the lead")
    link = serializers.CharField(
        help_text="Related link (e.g., meeting notes, website)", required=False
    )
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, help_text="Potential deal amount"
    )
    probability = serializers.IntegerField(
        help_text="Probability of conversion (0-100)", min_value=0, max_value=100
    )
    status = serializers.CharField(
        help_text="Status of the lead (assigned, in process, converted, recycled, closed)"
    )
    lead_source = serializers.CharField(
        help_text="Source of the lead (call, email, existing customer, partner, public relations, campaign, website, other)"
    )
    notes = serializers.CharField(
        help_text="Additional notes about the lead", required=False
    )
    assigned_to = serializers.UUIDField(
        help_text="UUID of the Profile to assign this lead to"
    )
    contact = serializers.UUIDField(
        help_text="UUID of the Contact associated with this lead"
    )
    company = serializers.UUIDField(
        help_text="UUID of the Company associated with this lead"
    )

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
