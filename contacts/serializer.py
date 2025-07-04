from rest_framework import serializers

from common.serializer import (
    AttachmentsSerializer,
    BillingAddressSerializer,
    OrganizationSerializer,
    ProfileSerializer,
)
from companies.models import CompanyProfile
from companies.serializer import CompanyListSerializer
from contacts.models import Contact
from teams.serializer import TeamsSerializer


class ContactSerializer(serializers.ModelSerializer):
    teams = TeamsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    address = BillingAddressSerializer(read_only=True)
    get_team_users = ProfileSerializer(read_only=True, many=True)
    get_team_and_assigned_users = ProfileSerializer(read_only=True, many=True)
    get_assigned_users_not_in_teams = ProfileSerializer(read_only=True, many=True)
    contact_attachment = AttachmentsSerializer(read_only=True, many=True)
    date_of_birth = serializers.DateField()
    org = OrganizationSerializer()
    country = serializers.SerializerMethodField()
    company = CompanyListSerializer(read_only=True)
    created_by = ProfileSerializer(read_only=True)


    def get_country(self, obj):
        return obj.get_country_display()



    class Meta:
        model = Contact
        fields = (
            "id",
            "salutation",
            "first_name",
            "last_name",
            "date_of_birth",
            "organization",
            "title",
            "primary_email",
            "secondary_email",
            "mobile_number",
            "secondary_number",
            "department",
            "country",
            "language",
            "do_not_call",
            "address",
            "description",
            "linked_in_url",
            "facebook_url",
            "twitter_username",
            "contact_attachment",
            "assigned_to",
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
            "teams",
            "created_on_arrow",
            "get_team_users",
            "get_team_and_assigned_users",
            "get_assigned_users_not_in_teams",
            "org",
            "company",
        )

class ContactBasicSerializer(serializers.ModelSerializer):

    company = CompanyListSerializer(read_only=True)
    salutation_display = serializers.SerializerMethodField()
    language_display = serializers.SerializerMethodField()

    def get_salutation_display(self, obj):
        return obj.get_salutation_display() if obj.salutation else None

    def get_language_display(self, obj):
        return obj.get_language_display() if obj.language else None
    class Meta:
        model = Contact
        fields = (
            "id",
            "salutation",
            "salutation_display",  #  (Mr, Ms, etc.)
            "first_name",
            "last_name",
            "title",
            "primary_email",
            "mobile_number",
            "language",
            "language_display",    # (English, Spanish, etc.)
            "do_not_call",
            "description",
            "company",
        )
class CreateContactSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        if request_obj:
            self.org = request_obj.profile.org
            self.fields['company'].queryset = CompanyProfile.objects.filter(
                org=self.org
            )
    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            request = getattr(self, 'request_obj', None)

        if request and hasattr(request, 'profile') and request.profile:
            validated_data['org'] = request.profile.org

        return super().create(validated_data)

    def validate_first_name(self, first_name):
        if self.instance:
            if (
                Contact.objects.filter(first_name__iexact=first_name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Contact already exists with this name"
                )

        else:
            if Contact.objects.filter(
                first_name__iexact=first_name, org=self.org
            ).exists():
                raise serializers.ValidationError(
                    "Contact already exists with this name"
                )
        return first_name

    def validate_primary_email(self, primary_email):
        org = getattr(self, 'org', None)
        if not org:
            raise serializers.ValidationError("Organization not found")

        if self.instance:
            if (
                Contact.objects.filter(primary_email__iexact=primary_email, org=org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Contact with this email already exists"
                )
        else:
            if Contact.objects.filter(
                primary_email__iexact=primary_email, org=org
            ).exists():
                raise serializers.ValidationError(
                    "Contact with this email already exists"
                )
        return primary_email
    def validate_company(self, company):
        if company:
            org = getattr(self, 'org', None)
            if org and company.org != org:
                raise serializers.ValidationError(
                    "Company does not belong to your organization"
                )
        return company

    company = serializers.PrimaryKeyRelatedField(
        queryset=CompanyProfile.objects.all(),
        required=False,
        allow_null=True
    )
    class Meta:
        model = Contact
        fields = (

            "salutation",        #  Popup field for selecting a salutation
            "first_name",        #
            "last_name",         #
            "title",             #
            "primary_email",     #
            "mobile_number",     #
            "language",          # Popup field for selecting a language
            "do_not_call",       # Checkbox
            "description",
            "company",        #  Popup field for selecting a company
        )



class ContactDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    contact_attachment = serializers.FileField()

class ContactCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
