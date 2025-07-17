from rest_framework import serializers

from accounts.models import Tags
from accounts.serializer import AccountSerializer
from common.serializer import AttachmentsSerializer, ProfileSerializer,UserSerializer
from contacts.serializer import ContactSerializer
from opportunity.models import Opportunity
from teams.serializer import TeamsSerializer
from common.utils import PIPELINE_CONFIG

class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class OpportunitySerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    closed_by = ProfileSerializer()
    created_by = UserSerializer()
    tags = TagsSerializer(read_only=True, many=True)
    assigned_to = ProfileSerializer(read_only=True, many=True)
    contacts = ContactSerializer(read_only=True, many=True)
    teams = TeamsSerializer(read_only=True, many=True)
    opportunity_attachment = AttachmentsSerializer(read_only=True, many=True)

    class Meta:
        model = Opportunity
        # fields = ‘__all__’
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
            # "get_team_users",
            # "get_team_and_assigned_users",
            # "get_assigned_users_not_in_teams",
        )


class OpportunityCreateSerializer(serializers.ModelSerializer):
    probability = serializers.IntegerField(max_value=100)
    closed_on = serializers.DateField

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
            "org"
            # "get_team_users",
            # "get_team_and_assigned_users",
            # "get_assigned_users_not_in_teams",
        )

class OpportunityCreateSwaggerSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField()
    opportunity_attachment = serializers.FileField()
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
            "opportunity_attachment"
        )

class OpportunityDetailEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()
    opportunity_attachment = serializers.FileField()

class OpportunityCommentEditSwaggerSerializer(serializers.Serializer):
    comment = serializers.CharField()

class OpportunityPipelineSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения Opportunity в pipeline"""
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    contacts_info = ContactSerializer(source='contacts', many=True, read_only=True)
    assigned_to_info = ProfileSerializer(source='assigned_to', many=True, read_only=True)

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
            'proposal_doc',
            'feedback',
            'is_active',
        )
        read_only_fields = ('id', 'created_at')


class OpportunityPipelineUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления полей при движении по pipeline"""

    class Meta:
        model = Opportunity
        fields = (
            'stage',
            'meeting_date',
            'proposal_doc',
            'feedback',
            'expected_close_date',
        )

    def validate(self, data):
        """Валидация обновления в зависимости от стадии"""
        if self.instance:
            current_stage = self.instance.stage
            new_stage = data.get('stage', current_stage)

            # Временно блокируем переход на CLOSE
            if new_stage == 'CLOSE':
                raise serializers.ValidationError(
                    "Moving to CLOSE stage is not available yet"
                )

            # Получаем конфигурацию для проверки
            stage_to_check = new_stage if new_stage else current_stage
            stage_config = PIPELINE_CONFIG.get(stage_to_check, {})

            allowed_fields = stage_config.get('editable_fields', [])
            allowed_fields.append('stage')  # Всегда можно менять стадию

            # Проверяем, что редактируем только разрешенные поля
            for field in data.keys():
                if field not in allowed_fields:
                    raise serializers.ValidationError(
                        f"Field '{field}' cannot be edited at stage '{stage_to_check}'"
                    )

        return data