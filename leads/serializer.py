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


class AttachmentCreateSwaggerSerializer(serializers.Serializer):
    lead_id = serializers.UUIDField(help_text="UUID of the Lead to attach this file to")
    file_name = serializers.CharField(help_text="Name of the file")
    file_type = serializers.CharField(
        help_text="MIME type of the file (e.g., image/jpeg, application/pdf)",
        required=False,
    )
    file_url = serializers.URLField(help_text="URL of the file (from Cloudinary)")


class CompanySwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ("name",)


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ("id", "name", "email", "phone", "website")


class LeadListSerializer(serializers.ModelSerializer):
    # Use lead_title if available, otherwise use description as a fallback
    lead_name = serializers.SerializerMethodField()
    contact_name = serializers.CharField(source="contact.first_name", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    assigned_to_email = serializers.CharField(
        source="assigned_to.user.email", read_only=True
    )
    created_date = serializers.SerializerMethodField()

    def get_lead_name(self, obj):
        return obj.lead_title if obj.lead_title else obj.description

    class Meta:
        model = Lead
        fields = (
            "id",
            "lead_title",  # Added the direct lead_title field
            "lead_name",  # Keep the existing lead_name for backward compatibility
            "contact_name",
            "company_name",
            "lead_source",
            "status",
            "created_date",
            "assigned_to_email",
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
            "lead_title",
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
            "attachment_links",
            "lead_attachment",
            "lead_comments",
        )


class LeadCreateSerializer(serializers.ModelSerializer):
    lead_title = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )  # Optional lead title
    probability = serializers.IntegerField(max_value=100)
    assigned_to = serializers.UUIDField(required=True)  # Make assigned_to required
    contact = serializers.UUIDField(required=True)  # Make contact required
    company = serializers.UUIDField(required=True)  # Make company required
    description = serializers.CharField(required=True)  # Make description required
    status = serializers.CharField(required=True)  # Make status required
    converted = serializers.BooleanField(required=False)

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

        # Convert contact UUID to Contact instance
        if "contact" in validated_data:
            from contacts.models import Contact

            contact_id = validated_data.pop("contact")
            try:
                contact = Contact.objects.get(id=contact_id)
                validated_data["contact"] = contact
            except Contact.DoesNotExist:
                raise serializers.ValidationError({"contact": ["Invalid contact ID"]})

        # Convert company UUID to Company instance
        if "company" in validated_data:
            from companies.models import CompanyProfile

            company_id = validated_data.pop("company")
            try:
                company = CompanyProfile.objects.get(id=company_id)
                validated_data["company"] = company
            except CompanyProfile.DoesNotExist:
                raise serializers.ValidationError({"company": ["Invalid company ID"]})

        return super().create(validated_data)

    def update(self, instance, validated_data):
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

        # Convert contact UUID to Contact instance
        if "contact" in validated_data:
            from contacts.models import Contact

            contact_id = validated_data.pop("contact")
            try:
                contact = Contact.objects.get(id=contact_id)
                validated_data["contact"] = contact
            except Contact.DoesNotExist:
                raise serializers.ValidationError({"contact": ["Invalid contact ID"]})

        # Convert company UUID to Company instance
        if "company" in validated_data:
            from companies.models import CompanyProfile

            company_id = validated_data.pop("company")
            try:
                company = CompanyProfile.objects.get(id=company_id)
                validated_data["company"] = company
            except CompanyProfile.DoesNotExist:
                raise serializers.ValidationError({"company": ["Invalid company ID"]})

        return super().update(instance, validated_data)

    def validate(self, data):
        """
        Validate that essential fields are provided.
        """
        # The required fields are already handled by required=True attributes
        # The existence of Contact, Company, and Profile instances is checked in create/update methods

        return data

    # Removed validation methods for fields that no longer exist

    class Meta:
        model = Lead
        fields = (
            "lead_title",
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
            "attachment_links",
            # "lead_attachment",
            "converted",
        )


class LeadCreateSwaggerSerializer(serializers.ModelSerializer):
    lead_title = serializers.CharField(help_text="Title of the lead", required=False)
    description = serializers.CharField(
        help_text="Description of the lead", required=True
    )
    link = serializers.CharField(
        help_text="Related link (e.g., meeting notes, website)", required=False
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Potential deal amount",
        required=False,
    )
    probability = serializers.IntegerField(
        help_text="Probability of conversion (0-100)", min_value=0, max_value=100
    )
    status = serializers.CharField(
        help_text="Status of the lead (new, qualified, disqualified, recycled)",
        required=True,
    )
    lead_source = serializers.CharField(
        help_text="Source of the lead (call, email, existing customer, partner, public relations, campaign, website, other)",
        required=False,
    )
    notes = serializers.CharField(
        help_text="Additional notes about the lead", required=False
    )
    attachment_links = serializers.JSONField(
        help_text="JSON array of attachment links", required=False
    )
    assigned_to = serializers.UUIDField(
        help_text="UUID of the Profile to assign this lead to", required=True
    )
    contact = serializers.UUIDField(
        help_text="UUID of the Contact associated with this lead", required=True
    )
    company = serializers.UUIDField(
        help_text="UUID of the Company associated with this lead", required=True
    )
    converted = serializers.BooleanField(
        help_text="Whether this lead has been converted to an opportunity",
        required=False,
    )

    class Meta:
        model = Lead
        fields = [
            "lead_title",
            "description",
            "link",
            "amount",
            "probability",
            "status",
            "lead_source",
            "notes",
            "attachment_links",
            "assigned_to",
            "contact",
            "company",
            "organization",
            "lead_attachment",
            "converted",
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

class LeadDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ("id", "lead_title", "updated_at", "status", "converted_at")