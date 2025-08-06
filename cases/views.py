import json
import uuid

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import csv

from rest_framework.views import APIView
from rest_framework import (
    generics,
    permissions,
    status,
)
from rest_framework.exceptions import APIException
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiParameter,
)


from accounts.models import Account
from cases.models import Case
from common.models import Attachments, Comment, Profile
from contacts.models import Contact
from teams.models import Teams

from accounts.serializer import AccountSerializer
from cases.serializer import (
    CaseCreateSerializer,
    CaseSerializer,
    CaseCreateSwaggerSerializer,
    CaseDetailEditSwaggerSerializer,
    CaseCommentEditSwaggerSerializer,
    CaseListSerializer,
)

from common.serializer import AttachmentsSerializer, CommentSerializer
from contacts.serializer import ContactSerializer
from cases import swagger_params1
from cases.tasks import send_email_to_assigned_user
from common.utils import CASE_TYPE, PRIORITY_CHOICE, STATUS_CHOICE
from .swagger_params1 import cases_list_get_params


# from common.external_auth import CustomDualAuthentication



# class CaseListView(APIView, LimitOffsetPagination):
#     #authentication_classes = (CustomDualAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     model = Case

#     def get_context_data(self, **kwargs):
#         params = self.request.query_params
#         queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
#         accounts = Account.objects.filter(org=self.request.profile.org).order_by("-id")
#         contacts = Contact.objects.filter(org=self.request.profile.org).order_by("-id")
#         profiles = Profile.objects.filter(is_active=True, org=self.request.profile.org)
#         if self.request.profile.role not in ["ADMIN", "MANAGER"] and not self.request.profile.is_admin:
#             queryset = queryset.filter(
#                 Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
#             ).distinct()
#             accounts = accounts.filter(
#                 Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
#             ).distinct()
#             contacts = contacts.filter(
#                 Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
#             ).distinct()
#             profiles = profiles.filter(role="ADMIN")

#         if params:
#             if params.get("name"):
#                 queryset = queryset.filter(name__icontains=params.get("name"))
#             if params.get("status"):
#                 queryset = queryset.filter(status=params.get("status"))
#             if params.get("priority"):
#                 queryset = queryset.filter(priority=params.get("priority"))
#             if params.get("account"):
#                 queryset = queryset.filter(account=params.get("account"))

#         context = {}

#         results_cases = self.paginate_queryset(queryset, self.request, view=self)
#         cases = CaseSerializer(results_cases, many=True).data

#         if results_cases:
#             offset = queryset.filter(id__gte=results_cases[-1].id).count()
#             if offset == queryset.count():
#                 offset = None
#         else:
#             offset = 0
#         context.update(
#             {
#                 "cases_count": self.count,
#                 "offset": offset,
#             }
#         )
#         context["cases"] = cases
#         context["status"] = STATUS_CHOICE
#         context["priority"] = PRIORITY_CHOICE
#         context["type_of_case"] = CASE_TYPE
#         context["accounts_list"] = AccountSerializer(accounts, many=True).data
#         context["contacts_list"] = ContactSerializer(contacts, many=True).data
#         return context

#     @extend_schema(
#         tags=["Cases"], parameters=swagger_params1.cases_list_get_params
#     )
#     def get(self, request, *args, **kwargs):
#         context = self.get_context_data(**kwargs)
#         return Response(context)

#     @extend_schema(
#         tags=["Cases"], parameters=swagger_params1.organization_params,request=CaseCreateSwaggerSerializer
#     )
#     def post(self, request, *args, **kwargs):
#         params = request.data
#         serializer = CaseCreateSerializer(data=params, request_obj=request)
#         if serializer.is_valid():
#             cases_obj = serializer.save(
#                 created_by=request.profile.user,
#                 org=request.profile.org,
#                 closed_on=params.get("closed_on"),
#                 case_type=params.get("case_type"),
#             )

#             if params.get("contacts"):
#                 contacts_list = params.get("contacts")
#                 contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
#                 if contacts:
#                     cases_obj.contacts.add(*contacts)

#             if params.get("teams"):
#                 teams_list = params.get("teams")
#                 teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
#                 if teams.exists():
#                     cases_obj.teams.add(*teams)

#             if params.get("assigned_to"):
#                 assinged_to_list = params.get("assigned_to")
#                 profiles = Profile.objects.filter(
#                     id__in=assinged_to_list, org=request.profile.org, is_active=True
#                 )
#                 if profiles:
#                     cases_obj.assigned_to.add(*profiles)

#             if self.request.FILES.get("case_attachment"):
#                 attachment = Attachments()
#                 attachment.created_by = self.request.profile.user
#                 attachment.file_name = self.request.FILES.get("case_attachment").name
#                 attachment.cases = cases_obj
#                 attachment.attachment = self.request.FILES.get("case_attachment")
#                 attachment.save()

#             recipients = list(cases_obj.assigned_to.all().values_list("id", flat=True))
#             send_email_to_assigned_user.delay(
#                 recipients,
#                 cases_obj.id,
#             )
#             return Response(
#                 {"error": False, "message": "Case Created Successfully"},
#                 status=status.HTTP_200_OK,
#             )

