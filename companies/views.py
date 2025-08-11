from django.db import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view

from rest_framework.pagination import LimitOffsetPagination

from .models import CompanyProfile
from .serializer import (
    CompanyListSerializer,
    CompanyDetailSerializer,
    CompanyCreateUpdateSerializer,
    CompanySwaggerCreateSerializer,
    CompanySwaggerListSerializer,
    CompanyLogoUpdateSerializer,
)
from .swagger_params1 import company_list_get_params, company_auth_headers


def format_serializer_errors(serializer_errors):
    """Преобразует ошибки serializer в читаемый формат"""
    if isinstance(serializer_errors, dict):
        formatted_errors = []
        for field, errors in serializer_errors.items():
            if field == "non_field_errors":
                formatted_errors.extend([str(error) for error in errors])
            else:
                field_errors = [f"{field}: {str(error)}" for error in errors]
                formatted_errors.extend(field_errors)
        return "; ".join(formatted_errors) if formatted_errors else "Validation failed"
    return str(serializer_errors)


@extend_schema_view(
    get=extend_schema(
        tags=["Companies"],
        description="Retrieve list of companies with filtering and pagination",
        parameters=company_list_get_params + company_auth_headers,
        responses={
            200: CompanySwaggerListSerializer(many=True),
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden"},
        },
    ),
    post=extend_schema(
        tags=["Companies"],
        description="Create a new company in the organization",
        parameters=company_auth_headers,
        request=CompanySwaggerCreateSerializer,
        responses={
            200: CompanyDetailSerializer,
            400: {"description": "Bad Request"},
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden"},
        },
    ),
)


