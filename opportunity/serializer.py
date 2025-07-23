from rest_framework import serializers
from companies.serializer import CompanyDetailSerializer
from contacts.serializer import ContactSerializer

from accounts.models import Tags
from accounts.serializer import AccountSerializer
from common.serializer import AttachmentsSerializer, ProfileSerializer, UserSerializer
from contacts.serializer import ContactSerializer
from opportunity.models import Opportunity
from teams.serializer import TeamsSerializer
from common.utils import PIPELINE_CONFIG
from common.models import Attachments
from companies.serializer import CompanyListSerializer

class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


from rest_framework import serializers
from opportunity.models import Opportunity
from accounts.models import Tags
from accounts.serializer import AccountSerializer
from common.serializer import (
    AttachmentsSerializer,
    ProfileSerializer,
    UserSerializer
)
from contacts.serializer import ContactSerializer
from teams.serializer import TeamsSerializer


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class OpportunitySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    closed_by = ProfileSerializer()
    created_by = UserSerializer()
    tags = TagsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    meeting_date = serializers.DateField()
    attachment_links = serializers.JSONField()
    days_to_close = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    opportunity_attachment = AttachmentsSerializer(many=True, read_only=True)

    class Meta:
        model = Opportunity
        fields = (
            "id",
            "name",
            "stage",
            "currency",
            "amount",
            "lead_source",
            "probability",
            "contacts",
            "closed_by",
            "closed_on",
            "description",
            "assigned_to",
            "created_by",
            "created_at",
            "is_active",
            "tags",
            "opportunity_attachment",
            "teams",
            "created_on_arrow",
            "account",
            "expected_revenue",
            "expected_close_date",
            "meeting_date",
            "attachment_links",
            "days_to_close",
            "company",
            "contact",
            "company_name"
        )

    def get_days_to_close(self, obj):
        if obj.expected_close_date and obj.created_at:
            return (obj.expected_close_date - obj.created_at.date()).days
        return None

    def get_company(self, obj):
        if hasattr(obj, 'lead') and obj.lead and obj.lead.company:
            from companies.serializer import CompanyListSerializer
            return CompanyListSerializer(obj.lead.company).data
        elif hasattr(obj, 'account') and obj.account and hasattr(obj.account, 'company') and obj.account.company:
            from companies.serializer import CompanyListSerializer
            return CompanyListSerializer(obj.account.company).data
        return None

    def get_contact(self, obj):
        if hasattr(obj, 'lead') and obj.lead and obj.lead.contact:
            from contacts.serializer import ContactSerializer
            return ContactSerializer(obj.lead.contact).data
        elif obj.contacts.exists():
            from contacts.serializer import ContactSerializer
            return ContactSerializer(obj.contacts.first()).data
        return None


class OpportunityCreateSerializer(serializers.ModelSerializer):
    probability = serializers.IntegerField(max_value=100)
    closed_on = serializers.DateField
    expected_revenue = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False, allow_null=True
    )
    expected_close_date = serializers.DateField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org

    def validate_name(self, name):
        if self.instance:
            if (
                Opportunity.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Opportunity already exists with this name"
                )

        else:
            if Opportunity.objects.filter(name__iexact=name, org=self.org).exists():
                raise serializers.ValidationError(
                    "Opportunity already exists with this name"
                )
        return name

    class Meta:
        model = Opportunity
        fields = (
            "name",
            "account",
            "stage",
            "currency",
            "amount",
            "lead_source",
            "probability",
            "closed_on",
            "description",
            "created_by",
            "created_at",
            "is_active",
            "created_on_arrow",
            "org",
            # "get_team_users",
            # "get_team_and_assigned_users",
            # "get_assigned_users_not_in_teams",
            "expected_revenue",
            "expected_close_date",
        )


class OpportunityCreateSwaggerSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField()
    opportunity_attachment = serializers.FileField()
    expected_revenue = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False, allow_null=True
    )
    expected_close_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Opportunity
        fields = (
            "name",
            "account",
            "amount",
            "currency",
            "stage",
            "teams",
            "lead_source",
            "probability",
            "description",
            "assigned_to",
            "contacts",
            "due_date",
            "tags",
            "opportunity_attachment",
            "expected_revenue",
            "expected_close_date",
        )


class OpportunityDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    opportunity_attachment = serializers.FileField()


class OpportunityCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()

class OpportunityPipelineSerializer(serializers.ModelSerializer):
    """ Serializer for Opportunity в pipeline"""
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    contacts_info = ContactSerializer(source='contacts', many=True, read_only=True)
    assigned_to_info = ProfileSerializer(source='assigned_to', many=True, read_only=True)
    attachments = AttachmentsSerializer(source='opportunity_attachment', many=True, read_only=True)
    # attachments = serializers.SerializerMethodField()
    # def get_attachments(self, obj):
    #     from common.serializer import AttachmentsSerializer
    #     return AttachmentsSerializer(
    #         Attachments.objects.filter(opportunity=obj).order_by('-id'),
    #         many=True
    #     ).data
    class Meta:
        model = Opportunity
        fields = (
            'id',
            'name',
            'stage',
            'stage_display',
            'contacts',
            'contacts_info',
            'meeting_date',
            'amount',
            'currency',
            'probability',
            'expected_revenue',
            'assigned_to',
            'assigned_to_info',
            'expected_close_date',
            'lead_source',
            'created_at',
            'description',
            'feedback',
            'is_active',
            'attachment_links',
            'attachments',
            'result'
        )
        read_only_fields = ('id', 'created_at')


class OpportunityPipelineUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating fields as you move through pipeline"""

    class Meta:
        model = Opportunity
        fields = (
            'stage',
            'meeting_date',
            'feedback',
            'expected_close_date',
            'result',
            'attachment_links'
        )

    def validate(self, data):
        """Validation of update depending on stage"""
        if self.instance:
            current_stage = self.instance.stage
            new_stage = data.get('stage', current_stage)

            #  Temporarily blocking the transition to CLOSE
            if new_stage == 'CLOSE':
                raise serializers.ValidationError(
                    "Moving to CLOSE stage is not available yet"
                )

            #  Receive the configuration for verification
            stage_to_check = new_stage if new_stage else current_stage
            stage_config = PIPELINE_CONFIG.get(stage_to_check, {})

            allowed_fields = stage_config.get('editable_fields', [])
            allowed_fields.append('stage')  # Всегда можно менять стадию

            # We check that we are editing only the allowed fields
            for field in data.keys():
                if field not in allowed_fields:
                    raise serializers.ValidationError(
                        f"Field '{field}' cannot be edited at stage '{stage_to_check}'"
                    )

        return data
class OpportunityAttachmentCreateSwaggerSerializer(serializers.Serializer):
    """Swagger schema для загрузки файлов через Cloudinary"""
    opportunity_id = serializers.UUIDField(
        help_text="ID оппортьюнити",
        required=True
    )
    file_name = serializers.CharField(
        help_text="Название файла",
        required=True
    )
    file_type = serializers.CharField(
        help_text="Тип файла (MIME)",
        required=False
    )
    file_url = serializers.URLField(
        help_text="URL файла из Cloudinary",
        required=True
    )