from rest_framework import serializers

from accounts.models import Account, Tags
from common.serializer import (
    AttachmentsSerializer,
    LeadCommentSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    UserSerializer,
)
from contacts.serializer import ContactSerializer
from leads.models import Company, Lead
from teams.serializer import TeamsSerializer


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class CompanySwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("name",)

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("id", "name", "org")


class LeadSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)
    assigned_to = ProfileSerializer(read_only=True)
    created_by = UserSerializer()
    lead_attachment = AttachmentsSerializer(read_only=True, many=True)
    lead_comments = LeadCommentSerializer(read_only=True, many=True)
    
    class Meta:
        model = Lead
        # fields = '__all__'
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
            "organization",
            "created_by",
            "created_at",
            "updated_at",
            "lead_attachment",
            "lead_comments",
        )


class LeadCreateSerializer(serializers.ModelSerializer):
    probability = serializers.IntegerField(max_value=100)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        if self.initial_data and self.initial_data.get("status") == "converted":
            self.fields["link"].required = True
        self.fields["description"].required = False
        self.org = request_obj.profile.org

        if self.instance:
            if hasattr(self.instance, 'created_from_site') and self.instance.created_from_site:
                prev_choices = self.fields["lead_source"]._get_choices()
                prev_choices = prev_choices + [("micropyramid", "Micropyramid")]
                self.fields["lead_source"]._set_choices(prev_choices)

    def validate_link(self, link):
        if self.instance:
            if (
                Account.objects.filter(name__iexact=link, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Account already exists with this name"
                )
        else:
            if Account.objects.filter(name__iexact=link, org=self.org).exists():
                raise serializers.ValidationError(
                    "Account already exists with this name"
                )
        return link

    # Title field is no longer in the model, so we don't need this validation
    # def validate_title(self, title):
    #     if self.instance:
    #         if (
    #             Lead.objects.filter(title__iexact=title, organization=self.org)
    #             .exclude(id=self.instance.id)
    #             .exists()
    #         ):
    #             raise serializers.ValidationError("Lead already exists with this title")
    #     else:
    #         if Lead.objects.filter(title__iexact=title, organization=self.org).exists():
    #             raise serializers.ValidationError("Lead already exists with this title")
    #     return title

    class Meta:
        model = Lead
        fields = (
            "description",
            "link",
            "amount",
            "status",
            "lead_source",
            "notes",
            "contact",
            "company",
            "organization",
            "probability",
            # "lead_attachment",
        )

class LeadCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["description","link","amount","probability","status","lead_source","notes",
                 "assigned_to","contact","company","organization","lead_attachment"]


class CreateLeadFromSiteSwaggerSerializer(serializers.Serializer):
    apikey=serializers.CharField()
    description=serializers.CharField()
    link=serializers.CharField()
    amount=serializers.DecimalField(max_digits=12, decimal_places=2)
    probability=serializers.IntegerField()
    status=serializers.CharField()
    lead_source=serializers.CharField()
    notes=serializers.CharField()


class LeadDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    lead_attachment = serializers.FileField()

class LeadCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()

class LeadUploadSwaggerSerializer(serializers.Serializer):
    leads_file = serializers.FileField()