class CompanyListView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CompanyListSerializer

    @extend_schema(
        tags=["Companies"], parameters=company_list_get_params + company_auth_headers
    )

    def get(self, request, *args, **kwargs):
        try:
            companies = CompanyProfile.objects.filter(org=request.profile.org)
            name_search = request.query_params.get("name")
            if name_search:
                companies = companies.filter(name__icontains=name_search)
            country_filter = request.query_params.get("billing_country")
            if country_filter:
                companies = companies.filter(billing_country=country_filter)
            industry_filter = request.query_params.get("industry")
            if industry_filter:
                companies = companies.filter(industry=industry_filter)
            companies = companies.order_by("-created_at")

            # 1. Create a paginator instance
            paginator = LimitOffsetPagination()
            # 2. Paginate the queryset
            paginated_companies = paginator.paginate_queryset(companies, request, view=self)
            # 3. Serialize the paginated data
            serializer = CompanyListSerializer(paginated_companies, many=True)
             # 4.   Return the paginated response
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            import traceback
            print(f"Error getting companies: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": True, "message": f"Error getting companies: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # def get(self, request, *args, **kwargs):
    #     """Get a list of companies with filtering"""
    #     try:
    #         print(f"Getting companies for user: {request.user}")
    #         print(f"Request profile: {getattr(request, 'profile', 'Not found')}")

    #         companies = CompanyProfile.objects.filter(org=request.profile.org)
    #         name_search = request.query_params.get("name", None)
    #         if name_search:
    #             companies = companies.filter(name__icontains=name_search)
    #             print(f"Searching by name: {name_search}")

    #         country_filter = request.query_params.get("billing_country", None)
    #         if country_filter:
    #             companies = companies.filter(billing_country=country_filter)
    #             print(f"Filtering by country: {country_filter}")

    #         industry_filter = request.query_params.get("industry", None)
    #         if industry_filter:
    #             companies = companies.filter(industry=industry_filter)
    #             print(f"Filtering by industry: {industry_filter}")

    #         companies = companies.order_by("-created_at")

    #         serializer = CompanyListSerializer(companies, many=True)
    #         return Response(
    #             {"error": False, "data": serializer.data},
    #             status=status.HTTP_200_OK,
    #         )
    #     except Exception as e:
    #         import traceback

    #         print(f"Error getting companies: {str(e)}")
    #         print(f"Traceback: {traceback.format_exc()}")
    #         return Response(
    #             {"error": True, "message": f"Error getting companies: {str(e)}"},
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )

    @extend_schema(
        tags=["Companies"],
        description="Company Create",
        parameters=company_auth_headers,
        request=CompanySwaggerCreateSerializer,
    )
    def post(self, request, *args, **kwargs):
        """Create a new company in the organization"""
        try:
            print(f"Creating company with data: {request.data}")
            print(f"Request user: {request.user}")
            print(f"Request profile: {getattr(request, 'profile', 'Not found')}")
            print(
                f"Request profile org: {getattr(request.profile, 'org', 'Not found') if hasattr(request, 'profile') else 'No profile'}"
            )

            # Check if the request data contains a name
            if not request.data.get("name"):
                return Response(
                    {"error": True, "message": "Company name is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if the user has a valid profile and organization
            if not hasattr(request, "profile") or not request.profile.org:
                return Response(
                    {"error": True, "message": "Organization is missing or invalid"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate the request data using the serializer
            company = CompanyCreateUpdateSerializer(
                data=request.data, context={"request": request}
            )

            if not company.is_valid():
                error_details = {
                    k: [str(e) for e in v] for k, v in company.errors.items()
                }
                error_message = format_serializer_errors(company.errors)
                return Response(
                    {"error": True, "message": error_message, "details": error_details},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                company_instance = company.save()
            except serializers.ValidationError as e:
                # Handling errors thrown in create()
                error_details = {k: [str(vv) for vv in v] for k, v in e.detail.items()}
                return Response(
                    {
                        "error": True,
                        "message": "Validation error",
                        "details": error_details,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "error": False,
                    "message": "Company created successfully",
                    "data": CompanyDetailSerializer(company_instance).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except IntegrityError as e:
            # Handle unique constraint violations
            error_message = (
                "A company with this information already exists in your organization"
            )

            if "name" in str(e).lower():
                error_message = (
                    "Company with this name already exists in your organization"
                )
            elif "email" in str(e).lower():
                error_message = (
                    "Company with this email already exists in your organization"
                )
            elif "website" in str(e).lower():
                error_message = (
                    "Company with this website already exists in your organization"
                )

            return Response(
                {"error": True, "message": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ValidationError as e:
            error_message = str(e)
            if hasattr(e, "message_dict"):
                error_message = format_serializer_errors(e.message_dict)

            return Response(
                {"error": True, "message": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            import traceback

            print(f"Unexpected error creating company: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": True, "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema_view(
    get=extend_schema(
        tags=["Companies"],
        parameters=company_auth_headers,
        responses={
            200: CompanyDetailSerializer,
            404: {"description": "Company not found"},
        },
    ),
    patch=extend_schema(
        tags=["Companies"],
        parameters=company_auth_headers,
        request=CompanySwaggerCreateSerializer,
        responses={
            200: CompanyDetailSerializer,
            400: {"description": "Bad Request"},
            404: {"description": "Company not found"},
        },
    ),
    delete=extend_schema(
        tags=["Companies"],
        parameters=company_auth_headers,
        responses={
            200: {"description": "Company deleted successfully"},
            404: {"description": "Company not found"},
        },
    ),
)
class CompanyDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        """Get the company object"""
        try:
            return CompanyProfile.objects.get(pk=pk)
        except CompanyProfile.DoesNotExist:
            raise Http404

    @extend_schema(tags=["Companies"], parameters=company_auth_headers)
    def get(self, request, pk, format=None):
        """Get company details"""
        company = self.get_object(pk)

        if company.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "message": "User company doesnot match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CompanyDetailSerializer(company)
        return Response(
            {"error": False, "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Companies"],
        parameters=company_auth_headers,
        request=CompanySwaggerCreateSerializer,
    )
    def patch(self, request, pk, format=None):
        """Partial update company"""
        company = self.get_object(pk)

        if company.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "message": "User company doesnot match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Role-based permission check for company updates
        if request.profile.role == "USER":
            # Users can only update companies they created
            if company.created_by != request.profile.user:
                return Response(
                    {
                        "error": True,
                        "message": "You do not have permission to update this company",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        # Admin and Manager can update any company (no additional check needed)

        serializer = CompanyCreateUpdateSerializer(
            company, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            updated_company = serializer.save()
            return Response(
                {
                    "error": False,
                    "data": CompanyDetailSerializer(updated_company).data,
                    "message": "Updated Successfully",
                },
                status=status.HTTP_200_OK,
            )
        error_message = format_serializer_errors(serializer.errors)
        return Response(
            {"error": True, "message": error_message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Companies"], parameters=company_auth_headers)
    def delete(self, request, pk, format=None):
        """Delete company"""
        company = self.get_object(pk)

        if company.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "message": "User company doesnot match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Role-based permission check for company deletion
        if request.profile.role == "USER":
            # Users can only delete companies they created
            if company.created_by != request.profile.user:
                return Response(
                    {
                        "error": True,
                        "message": "You do not have permission to delete this company",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        # Admin and Manager can delete any company (no additional check needed)

        company.delete()
        return Response(
            {"error": False, "message": "Company deleted successfully"},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    put=extend_schema(
        tags=["Companies"],
        description="Update company logo",
        parameters=company_auth_headers,
        request=CompanyLogoUpdateSerializer,
        responses={
            200: {"description": "Logo updated successfully"},
            400: {"description": "Invalid logo URL"},
            404: {"description": "Company not found"},
        },
    )
)
class CompanyLogoUploadView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, pk, *args, **kwargs):
        try:
            company = CompanyProfile.objects.get(pk=pk)
        except CompanyProfile.DoesNotExist:
            return Response(
                {"error": True, "message": "Company not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check organization match
        if company.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "message": "Access denied: company does not belong to your organization",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ✅ FIXED: add partial=True
        serializer = CompanyLogoUpdateSerializer(
            company, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"error": False, "message": "Logo updated successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": True, "message": "Invalid input", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