#         return Response(
#             {"error": True, "errors": serializer.errors},
#             status=status.HTTP_400_BAD_REQUEST,
#         )




class CaseListView(generics.ListAPIView):
    serializer_class = CaseListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'case_type']

    @extend_schema(
        parameters=cases_list_get_params,
        responses=CaseListSerializer(many=True)
    )

    def get(self, request, *args, **kwargs):
        export = request.query_params.get('export', '').lower() == 'true'
        if export:
            print("Export flag detected. Generating CSV...")
            queryset = self.filter_queryset(self.get_queryset())  # Confirm this line executes without error
            print("Queryset count:", queryset.count())
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="cases_export.csv"'
            
            # Force the response to be treated as CSV
            response['Content-Type'] = 'text/csv'
            
            writer = csv.writer(response)
            writer.writerow(['Case Name', 'Industry', 'Contact', 'Result', 'Close Date', 'Assigned To'])
            
            queryset = self.filter_queryset(self.get_queryset())
            for case in queryset:
                writer.writerow([
                    case.name,
                    case.opportunity.lead.company.industry if case.opportunity and case.opportunity.lead and case.opportunity.lead.company else '',
                    f"{case.opportunity.lead.contact.first_name} {case.opportunity.lead.contact.last_name}" if case.opportunity and case.opportunity.lead and case.opportunity.lead.contact else '',
                    str(case.expected_revenue) if case.expected_revenue else '',
                    case.closed_on.strftime('%Y-%m-%d') if case.closed_on else '',
                    ', '.join([f"{user.first_name} {user.last_name}" for user in case.assigned_to.all()])
                ])
            
            return response
        return super().get(request, *args, **kwargs)
            
    def get_profile(self):
        """Safely get user profile with proper error handling"""
        try:
            return get_object_or_404(Profile, user=self.request.user)
        except Exception as e:
            raise APIException(
                detail='User profile not found or incomplete',
                code=status.HTTP_403_FORBIDDEN
            )

    def validate_org_access(self, org_header):
        """Validate the org header and user access"""
        try:
            org_uuid = uuid.UUID(org_header)
        except ValueError:
            raise APIException(
                detail='Invalid organization UUID format',
                code=status.HTTP_400_BAD_REQUEST
            )

        profile = self.get_profile()
        if str(profile.org_id) != org_header:
            raise APIException(
                detail='You do not have access to this organization',
                code=status.HTTP_403_FORBIDDEN
            )
        return org_uuid, profile
    
    def get_queryset(self):
        # Get org header
        org_header = self.request.META.get('HTTP_ORG')
        if not org_header:
            raise APIException(
                detail='org header is required',
                code=status.HTTP_400_BAD_REQUEST
            )

        org_uuid, profile = self.validate_org_access(org_header)

        # Base queryset
        queryset = Case.objects.filter(org_id=org_uuid)
        
        # Initialize filter variables
        name = self.request.query_params.get('name')
        industry = self.request.query_params.get('industry')
        contact_id = self.request.query_params.get('contact_id')
        status = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        case_type = self.request.query_params.get('case_type')
        search = self.request.query_params.get('search')
        
        # Apply name filter if specified (independent of search)
        if name:
            queryset = queryset.filter(name__icontains=name)
            
        # Apply contact filter if specified (independent of search)
        if contact_id:
            queryset = queryset.filter(
                Q(contacts__id=contact_id) |
                Q(opportunity__lead__contact__id=contact_id)
            ).distinct()

        
        # Apply industry filter if specified (independent of search)
        if industry:
            queryset = queryset.filter(
                Q(opportunity__lead__company__industry__icontains=industry)
            ).distinct()
        
        # Apply search if parameter exists (combines with other filters)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(opportunity__lead__company__industry__icontains=search) |
                # Add these contact search fields:
                Q(contacts__first_name__icontains=search) |
                Q(contacts__last_name__icontains=search) |
                Q(opportunity__lead__contact__first_name__icontains=search) |
                Q(opportunity__lead__contact__last_name__icontains=search)
            ).distinct()
        
        # Apply status, priority, and case_type filters (always applied)
        if status:
            queryset = queryset.filter(status=status.lower() == 'true')
        if priority:
            queryset = queryset.filter(priority=priority)
        if case_type:
            queryset = queryset.filter(case_type=case_type)

        # Permission filtering
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.user) | 
                Q(assigned_to__in=[profile])
            ).distinct()
            
        return queryset.select_related(
            'opportunity',
            'opportunity__lead',
            'opportunity__lead__company',
            'opportunity__lead__contact',
            'account'
        ).prefetch_related(
            'contacts',
            'assigned_to',
            'assigned_to__user'
        ).order_by('-created_at')

    def handle_exception(self, exc):
        """Custom exception handling for consistent error responses"""
        if isinstance(exc, APIException):
            return Response(
                {'error': str(exc.detail)},
                status=exc.status_code
            )
        return super().handle_exception(exc)


