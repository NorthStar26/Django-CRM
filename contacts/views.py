import json

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Attachments, Comment, Profile
from common.serializer import (
    AttachmentsSerializer,
    BillingAddressSerializer,
    CommentSerializer,
)
from common.utils import COUNTRIES
from contacts.models import Contact, SALUTATION_CHOICES, LANGUAGE_CHOICES

# from common.external_auth import CustomDualAuthentication
from contacts import swagger_params1
from contacts.serializer import *
from contacts.tasks import send_email_to_assigned_user
from tasks.serializer import TaskSerializer
from teams.models import Teams
from companies.models import CompanyProfile
from contacts.serializer import ContactBasicSerializer


def format_serializer_errors(errors):
    """
    Converts serializer errors to a string for message.
    """
    messages = []
    for field, errs in errors.items():
        if isinstance(errs, (list, tuple)):
            for err in errs:
                messages.append(f"{field}: {err}")
        else:
            messages.append(f"{field}: {errs}")
    return "; ".join(messages)


class ContactsListView(APIView, LimitOffsetPagination):
    # authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Contact

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by(
            "-id"
        )

        context = {}
        # Remove the restrictive filter - all users in the organization should see all contacts
        # if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
        #     queryset = queryset.filter(
        #         Q(assigned_to__in=[self.request.profile])
        #         | Q(created_by=self.request.profile.user)
        #     ).distinct()
        # Applying filters from request parameters
        if params:
            if params.get("name"):
                queryset = queryset.filter(
                    Q(first_name__icontains=params.get("name"))
                    | Q(last_name__icontains=params.get("name"))
                )
            if params.get("city"):
                queryset = queryset.filter(address__city__icontains=params.get("city"))
            if params.get("phone"):
                queryset = queryset.filter(mobile_number__icontains=params.get("phone"))
            if params.get("email"):
                queryset = queryset.filter(primary_email__icontains=params.get("email"))
            if params.get("company"):
                queryset = queryset.filter(company_id=params.get("company"))
                print(f"Filtering by company: {params.get('company')}")
                print(f"Contacts found: {queryset.count()}")
            if params.get("company_name"):
                queryset = queryset.filter(
                    company__name__icontains=params.get("company_name")
                )
                print(f"Filtering by company name: {params.get('company_name')}")
                print(f"Contacts found: {queryset.count()}")
            #     queryset = queryset.filter(
            #         assigned_to__id__in=params.get("assigned_to")
            #     ).distinct()
            if params.get("department"):
                queryset = queryset.filter(
                    department__icontains=params.get("department")
                )
                print(f"Filtering by department: {params.get('department')}")
                print(f"Contacts found: {queryset.count()}")
                context["selected_department"] = params.get("department")

            sort_field = params.get("sort_by", "-id")
            sort_order = params.get("sort_order", "")

            if sort_field == "department":
                if sort_order and sort_order.lower() == "desc":
                    queryset = queryset.order_by("-department")
                else:
                    queryset = queryset.order_by("department")
            else:
                queryset = queryset.order_by(sort_field if sort_field else "-id")

        results_contact = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        contacts = ContactSerializer(results_contact, many=True).data
        if results_contact:
            offset = queryset.filter(id__gte=results_contact[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context.update({"contacts_count": self.count, "offset": offset})
        context["contact_obj_list"] = contacts

        # Add users for filters and drop-down lists
        #         users = Profile.objects.filter(is_active=True, org=self.request.profile.org).values(
        #             "id", "user__email"
        #         )
        #         context["users"] = users

        # Add companies for filters
        companies = CompanyProfile.objects.filter(org=self.request.profile.org).values(
            "id", "name"
        )
        context["companies"] = companies
        # Add unique job titles for filters
        job_titles = (
            self.model.objects.filter(org=self.request.profile.org)
            .exclude(title__isnull=True)
            .exclude(title__exact="")
            .values_list("title", flat=True)
            .distinct()
        )
        context["job_titles"] = list(job_titles)

        departments = (
            self.model.objects.filter(org=self.request.profile.org)
            .exclude(department__isnull=True)
            .exclude(department__exact="")
            .values_list("department", flat=True)
            .distinct()
            .order_by("department")
        )
        context["departments"] = list(departments)

        return context

    @extend_schema(
        tags=["contacts"], parameters=swagger_params1.contact_list_get_params
    )
    def get(self, request, *args, **kwargs):
        """Getting a list of contacts with filtering by companies and other parameters"""

        if not hasattr(request, "profile") or not request.profile:
            return Response(
                {"error": True, "errors": "Profile not found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if request.profile.role != "ADMIN" and not request.profile.is_admin:
            if not request.profile.is_active:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        if not request.profile.org:
            return Response(
                {"error": True, "errors": "Organization not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Getting context data taking into account all filters
            context = self.get_context_data(**kwargs)

            #  Forming the response structure to match the rest of the API
            return Response(
                {"error": False, "data": context}, status=status.HTTP_200_OK
            )

        except Exception as e:
            import traceback

            print(f"Error getting contacts: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": True, "errors": f"Error getting contacts: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params1.organization_params,
        request=CreateContactSerializer,
    )
    def post(self, request, *args, **kwargs):  ##new version ##
        params = request.data

        if not hasattr(request, "profile") or not request.profile:
            return Response(
                {"error": True, "errors": "Profile not found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if request.profile.role != "ADMIN" and not request.profile.is_admin:
            if not request.profile.is_active:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        if not request.profile.org:
            return Response(
                {"error": True, "errors": "Organization not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        #  CreateContactSerializer expects a request_obj
        contact_serializer = CreateContactSerializer(
            data=params,
            request_obj=request,
            context={"request": request},  # Add context to the serializer
        )

        if not contact_serializer.is_valid():
            error_details = {
                k: [str(e) for e in v] for k, v in contact_serializer.errors.items()
            }
            error_message = format_serializer_errors(contact_serializer.errors)
            return Response(
                {
                    "error": True,
                    "message": error_message or "Validation error",
                    "details": error_details,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contact_obj = contact_serializer.save()
            contact_obj.org = request.profile.org
            contact_obj.is_active = True
            contact_obj.save()

            print(f"Contact created successfully: {contact_obj.id}")
            print(f"Created by: {request.profile.user.email}")
            print(f"Organization: {request.profile.org}")
            print(f"Is active: {contact_obj.is_active}")

            return Response(
                {
                    "error": False,
                    "message": "Contact created successfully",
                    "contact_id": str(contact_obj.id),
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            import traceback

            print(f"Error creating contact: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": True, "errors": f"Failed to create contact: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ContactDetailView(APIView):
    # #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Contact

    def get_object(self, pk):
        return get_object_or_404(Contact, pk=pk)

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params1.organization_params,
        request=CreateContactSerializer,
    )
    def patch(self, request, pk, format=None):  # new version - partial update
        """Partially update a specific contact by ID"""

        params = request.data
        if not hasattr(request, "profile") or not request.profile:
            return Response(
                {"error": True, "errors": "Profile not found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if request.profile.role != "ADMIN" and not request.profile.is_admin:
            if not request.profile.is_active:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        if not request.profile.org:
            return Response(
                {"error": True, "errors": "Organization not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            contact_obj = self.get_object(pk)
            if contact_obj.org != request.profile.org:
                return Response(
                    {"error": True, "errors": "Contact not found in your organization"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if request.profile.role != "ADMIN" and not request.profile.is_admin:
                if request.profile != contact_obj.created_by:
                    return Response(
                        {
                            "error": True,
                            "errors": "You do not have Permission to update this contact",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            contact_serializer = CreateContactSerializer(
                data=params,
                instance=contact_obj,
                request_obj=request,
                context={"request": request},
                partial=True,
            )
            if not contact_serializer.is_valid():
                error_details = {
                    k: [str(e) for e in v] for k, v in contact_serializer.errors.items()
                }
                error_message = format_serializer_errors(contact_serializer.errors)
                return Response(
                    {
                        "error": True,
                        "message": error_message or "Validation error",
                        "details": error_details,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            updated_contact = contact_serializer.save()
            updated_data = ContactBasicSerializer(updated_contact).data

            print(f"Contact partially updated: {updated_contact.id}")
            print(f"Updated by: {request.profile.user.email}")
            print(f"Updated fields: {list(params.keys())}")

            return Response(
                {
                    "error": False,
                    "message": "Contact updated successfully",
                    "contact_id": str(updated_contact.id),
                    "updated_contact": updated_data,
                },
                status=status.HTTP_200_OK,
            )

        except Contact.DoesNotExist:
            return Response(
                {"error": True, "errors": "Contact not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            import traceback

            print(f"Error updating contact: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": True, "errors": f"Failed to update contact: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(tags=["contacts"], parameters=swagger_params1.organization_params)
    def get(self, request, pk, format=None):  # New version Get by id
        """Get a specific contact by ID"""

        if not hasattr(request, "profile") or not request.profile:
            return Response(
                {"error": True, "errors": "Profile not found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            contact_obj = self.get_object(pk)

            if contact_obj.org != request.profile.org:
                return Response(
                    {"error": True, "errors": "Contact not found in your organization"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if request.profile.role != "ADMIN" and not request.profile.is_admin:
                if request.profile != contact_obj.created_by:
                    return Response(
                        {
                            "error": True,
                            "errors": "You do not have Permission to view this contact",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            contact_data = ContactBasicSerializer(contact_obj).data

            context = {"error": False, "contact": contact_data}

            return Response(context, status=status.HTTP_200_OK)

        except Contact.DoesNotExist:
            return Response(
                {"error": True, "errors": "Contact not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": True, "errors": f"Failed to retrieve contact: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(tags=["contacts"], parameters=swagger_params1.organization_params)
    def delete(self, request, pk, format=None):  # NEW version
        """Delete a specific contact by ID"""
        if not hasattr(request, "profile") or not request.profile:
            return Response(
                {"error": True, "errors": "Profile not found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            contact_obj = self.get_object(pk)
            if contact_obj.org != request.profile.org:
                return Response(
                    {"error": True, "errors": "Contact not found in your organization"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if request.profile.role != "ADMIN" and not request.profile.is_admin:
                if request.profile != contact_obj.created_by:
                    return Response(
                        {
                            "error": True,
                            "errors": "You do not have Permission to delete this contact",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            contact_obj.delete()

            return Response(
                {
                    "error": False,
                    "message": "Contact deleted successfully",
                },
                status=status.HTTP_200_OK,
            )

        except Contact.DoesNotExist:
            return Response(
                {"error": True, "errors": "Contact not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": True, "errors": f"Failed to delete contact: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params1.organization_params,
        request=ContactDetailEditSwaggerSerializer,
    )
    def post(self, request, pk, **kwargs):
        params = request.data
        context = {}
        self.contact_obj = Contact.objects.get(pk=pk)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.contact_obj.created_by)
                or (self.request.profile in self.contact_obj.assigned_to.all())
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
                    contact_id=self.contact_obj.id,
                    commented_by_id=self.request.profile.id,
                    org=request.profile.org,
                )

        if self.request.FILES.get("contact_attachment"):
            attachment = Attachments()
            attachment.created_by = request.profile
            attachment.file_name = self.request.FILES.get("contact_attachment").name
            attachment.contact = self.contact_obj
            attachment.attachment = self.request.FILES.get("contact_attachment")
            attachment.save()

        comments = Comment.objects.filter(contact__id=self.contact_obj.id).order_by(
            "-id"
        )
        attachments = Attachments.objects.filter(
            contact__id=self.contact_obj.id
        ).order_by("-id")
        context.update(
            {
                "contact_obj": ContactSerializer(self.contact_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)


class ContactCommentView(APIView):
    model = Comment
    # #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @extend_schema(
        tags=["contacts"],
        parameters=swagger_params1.organization_params,
        request=ContactCommentEditSwaggerSerializer,
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=params)
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
                "errors": "You don't have permission to edit this Comment",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(tags=["contacts"], parameters=swagger_params1.organization_params)
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
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
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class ContactAttachmentView(APIView):
    model = Attachments
    # #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(tags=["contacts"], parameters=swagger_params1.organization_params)
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.profile.role == "ADMIN"
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
                "errors": "You don't have permission to delete this Attachment",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
