from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import Http404
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account, Tags
from common.models import APISettings, Attachments, Comment, Profile

# from common.external_auth import CustomDualAuthentication
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    LeadCommentSerializer,
    ProfileSerializer,
)
from .forms import LeadListForm
from .models import Lead
from common.utils import COUNTRIES, INDCHOICES, LEAD_SOURCE, LEAD_STATUS
from contacts.models import Contact
from leads import swagger_params1
from companies.models import CompanyProfile
from leads.serializer import (
    CompanySerializer,
    CompanySwaggerSerializer,
    LeadCreateSerializer,
    LeadSerializer,
    TagsSerializer,
    LeadCreateSwaggerSerializer,
    LeadDetailEditSwaggerSerializer,
    LeadCommentEditSwaggerSerializer,
    CreateLeadFromSiteSwaggerSerializer,
    LeadUploadSwaggerSerializer,
    AttachmentCreateSwaggerSerializer,
    LeadListSerializer,
)
from common.models import User
from leads.tasks import (
    create_lead_from_file,
    send_email_to_assigned_user,
    send_lead_assigned_emails,
)
from teams.models import Teams
from teams.serializer import TeamsSerializer


class LeadListView(APIView, LimitOffsetPagination):
    model = Lead
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = (
            self.model.objects.filter(
                organization=self.request.profile.org, converted=False
            )  # Updated from org to organization
            .exclude(status="converted")
            .select_related("created_by", "contact", "company")
            .prefetch_related(
                "assigned_to",
            )
        ).order_by("-id")
        if (
            self.request.profile.role not in ["ADMIN", "MANAGER"]
            and not self.request.user.is_superuser
        ):
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile])
                | Q(created_by=self.request.profile.user)
            )

            # ✅ Enhanced filters (this is what you want to add)
        if search := params.get("search"):
            queryset = queryset.select_related("contact", "company").filter(
                Q(lead_title__icontains=search)  # Add search by lead_title
                | Q(description__icontains=search)
                | Q(lead_source__icontains=search)
                | Q(status__icontains=search)
                | Q(contact__first_name__icontains=search)
                | Q(
                    contact__last_name__icontains=search
                )  # Add search by contact's last name
                | Q(
                    contact__primary_email__icontains=search
                )  # Add search by contact's primary email
                | Q(company__name__icontains=search)
            )

        if params:
            if params.get("name"):
                # Update name search to use lead_title field
                queryset = queryset.filter(lead_title__icontains=params.get("name"))
            if params.get("lead_title"):
                # Add explicit lead_title filter
                queryset = queryset.filter(
                    lead_title__icontains=params.get("lead_title")
                )
            if params.get("description"):
                queryset = queryset.filter(
                    description__icontains=params.get("description")
                )
            if params.get("lead_source"):
                queryset = queryset.filter(lead_source=params.get("lead_source"))
            if params.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=params.get("assigned_to")
                )
            if params.get("status"):
                queryset = queryset.filter(status=params.get("status"))
            # Removed tags filtering as Lead model doesn't have tags field
            # if params.get("tags"):
            #     queryset = queryset.filter(tags__in=params.get("tags"))
            if params.get("city"):
                queryset = queryset.filter(city__icontains=params.get("city"))
            if params.get("email"):
                queryset = queryset.filter(email__icontains=params.get("email"))
        context = {}
        queryset_open = queryset.exclude(status="closed")
        results_leads_open = self.paginate_queryset(
            queryset_open.distinct(), self.request, view=self
        )
        open_leads = LeadListSerializer(results_leads_open, many=True).data
        if results_leads_open:
            offset = queryset_open.filter(id__gte=results_leads_open[-1].id).count()
            if offset == queryset_open.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context["open_leads"] = {
            "leads_count": self.count,
            "open_leads": open_leads,
            "offset": offset,
        }

        queryset_close = queryset.filter(status="closed")
        results_leads_close = self.paginate_queryset(
            queryset_close.distinct(), self.request, view=self
        )
        close_leads = LeadListSerializer(results_leads_close, many=True).data
        if results_leads_close:
            offset = queryset_close.filter(id__gte=results_leads_close[-1].id).count()
            if offset == queryset_close.count():
                offset = None
        else:
            offset = 0

        context["close_leads"] = {
            "leads_count": self.count,
            "close_leads": close_leads,
            "offset": offset,
        }
        contacts = Contact.objects.filter(org=self.request.profile.org).values(
            "id", "first_name"
        )

        context["contacts"] = contacts
        context["status"] = LEAD_STATUS
        context["source"] = LEAD_SOURCE
        context["companies"] = CompanySerializer(
            CompanyProfile.objects.filter(), many=True
        ).data
        # Note: Lead model no longer has tags, but we still include available tags in context
        # for other models or potential future use
        context["tags"] = TagsSerializer(Tags.objects.all(), many=True).data

        users = Profile.objects.filter(
            is_active=True, org=self.request.profile.org
        ).values("id", "user__email")
        context["users"] = users
        context["countries"] = COUNTRIES
        context["industries"] = INDCHOICES
        return context

    @extend_schema(tags=["Leads"], parameters=swagger_params1.lead_list_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Leads"],
        description="Leads Create",
        parameters=swagger_params1.organization_params,
        request=LeadCreateSwaggerSerializer,
        examples=[
            OpenApiExample(
                "Lead Example",
                summary="Create a new lead",
                value={
                    "lead_title": "Enterprise Software Solution",
                    "description": "Potential client for software development services",
                    "link": "https://example.com/meeting-notes",
                    "amount": "50000.00",
                    "probability": 75,
                    "status": "in process",
                    "lead_source": "email",
                    "notes": "Initial contact made via email, interested in our product suite",
                    "attachment_links": [
                        "https://example.com/files/doc1.pdf",
                        "https://example.com/files/doc2.pdf",
                    ],
                    "contact": "fe3e240f-0664-4288-868d-6b63511daa59",
                    "company": "ee3dddad-21ab-4b22-9ab4-076d3a28a0ac",
                    "assigned_to": "7daf9e00-328c-47cd-af57-0e1fe8e43190",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        # Removed debug print statement
        data = request.data

        # Check for required fields
        required_fields = ["contact", "company", "description", "status", "assigned_to"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return Response(
                {
                    "error": True,
                    "errors": f"Missing required fields: {', '.join(missing_fields)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LeadCreateSerializer(data=data, request_obj=request)
        if serializer.is_valid():
            lead_obj = serializer.save(
                created_by=request.profile.user, organization=request.profile.org
            )

            # Handle attachment_links if provided
            if data.get("attachment_links"):
                lead_obj.attachment_links = data.get("attachment_links")
                lead_obj.save()

            # Removed tags handling as Lead model doesn't have tags field
            # if data.get("tags", None):
            #     tags = data.get("tags")
            #     for t in tags:
            #         tag = Tags.objects.filter(slug=t.lower())
            #         if tag.exists():
            #             tag = tag[0]
            #         else:
            #             tag = Tags.objects.create(name=t)
            #         lead_obj.tags.add(tag)

            # Handle contact as a ForeignKey, not ManyToMany
            if data.get("contact", None):
                try:
                    contact = Contact.objects.get(
                        id=data.get("contact"), org=request.profile.org
                    )
                    lead_obj.contact = contact
                    lead_obj.save()
                except Contact.DoesNotExist:
                    pass  # The serializer should have already validated this

            # Handle assigned_to as a single Profile object, not a queryset
            recipients = [lead_obj.assigned_to.id] if lead_obj.assigned_to else []
            send_email_to_assigned_user.delay(
                recipients,
                lead_obj.id,
            )

            if request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = request.profile.user
                attachment.file_name = request.FILES.get("lead_attachment").name
                attachment.lead = lead_obj
                attachment.attachment = request.FILES.get("lead_attachment")
                attachment.save()

            # Commented out teams-related code as we don't have teams in Lead model currently
            # if data.get("teams", None):
            #     teams_list = data.get("teams")
            #     teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
            #     lead_obj.teams.add(*teams)

            # Skip handling of assigned_to here as it's already set as a ForeignKey
            # The assigned_to is now directly set in serializer.save()

            if data.get("status") == "converted":
                account_object = Account.objects.create(
                    created_by=request.profile.user,
                    description=data.get("description"),
                    website=data.get("website"),
                    org=request.profile.org,
                )

                # Removed address field copying as Lead model no longer has these fields
                comments = Comment.objects.filter(lead=self.lead_obj)
                if comments.exists():
                    for comment in comments:
                        comment.account_id = account_object.id
                attachments = Attachments.objects.filter(lead=self.lead_obj)
                if attachments.exists():
                    for attachment in attachments:
                        attachment.account_id = account_object.id
                # Removed tags copying as Lead model doesn't have tags field
                # for tag in lead_obj.tags.all():
                #     account_object.tags.add(tag)

                if data.get("assigned_to", None):
                    assigned_to_list = data.getlist("assigned_to")
                    recipients = assigned_to_list
                    send_email_to_assigned_user.delay(
                        recipients,
                        lead_obj.id,
                    )
                return Response(
                    {
                        "error": False,
                        "message": "Lead Converted to Account Successfully",
                        "id": str(lead_obj.id),
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {
                    "error": False,
                    "message": "Lead Created Successfully",
                    "id": str(lead_obj.id),
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LeadDetailView(APIView):
    model = Lead
    # authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return get_object_or_404(Lead, id=pk)

    def get_context_data(self, **kwargs):
        context = {}

        comments = Comment.objects.filter(lead=self.lead_obj).order_by("-id")
        attachments = Attachments.objects.filter(lead=self.lead_obj).order_by("-id")
        assigned_data = []
        # Handle assigned_to as a single object, not a queryset
        if self.lead_obj.assigned_to:
            assigned_dict = {}
            assigned_dict["id"] = self.lead_obj.assigned_to.id
            assigned_dict["name"] = self.lead_obj.assigned_to.user.email
            assigned_data.append(assigned_dict)

        if self.request.user.is_superuser or self.request.profile.role in [
            "ADMIN",
            "MANAGER",
        ]:
            users_mention = list(
                Profile.objects.filter(
                    is_active=True, org=self.request.profile.org
                ).values("user__email")
            )
        elif self.request.profile.user != self.lead_obj.created_by:
            users_mention = [{"user__email": self.lead_obj.created_by.email}]
        else:
            # Handle assigned_to as a single object
            users_mention = []
            if self.lead_obj.assigned_to:
                users_mention.append(
                    {"user__email": self.lead_obj.assigned_to.user.email}
                )

        if (
            self.request.profile.role in ["ADMIN", "MANAGER"]
            or self.request.user.is_superuser
        ):
            users = Profile.objects.filter(
                is_active=True, org=self.request.profile.org
            ).order_by("user__email")
        else:
            users = Profile.objects.filter(
                role="ADMIN", org=self.request.profile.org
            ).order_by("user__email")

        # Handle assigned_to as a ForeignKey field
        user_assgn_list = []
        if self.lead_obj.assigned_to:
            user_assgn_list.append(self.lead_obj.assigned_to.id)

        if self.request.profile.user == self.lead_obj.created_by:
            user_assgn_list.append(self.request.profile.id)
        if (
            self.request.profile.role not in ["ADMIN", "MANAGER"]
            and not self.request.user.is_superuser
        ):
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        # Comment out team-related code as we don't have teams in Lead model currently
        # team_ids = [user.id for user in self.lead_obj.get_team_users]
        team_ids = []  # Empty list since we're not using teams
        all_user_ids = [user.id for user in users]
        users_excluding_team_id = set(all_user_ids) - set(team_ids)
        users_excluding_team = Profile.objects.filter(id__in=users_excluding_team_id)
        context.update(
            {
                "lead_obj": LeadSerializer(self.lead_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": LeadCommentSerializer(comments, many=True).data,
                "users_mention": users_mention,
                "assigned_data": assigned_data,
            }
        )
        context["users"] = ProfileSerializer(users, many=True).data
        context["users_excluding_team"] = ProfileSerializer(
            users_excluding_team, many=True
        ).data
        context["source"] = LEAD_SOURCE
        context["status"] = LEAD_STATUS
        context["teams"] = TeamsSerializer(
            Teams.objects.filter(org=self.request.profile.org), many=True
        ).data
        context["countries"] = COUNTRIES
        context["converted"] = self.lead_obj.converted
        print("test", self.lead_obj.converted)

        return context

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params1.organization_params,
        description="Lead Detail",
    )
    def get(self, request, pk, **kwargs):
        self.lead_obj = self.get_object(pk)

        # Permission check
        user_assgn_list = []
        if self.lead_obj.assigned_to:
            user_assgn_list.append(self.lead_obj.assigned_to.id)

        if self.request.profile.user == self.lead_obj.created_by:
            user_assgn_list.append(self.request.profile.id)
        if (
            self.request.profile.role not in ["ADMIN", "MANAGER"]
            and not self.request.user.is_superuser
        ):
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params1.organization_params,
        request=LeadDetailEditSwaggerSerializer,
    )
    def post(self, request, pk, **kwargs):
        params = request.data

        context = {}
        self.lead_obj = Lead.objects.get(pk=pk)
        if self.lead_obj.organization != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if (
            self.request.profile.role not in ["ADMIN", "MANAGER"]
            and not self.request.user.is_superuser
        ):
            if not (
                (self.request.profile.user == self.lead_obj.created_by)
                or (self.request.profile == self.lead_obj.assigned_to)
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        comment_serializer = CommentSerializer(data=params)
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    lead_id=self.lead_obj.id,
                    commented_by_id=self.request.profile.id,
                )

            if self.request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = User.objects.get(
                    id=self.request.profile.user.id
                )

                attachment.file_name = self.request.FILES.get("lead_attachment").name
                attachment.lead = self.lead_obj
                attachment.attachment = self.request.FILES.get("lead_attachment")
                attachment.save()

        comments = Comment.objects.filter(lead__id=self.lead_obj.id).order_by("-id")
        attachments = Attachments.objects.filter(lead__id=self.lead_obj.id).order_by(
            "-id"
        )
        context.update(
            {
                "lead_obj": LeadSerializer(self.lead_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": LeadCommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params1.organization_params,
        request=LeadCreateSwaggerSerializer,
    )
    def put(self, request, pk, **kwargs):
        params = request.data
        self.lead_obj = self.get_object(pk)

        # Check organization permission
        if self.lead_obj.organization != request.profile.org:
            return Response(
                {
                    "error": True,
                    "errors": "User company does not match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Role-based permission check for lead updates
        if request.profile.role == "USER":
            # Users can only update leads they created or are assigned to
            can_update = self.lead_obj.created_by == request.profile.user or (
                self.lead_obj.assigned_to
                and self.lead_obj.assigned_to == request.profile
            )
            if not can_update:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have permission to update this lead",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        # Admin and Manager can update any lead (no additional check needed)

        # Check for required fields (same as in create method)
        required_fields = ["contact", "company", "description", "status", "assigned_to"]
        missing_fields = [field for field in required_fields if not params.get(field)]

        if missing_fields:
            return Response(
                {
                    "error": True,
                    "errors": f"Missing required fields: {', '.join(missing_fields)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the previous assigned_to ID before saving
        previous_assigned_to_id = (
            self.lead_obj.assigned_to.id if self.lead_obj.assigned_to else None
        )

        serializer = LeadCreateSerializer(
            data=params,
            instance=self.lead_obj,
            request_obj=request,
        )

        if serializer.is_valid():
            lead_obj = serializer.save()

            # Handle attachment_links if provided
            if params.get("attachment_links"):
                lead_obj.attachment_links = params.get("attachment_links")
                lead_obj.save()

            # Get the new assigned_to ID
            current_assigned_to_id = (
                lead_obj.assigned_to.id if lead_obj.assigned_to else None
            )

            # Check if assigned_to has changed and send notification if it has
            if (
                current_assigned_to_id
                and current_assigned_to_id != previous_assigned_to_id
            ):
                recipients = [current_assigned_to_id]
                send_email_to_assigned_user.delay(recipients, lead_obj.id)

            # Handle file attachments
            if request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = request.profile.user
                attachment.file_name = request.FILES.get("lead_attachment").name
                attachment.lead = lead_obj
                attachment.attachment = request.FILES.get("lead_attachment")
                attachment.save()

            # Handle status conversion to account
            if params.get("status") == "converted":
                account_object = Account.objects.create(
                    created_by=request.profile.user,
                    name=params.get(
                        "lead_title", ""
                    ),  # Use lead_title as account name if available
                    description=params.get("description"),
                    website=params.get("website"),
                    lead=lead_obj,
                    org=request.profile.org,
                )

                # Move comments and attachments to the account
                comments = Comment.objects.filter(lead=self.lead_obj)
                if comments.exists():
                    for comment in comments:
                        comment.account_id = account_object.id

                attachments = Attachments.objects.filter(lead=self.lead_obj)
                if attachments.exists():
                    for attachment in attachments:
                        attachment.account_id = account_object.id

                # Notify the assigned user about the account conversion
                if lead_obj.assigned_to:
                    recipients = [lead_obj.assigned_to.id]
                    send_email_to_assigned_user.delay(recipients, lead_obj.id)

                # Associate comments with account
                for comment in lead_obj.leads_comments.all():
                    comment.account = account_object
                    comment.save()

                account_object.save()

                # update converted field if it is exists
                if params.get("converted") is not None:
                    lead_obj.converted = params.get("converted")
                    lead_obj.save()

                return Response(
                    {
                        "error": False,
                        "message": "Lead Converted to Account Successfully",
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {
                    "error": False,
                    "message": "Lead updated Successfully",
                    "id": str(lead_obj.id),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params1.organization_params,
        description="Lead Delete",
    )
    def delete(self, request, pk, **kwargs):
        self.object = self.get_object(pk)
        if (
            request.profile.role in ["ADMIN", "MANAGER"]
            or request.user.is_superuser
            or request.profile.user == self.object.created_by
            or (self.object.assigned_to and self.object.assigned_to == request.profile)
        ) and self.object.organization == request.profile.org:
            self.object.delete()
            return Response(
                {"error": False, "message": "Lead deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": "you don't have permission to delete this lead"},
            status=status.HTTP_403_FORBIDDEN,
        )


class LeadUploadView(APIView):
    model = Lead
    # authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params1.organization_params,
        request=LeadUploadSwaggerSerializer,
    )
    def post(self, request, *args, **kwargs):
        lead_form = LeadListForm(request.POST, request.FILES)
        if lead_form.is_valid():
            create_lead_from_file.delay(
                lead_form.validated_rows,
                lead_form.invalid_rows,
                request.profile.id,
                request.get_host(),
                request.profile.org.id,
            )
            return Response(
                {"error": False, "message": "Leads created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": lead_form.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LeadCommentView(APIView):
    model = Comment
    # authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params1.organization_params,
        request=LeadCommentEditSwaggerSerializer,
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role in ["ADMIN", "MANAGER"]
            or request.user.is_superuser
            or request.profile == obj.commented_by
        ):
            serializer = LeadCommentSerializer(obj, data=params)
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
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(tags=["Leads"], parameters=swagger_params1.organization_params)
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.profile.role in ["ADMIN", "MANAGER"]
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


class LeadAttachmentView(APIView):
    model = Attachments
    # authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params1.organization_params,
        request=AttachmentCreateSwaggerSerializer,
    )
    def post(self, request, format=None):
        """
        Create an attachment for a lead using data from Cloudinary
        """
        lead_id = request.data.get("lead_id")
        file_name = request.data.get("file_name")
        file_type = request.data.get("file_type", "")
        file_url = request.data.get("file_url")

        if not (lead_id and file_name and file_url):
            return Response(
                {"error": True, "errors": "Missing required data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lead = Lead.objects.get(id=lead_id)

            # Check permissions
            if lead.organization != request.profile.org:
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have permission for this lead",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            attachment = Attachments()
            attachment.created_by = request.profile.user
            attachment.file_name = file_name
            attachment.lead = lead

            # Save the Cloudinary URL instead of a file upload
            attachment.attachment = file_url
            attachment.save()

            return Response(
                {
                    "error": False,
                    "message": "Attachment created successfully",
                    "attachment_id": str(attachment.id),
                    "attachment": file_name,
                    "attachment_url": file_url,
                    "attachment_display": file_type,
                    "created_by": request.profile.user.email,
                    "created_on": attachment.created_at,
                    "file_type": (
                        file_type.split("/") if "/" in file_type else [file_type, ""]
                    ),
                    "download_url": file_url,
                },
                status=status.HTTP_201_CREATED,
            )

        except Lead.DoesNotExist:
            return Response(
                {"error": True, "errors": "Lead not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": True, "errors": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(tags=["Leads"], parameters=swagger_params1.organization_params)
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.profile.role in ["ADMIN", "MANAGER"]
            or request.user.is_superuser
            or request.profile.user == self.object.created_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Attachment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class CreateLeadFromSite(APIView):
    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params1.organization_params,
        request=CreateLeadFromSiteSwaggerSerializer,
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        api_key = params.get("apikey")
        # api_setting = APISettings.objects.filter(
        #     website=website_address, apikey=api_key).first()
        api_setting = APISettings.objects.filter(apikey=api_key).first()
        if not api_setting:
            return Response(
                {
                    "error": True,
                    "message": "You don't have permission, please contact the admin!.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if api_setting and params.get("description"):
            # user = User.objects.filter(is_admin=True, is_active=True).first()
            user = api_setting.created_by

            # Create Contact first
            try:
                # We need contact info from the form or use default values
                contact_name = params.get("contact_name", "Website Visitor")
                contact = Contact.objects.create(
                    first_name=contact_name,
                    email=params.get("email", ""),
                    phone=params.get("phone", ""),
                    description=params.get("message", ""),
                    created_by=user,
                    is_active=True,
                    org=api_setting.org,
                )

                # Create Lead with the contact
                lead = Lead.objects.create(
                    status="assigned",
                    lead_source=api_setting.website,
                    description=params.get("description"),
                    notes=params.get("message", ""),
                    created_by=user,
                    contact=contact,
                    organization=api_setting.org,
                )
                lead.assigned_to = user
                lead.save()

                # Send Email to Assigned Users
                site_address = request.scheme + "://" + request.META["HTTP_HOST"]
                send_lead_assigned_emails.delay(lead.id, [user.id], site_address)
            except Exception:
                pass

            return Response(
                {
                    "error": False,
                    "message": "Lead Created sucessfully.",
                    "id": str(lead.id),
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "message": "Invalid data"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CompaniesView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(tags=["Company"], parameters=swagger_params1.organization_params)
    def get(self, request, *args, **kwargs):
        try:
            companies = CompanyProfile.objects.all()
            serializer = CompanySerializer(companies, many=True)
            return Response(
                {"error": False, "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"error": True, "message": "Organization is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        tags=["Company"],
        description="Company Create",
        parameters=swagger_params1.organization_params,
        request=CompanySwaggerSerializer,
    )
    def post(self, request, *args, **kwargs):
        request.data["org"] = request.profile.org.id
        print(request.data)
        company = CompanySerializer(data=request.data)
        name = request.data.get("name")
        if name and CompanyProfile.objects.filter(name=name).exists():
            return Response(
                {"error": True, "message": "A company with this name already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if company.is_valid():
            company.save()
            return Response(
                {"error": False, "message": "Company created successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": True, "message": company.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CompanyDetail(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        try:
            return CompanyProfile.objects.get(pk=pk)
        except CompanyProfile.DoesNotExist:
            raise Http404

    @extend_schema(tags=["Company"], parameters=swagger_params1.organization_params)
    def get(self, request, pk, format=None):
        company = self.get_object(pk)
        serializer = CompanySerializer(company)
        return Response(
            {"error": False, "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Company"],
        description="Company Update",
        parameters=swagger_params1.organization_params,
        request=CompanySerializer,
    )
    def put(self, request, pk, format=None):
        company = self.get_object(pk)
        serializer = CompanySerializer(company, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "error": False,
                    "data": serializer.data,
                    "message": "Updated Successfully",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Company"], parameters=swagger_params1.organization_params)
    def delete(self, request, pk, format=None):
        company = self.get_object(pk)
        company.delete()
        return Response(
            {"error": False, "message": "Deleted successfully"},
            status=status.HTTP_200_OK,
        )