class CaseDetailView(APIView):
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Case

    def get_object(self, pk):
        return self.model.objects.filter(id=pk).first()

    @extend_schema(
        tags=["Cases"], parameters=swagger_params1.organization_params,request=CaseCreateSwaggerSerializer
    )
    def put(self, request, pk, format=None):
        params = request.data
        cases_object = self.get_object(pk=pk)
        if cases_object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role not in ["ADMIN", "MANAGER"] and not self.request.profile.is_admin:
            if not (
                (self.request.profile == cases_object.created_by)
                or (self.request.profile in cases_object.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = CaseCreateSerializer(
            cases_object,
            data=params,
            request_obj=request,
        )

        if serializer.is_valid():
            cases_object = serializer.save(
                closed_on=params.get("closed_on"), case_type=params.get("case_type")
            )
            previous_assigned_to_users = list(
                cases_object.assigned_to.all().values_list("id", flat=True)
            )
            cases_object.contacts.clear()
            if params.get("contacts"):
                contacts_list = params.get("contacts")
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
                if contacts:
                    cases_object.contacts.add(*contacts)

            cases_object.teams.clear()
            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                if teams.exists():
                    cases_object.teams.add(*teams)

            cases_object.assigned_to.clear()
            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org, is_active=True
                )
                if profiles:
                    cases_object.assigned_to.add(*profiles)

            if self.request.FILES.get("case_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
                attachment.file_name = self.request.FILES.get("case_attachment").name
                attachment.case = cases_object
                attachment.attachment = self.request.FILES.get("case_attachment")
                attachment.save()

            assigned_to_list = list(
                cases_object.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                cases_object.id,
            )
            return Response(
                {"error": False, "message": "Case Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Cases"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role not in ["ADMIN", "MANAGER"] and not self.request.profile.is_admin:
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
            {"error": False, "message": "Case Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Cases"], parameters=swagger_params1.organization_params
    )
    def get(self, request, pk, format=None):
        self.cases = self.get_object(pk=pk)
        if self.cases.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        context = {}
        context["cases_obj"] = CaseSerializer(self.cases).data
        if self.request.profile.role not in ["ADMIN", "MANAGER"] and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.cases.created_by)
                or (self.request.profile in self.cases.assigned_to.all())
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
            self.request.profile == self.cases.created_by
            or self.request.profile.is_admin
            or self.request.profile.role in ["ADMIN", "MANAGER"]
        ):
            comment_permission = True

        if self.request.profile.is_admin or self.request.profile.role in ["ADMIN", "MANAGER"]:
            users_mention = list(
                Profile.objects.filter(is_active=True, org=self.request.profile.org).values(
                    "user__email"
                )
            )
        elif self.request.profile != self.cases.created_by:
            if self.cases.created_by:
                users_mention = [{"username": self.cases.created_by.user.email}]
            else:
                users_mention = []
        else:
            users_mention = []

        attachments = Attachments.objects.filter(case=self.cases).order_by("-id")
        comments = Comment.objects.filter(case=self.cases).order_by("-id")

        context.update(
            {
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
                "contacts": ContactSerializer(
                    self.cases.contacts.all(), many=True
                ).data,
                "status": STATUS_CHOICE,
                "priority": PRIORITY_CHOICE,
                "type_of_case": CASE_TYPE,
                "comment_permission": comment_permission,
                "users_mention": users_mention,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Cases"], parameters=swagger_params1.organization_params,request=CaseDetailEditSwaggerSerializer
    )
    def post(self, request, pk, **kwargs):
        params = request.data
        self.cases_obj = Case.objects.get(pk=pk)
        if self.cases_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        context = {}
        comment_serializer = CommentSerializer(data=params)
        if self.request.profile.role not in ["ADMIN", "MANAGER"] and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.cases_obj.created_by)
                or (self.request.profile in self.cases_obj.assigned_to.all())
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
                    case_id=self.cases_obj.id,
                    commented_by_id=self.request.profile.id,
                )

        if self.request.FILES.get("case_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.profile.user
            attachment.file_name = self.request.FILES.get("case_attachment").name
            attachment.case = self.cases_obj
            attachment.attachment = self.request.FILES.get("case_attachment")
            attachment.save()

        attachments = Attachments.objects.filter(case=self.cases_obj).order_by("-id")
        comments = Comment.objects.filter(case=self.cases_obj).order_by("-id")

        context.update(
            {
                "cases_obj": CaseSerializer(self.cases_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)


class CaseCommentView(APIView):
    model = Comment
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @extend_schema(
        tags=["Cases"], parameters=swagger_params1.organization_params,request=CaseCommentEditSwaggerSerializer
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role in ["ADMIN", "MANAGER"]
            or request.profile.is_admin
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
        tags=["Cases"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.profile.role in ["ADMIN", "MANAGER"]
            or request.profile.is_admin
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


class CaseAttachmentView(APIView):
    model = Attachments
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Cases"], parameters=swagger_params1.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.profile.role in ["ADMIN", "MANAGER"]
            or request.profile.is_admin
            or request.profile == self.object.created_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Attachment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
