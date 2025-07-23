import json
from django.utils import timezone

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account, Tags
from accounts.serializer import AccountSerializer, TagsSerailizer
from common.models import Attachments, Comment, Profile, User
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    ProfileSerializer,
)
from common.utils import CURRENCY_CODES, SOURCES, STAGES,PIPELINE_CONFIG
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from opportunity import swagger_params1
from opportunity.models import Opportunity
from opportunity.serializer import *
from opportunity.tasks import send_email_to_assigned_user
from teams.models import Teams



class OpportunityListView(APIView, LimitOffsetPagination):

    # authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Opportunity

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by(
            "-id"
        )
        accounts = Account.objects.filter(org=self.request.profile.org)
        contacts = Contact.objects.filter(org=self.request.profile.org)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
            ).distinct()
            accounts = accounts.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
            ).distinct()
            contacts = contacts.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
            ).distinct()

        if params:
            if params.get("name"):
                queryset = queryset.filter(name__icontains=params.get("name"))
            if params.get("account"):
                queryset = queryset.filter(account=params.get("account"))
            if params.get("stage"):
                queryset = queryset.filter(stage__contains=params.get("stage"))
            if params.get("lead_source"):
                queryset = queryset.filter(
                    lead_source__contains=params.get("lead_source")
                )
            if params.get("tags"):
                queryset = queryset.filter(tags__in=params.get("tags")).distinct()

        context = {}
        results_opportunities = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        opportunities = OpportunitySerializer(results_opportunities, many=True).data
        if results_opportunities:
            offset = queryset.filter(id__gte=results_opportunities[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context.update(
            {
                "opportunities_count": self.count,
                "offset": offset,
            }
        )
        context["opportunities"] = opportunities
        context["accounts_list"] = AccountSerializer(accounts, many=True).data
        context["contacts_list"] = ContactSerializer(contacts, many=True).data
        context["tags"] = TagsSerailizer(Tags.objects.filter(), many=True).data
        context["stage"] = STAGES
        context["lead_source"] = SOURCES
        context["currency"] = CURRENCY_CODES

        return context

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.opportunity_list_get_params,
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,
        request=OpportunityCreateSwaggerSerializer,
    )
    def post(self, request, *args, **kwargs):
        params = request.data

        serializer = OpportunityCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            opportunity_obj = serializer.save(
                created_by=request.profile.user,
                closed_on=params.get("due_date"),
                org=request.profile.org,
            )

            if params.get("contacts"):
                contacts_list = params.get("contacts")
                contacts = Contact.objects.filter(
                    id=contacts_list, org=request.profile.org
                )
                opportunity_obj.contacts.add(*contacts)
                opportunity_obj.save()

            if params.get("tags"):
                tags = params.get("tags")
                for tag in tags:
                    obj_tag = Tags.objects.filter(slug=tag.lower())
                    if obj_tag.exists():
                        obj_tag = obj_tag[0]
                    else:
                        obj_tag = Tags.objects.create(name=tag)
                    opportunity_obj.tags.add(obj_tag)

            if params.get("stage"):
                stage = params.get("stage")
                if stage in ["CLOSED WON", "CLOSED LOST"]:
                    opportunity_obj.closed_by = self.request.profile

            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                opportunity_obj.teams.add(*teams)

            if params.get("assigned_to"):
                assigned_to = params.get("assigned_to")
                print("assigned_to", assigned_to)
                profiles = Profile.objects.filter(
                    id=assigned_to, org=request.profile.org, is_active=True
                )
                print("profiles", profiles)
                opportunity_obj.assigned_to.add(*profiles)
                opportunity_obj.save()

            if self.request.FILES.get("opportunity_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
                attachment.file_name = self.request.FILES.get(
                    "opportunity_attachment"
                ).name
                attachment.opportunity = opportunity_obj
                attachment.attachment = self.request.FILES.get("opportunity_attachment")
                attachment.save()

            recipients = list(
                opportunity_obj.assigned_to.all().values_list("id", flat=True)
            )

            send_email_to_assigned_user.delay(
                recipients,
                opportunity_obj.id,
            )
            return Response(
                {"error": False, "message": "Opportunity Created Successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class OpportunityDetailView(APIView):
    # authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Opportunity

    def get_object(self, pk):
        return self.model.objects.filter(id=pk).first()

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,
        request=OpportunityCreateSwaggerSerializer,
    )
    def put(self, request, pk, format=None):
        params = request.data
        opportunity_object = self.get_object(pk=pk)
        if opportunity_object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == opportunity_object.created_by)
                or (self.request.profile in opportunity_object.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = OpportunityCreateSerializer(
            opportunity_object,
            data=params,
            request_obj=request,
            # opportunity=True,
        )

        if serializer.is_valid():
            opportunity_object = serializer.save(closed_on=params.get("due_date"))
            previous_assigned_to_users = list(
                opportunity_object.assigned_to.all().values_list("id", flat=True)
            )
            opportunity_object.contacts.clear()
            if params.get("contacts"):
                contacts_list = params.get("contacts")
                contacts = Contact.objects.filter(
                    id__in=contacts_list, org=request.profile.org
                )
                opportunity_object.contacts.add(*contacts)

            opportunity_object.tags.clear()
            if params.get("tags"):
                tags = params.get("tags")
                for tag in tags:
                    obj_tag = Tags.objects.filter(slug=tag.lower())
                    if obj_tag.exists():
                        obj_tag = obj_tag[0]
                    else:
                        obj_tag = Tags.objects.create(name=tag)
                    opportunity_object.tags.add(obj_tag)

            if params.get("stage"):
                stage = params.get("stage")
                if stage in ["CLOSED WON", "CLOSED LOST"]:
                    opportunity_object.closed_by = self.request.profile

            opportunity_object.teams.clear()
            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                opportunity_object.teams.add(*teams)

            opportunity_object.assigned_to.clear()
            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org, is_active=True
                )
                opportunity_object.assigned_to.add(*profiles)

            if self.request.FILES.get("opportunity_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
                attachment.file_name = self.request.FILES.get(
                    "opportunity_attachment"
                ).name
                attachment.opportunity = opportunity_object
                attachment.attachment = self.request.FILES.get("opportunity_attachment")
                attachment.save()

            assigned_to_list = list(
                opportunity_object.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                opportunity_object.id,
            )
            return Response(
                {"error": False, "message": "Opportunity Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Opportunities"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.profile != self.object.created_by:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        self.object.delete()
        return Response(
            {"error": False, "message": "Opportunity Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Opportunities"], parameters=swagger_params1.organization_params
    )
    def get(self, request, pk, format=None):
        self.opportunity = self.get_object(pk=pk)
        print("opportunity", self.opportunity)
        context = {}
        context["opportunity_obj"] = OpportunitySerializer(self.opportunity).data
        if self.opportunity.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == self.opportunity.created_by)
                or (self.request.profile in self.opportunity.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        comment_permission = False

        if (
            self.request.profile == self.opportunity.created_by
            or self.request.user.is_superuser
            or self.request.profile.role == "ADMIN"
        ):
            comment_permission = True

        if self.request.user.is_superuser or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(
                    is_active=True, org=self.request.profile.org
                ).values("user__email")
            )
        elif self.request.profile != self.opportunity.created_by:
            if self.opportunity.created_by:
                users_mention = [{"username": self.opportunity.created_by.user.email}]
            else:
                users_mention = []
        else:
            users_mention = []

        context.update(
            {
                "comments": CommentSerializer(
                    self.opportunity.opportunity_comments.all(), many=True
                ).data,
                "attachments": AttachmentsSerializer(
                    self.opportunity.opportunity_attachment.all(), many=True
                ).data,
                "contacts": ContactSerializer(
                    self.opportunity.contacts.all(), many=True
                ).data,
                "users": ProfileSerializer(
                    Profile.objects.filter(
                        is_active=True, org=self.request.profile.org
                    ).order_by("user__email"),
                    many=True,
                ).data,
                "stage": STAGES,
                "lead_source": SOURCES,
                "currency": CURRENCY_CODES,
                "comment_permission": comment_permission,
                "users_mention": users_mention,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,
        request=OpportunityDetailEditSwaggerSerializer,
    )
    def post(self, request, pk, **kwargs):
        params = request.data
        context = {}
        self.opportunity_obj = Opportunity.objects.get(pk=pk)
        if self.opportunity_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment_serializer = CommentSerializer(data=params)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == self.opportunity_obj.created_by)
                or (self.request.profile in self.opportunity_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    opportunity_id=self.opportunity_obj.id,
                    commented_by_id=self.request.profile.id,
                )

            if self.request.FILES.get("opportunity_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
                attachment.file_name = self.request.FILES.get(
                    "opportunity_attachment"
                ).name
                attachment.opportunity = self.opportunity_obj
                attachment.attachment = self.request.FILES.get("opportunity_attachment")
                attachment.save()

        comments = Comment.objects.filter(opportunity=self.opportunity_obj).order_by(
            "-id"
        )
        attachments = Attachments.objects.filter(
            opportunity=self.opportunity_obj
        ).order_by("-id")
        context.update(
            {
                "opportunity_obj": OpportunitySerializer(self.opportunity_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)


class OpportunityCommentView(APIView):
    model = Comment
    # authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,
        request=OpportunityCommentEditSwaggerSerializer,
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=params)
            if params.get("comment"):
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {"error": False, "message": "Comment Submitted"},
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {"error": True, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Opportunities"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile == self.object.commented_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Comment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You do not have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


from common.serializer import AttachmentsSerializer

class OpportunityAttachmentView(APIView):
    model = Attachments
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return get_object_or_404(Opportunity, pk=pk)

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,

    )
    def get(self, request, pk, format=None):
        """
        Получить все вложения для opportunity
        """
        opportunity = self.get_object(pk)

        # Проверка прав доступа
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            if not (
                (request.profile == opportunity.created_by)
                or (request.profile in opportunity.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have permission to view attachments for this opportunity"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        attachments = Attachments.objects.filter(
            opportunity=opportunity
        ).order_by("-id")

        return Response({
            "error": False,
            "attachments": AttachmentsSerializer(attachments, many=True).data
        })

    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,
        request=OpportunityAttachmentCreateSwaggerSerializer,
    )
    def post(self, request, pk=None, format=None):
        """
        Create an attachment for opportunity using data from Cloudinary
        Supports attachment_type: 'proposal' or 'contract'
        """
        opportunity_id = request.data.get("opportunity_id")
        file_name = request.data.get("file_name")
        file_type = request.data.get("file_type", "")
        file_url = request.data.get("file_url")
        attachment_type = request.data.get("attachment_type", "proposal")

        if not (opportunity_id and file_name and file_url):
            return Response(
                {"error": True, "errors": "Missing required data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            opportunity = Opportunity.objects.get(id=opportunity_id, org=request.profile.org)

            # Проверка прав доступа
            if request.profile.role != "ADMIN" and not request.user.is_superuser:
                if not (
                    (request.profile == opportunity.created_by)
                    or (request.profile in opportunity.assigned_to.all())
                ):
                    return Response(
                        {
                            "error": True,
                            "errors": "You don't have permission for this opportunity"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            # Создаем attachment
            attachment = Attachments()
            attachment.created_by = request.user
            attachment.file_name = file_name
            attachment.opportunity = opportunity
            attachment.attachment = file_url
            attachment.save()

            # Обновляем объект после сохранения
            attachment.refresh_from_db()

            # Формируем информацию о вложении
            attachment_info = {
                'attachment_id': str(attachment.id),
                'file_name': file_name,
                'url': file_url,
                'uploaded_at': attachment.created_at.isoformat() if attachment.created_at else '',
                'file_type': file_type
            }

            # Обновляем соответствующее поле в зависимости от типа
            if attachment_type == "contract":
                # Для контракта обновляем contract_attachment
                if opportunity.contract_attachment is None:
                    opportunity.contract_attachment = []
                opportunity.contract_attachment.append(attachment_info)

                # Если загружаем контракт на стадии CLOSED WON, обновляем дополнительные поля
                if opportunity.stage == 'CLOSED WON':
                    opportunity.closed_by = request.profile
                    opportunity.closed_on = timezone.now().date()
                    opportunity.result = True
                    opportunity.probability = 100
            else:
                # Для proposal и других обновляем attachment_links
                if opportunity.attachment_links is None:
                    opportunity.attachment_links = []
                opportunity.attachment_links.append(attachment_info)

            opportunity.save()

            return Response(
                {
                    "error": False,
                    "message": f"Attachment created successfully as {attachment_type}",
                    "attachment_id": str(attachment.id),
                    "attachment": file_name,
                    "attachment_url": file_url,
                    "attachment_type": attachment_type,
                    "attachment_display": file_type,
                    "created_by": request.user.email,
                    "created_on": attachment.created_at.isoformat() if attachment.created_at else '',
                    "file_type": (
                        file_type.split("/") if "/" in file_type else [file_type, ""]
                    ),
                    "download_url": file_url,
                },
                status=status.HTTP_201_CREATED,
            )

        except Opportunity.DoesNotExist:
            return Response(
                {"error": True, "errors": "Opportunity not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            import traceback
            print(f"Error in OpportunityAttachmentView.post: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"error": True, "errors": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    @extend_schema(
        tags=["Opportunities"],
        parameters=swagger_params1.organization_params,
    )
    def delete(self, request, pk, attachment_id, format=None):
        """
        Удалить вложение
        """
        opportunity = self.get_object(pk)

        try:
            attachment = Attachments.objects.get(
                id=attachment_id,
                opportunity=opportunity
            )
        except Attachments.DoesNotExist:
            return Response({
                "error": True,
                "errors": "Attachment not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Проверка прав доступа (аналогично leads)
        if (
            request.profile.role == "ADMIN"
            or request.user.is_superuser
            or request.profile.user == attachment.created_by
        ):
            attachment.delete()
            return Response({
                "error": False,
                "message": "Attachment deleted successfully"
            })
        else:
            return Response({
                "error": True,
                "errors": "You don't have permission to delete this attachment"
            }, status=status.HTTP_403_FORBIDDEN)

class OpportunityPipelineView(APIView):
    """View для работы с Opportunity в pipeline"""
    permission_classes = (IsAuthenticated,)

    @extend_schema(
    tags=["Opportunities"],
    parameters=swagger_params1.organization_params,
)
    def get(self, request, pk):
        """Получить данные opportunity для pipeline view"""
        opportunity = get_object_or_404(Opportunity, pk=pk, org=request.profile.org)

        # Проверка прав доступа
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            if not (
                (request.profile == opportunity.created_by)
                or (request.profile in opportunity.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have permission to view this opportunity"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = OpportunityPipelineSerializer(opportunity)

        # Определяем текущую стадию для конфигурации
        config_stage = opportunity.stage
        current_stage_config = PIPELINE_CONFIG.get(config_stage, {})

        # Отображаем стадии pipeline БЕЗ CLOSED WON/LOST
        # Только основные стадии для отображения в pipeline
        available_stages = [
            {'value': 'QUALIFICATION', 'label': 'Qualification'},
            {'value': 'IDENTIFY_DECISION_MAKERS', 'label': 'Identify Decision Makers'},
            {'value': 'PROPOSAL', 'label': 'Proposal'},
            {'value': 'NEGOTIATION', 'label': 'Negotiation'},
            {'value': 'CLOSE', 'label': 'Close'}
        ]

        # Если opportunity уже в статусе CLOSED WON или CLOSED LOST,
        # отображаем стадию CLOSE как активную в pipeline
        display_stage = opportunity.stage
        if display_stage in ['CLOSED WON', 'CLOSED LOST']:
            display_stage = 'CLOSE'

        # Опции для выбора на стадии CLOSE
        close_options = [
            {'value': 'CLOSED WON', 'label': 'Close as Won'},
            {'value': 'CLOSED LOST', 'label': 'Close as Lost'}
        ]

        # Доступные переходы между стадиями
        available_transitions = []

        # Определяем доступные переходы на основе текущей стадии и выполненных условий
        if opportunity.stage == 'QUALIFICATION':
            available_transitions.append('IDENTIFY_DECISION_MAKERS')

        elif opportunity.stage == 'IDENTIFY_DECISION_MAKERS':
            if opportunity.meeting_date:
                available_transitions.append('PROPOSAL')

        elif opportunity.stage == 'PROPOSAL':
            if opportunity.attachment_links:
                available_transitions.append('NEGOTIATION')

        elif opportunity.stage == 'NEGOTIATION':
            if opportunity.feedback:
                available_transitions.append('CLOSE')

        # Формируем метаданные для фронтенда
        pipeline_metadata = {
            'current_stage': opportunity.stage,
            'display_stage': display_stage,  # Для визуального отображения в pipeline
            'current_stage_display': opportunity.get_stage_display(),
            'editable_fields': current_stage_config.get('editable_fields', []),
            'next_stage': current_stage_config.get('next_stage'),
            'available_stages': available_stages,  # Стадии для отображения в pipeline
            'available_transitions': available_transitions,  # Доступные переходы
            'close_options': close_options,  # Опции для выбора при закрытии
            'is_at_close': opportunity.stage == 'CLOSE',
            'is_closed': opportunity.stage in ['CLOSED WON', 'CLOSED LOST'],
            'close_result': 'won' if opportunity.stage == 'CLOSED WON' else ('lost' if opportunity.stage == 'CLOSED LOST' else None),
            'has_attachments': bool(opportunity.attachment_links),
            'has_contract': bool(opportunity.contract_attachment),
            'has_feedback': bool(opportunity.feedback),
            'can_move_to_close': opportunity.stage == 'NEGOTIATION' and bool(opportunity.feedback),
            'reason': opportunity.reason if opportunity.stage == 'CLOSED LOST' else None
        }

        return Response({
            'error': False,
            'opportunity': serializer.data,
            'pipeline_metadata': pipeline_metadata
        })
    @extend_schema(
    tags=["Opportunities"],
    parameters=swagger_params1.organization_params,
    request=OpportunityPipelineUpdateSerializer,
)
    def patch(self, request, pk):
        """Обновить opportunity при движении по pipeline"""
        opportunity = get_object_or_404(Opportunity, pk=pk, org=request.profile.org)

        # Проверка прав доступа
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            if not (
                (request.profile == opportunity.created_by)
                or (request.profile in opportunity.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have permission to update this opportunity"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        # Проверяем, что opportunity активна
        if not opportunity.is_active:
            return Response(
                {
                    "error": True,
                    "errors": "Cannot update inactive opportunity"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Сохраняем старые значения для логирования
        old_values = {
            'stage': opportunity.stage,
            'meeting_date': opportunity.meeting_date,
            'feedback': opportunity.feedback,
            'reason': opportunity.reason,
            'has_contract': bool(opportunity.contract_attachment)
        }

        # Обрабатываем данные
        data = request.data.copy()

        # Handle stage transitions
        current_stage = opportunity.stage
        new_stage = data.get('stage')

        # Обработка случая с переходом QUALIFICATION -> PROPOSAL с meeting_date
        # В этом случае сначала сохраняем meeting_date
        if current_stage == 'QUALIFICATION' and new_stage == 'PROPOSAL' and data.get('meeting_date'):
            # Сохраняем meeting_date в opportunity перед сменой стадии
            opportunity.meeting_date = data.get('meeting_date')
            opportunity.save(update_fields=['meeting_date'])

            # Удаляем meeting_date из data, чтобы не вызвать ошибку валидации
            # о невозможности изменения meeting_date на стадии PROPOSAL
            if 'meeting_date' in data:
                del data['meeting_date']

        # Для обратной совместимости - запрос со stage=IDENTIFY_DECISION_MAKERS
        elif current_stage == 'QUALIFICATION' and new_stage == 'IDENTIFY_DECISION_MAKERS' and data.get('meeting_date'):
            # Сохраняем meeting_date
            opportunity.meeting_date = data.get('meeting_date')
            opportunity.save(update_fields=['meeting_date'])

            # Переводим на PROPOSAL и удаляем meeting_date из данных
            data['stage'] = 'PROPOSAL'
            if 'meeting_date' in data:
                del data['meeting_date']

        # Handle validations for transitions
        if new_stage and new_stage != current_stage:
            # Validate transition from QUALIFICATION to PROPOSAL - requires meeting_date
            if current_stage == 'QUALIFICATION' and new_stage == 'PROPOSAL':
                if not opportunity.meeting_date and not data.get('meeting_date'):
                    return Response({
                        'error': True,
                        'errors': 'Meeting date is required to move to Proposal stage'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Validate transition from IDENTIFY_DECISION_MAKERS to PROPOSAL - requires meeting_date
            elif current_stage == 'IDENTIFY_DECISION_MAKERS' and new_stage == 'PROPOSAL':
                if not opportunity.meeting_date and not data.get('meeting_date'):
                    return Response({
                        'error': True,
                        'errors': 'Meeting date is required to move to Proposal stage'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Validate transition from PROPOSAL to NEGOTIATION - requires attachment
            if current_stage == 'PROPOSAL' and new_stage == 'NEGOTIATION':
                if not opportunity.attachment_links:
                    return Response({
                        'error': True,
                        'errors': 'Proposal document is required to move to Negotiation stage'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Validate transition from NEGOTIATION to CLOSE - requires feedback
            if current_stage == 'NEGOTIATION' and new_stage == 'CLOSE':
                if not opportunity.feedback and not data.get('feedback'):
                    return Response({
                        'error': True,
                        'errors': 'Feedback is required to move to Close stage'
                    }, status=status.HTTP_400_BAD_REQUEST)

        # Обработка выбора Close option
        if data.get('close_option') and opportunity.stage == 'CLOSE':
            # Для CLOSED WON проверяем наличие контракта
            if data['close_option'] == 'CLOSED WON' and not opportunity.contract_attachment:
                return Response({
                    'error': True,
                    'errors': {
                        'contract_attachment': 'Please upload contract before closing as won. Use /api/opportunities/attachment/ endpoint with attachment_type="contract"'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            data['stage'] = data['close_option']

        serializer = OpportunityPipelineUpdateSerializer(
            opportunity,
            data=data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            opportunity = serializer.save()

            # Логирование изменений
            changes = []

            if old_values['stage'] != opportunity.stage:
                changes.append(f"Stage: {old_values['stage']} → {opportunity.stage}")

            if old_values['meeting_date'] != opportunity.meeting_date:
                changes.append("Meeting date updated")

            if old_values['feedback'] != opportunity.feedback:
                changes.append("Feedback updated")

            if old_values['reason'] != opportunity.reason:
                changes.append("Close reason added")

            if not old_values['has_contract'] and opportunity.contract_attachment:
                changes.append("Contract uploaded")

            # Получаем все вложения для opportunity
            attachments = Attachments.objects.filter(opportunity=opportunity).order_by('-created_at')

            return Response({
                'error': False,
                'message': 'Opportunity updated successfully',
                'opportunity': OpportunityPipelineSerializer(opportunity).data,
                'changes': changes,
                'attachments': AttachmentsSerializer(attachments, many=True).data
            })

        return Response({
            'error': True,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)