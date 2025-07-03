from django.db import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import CompanyProfile
from .serializer import (
    CompanyListSerializer,
    CompanyDetailSerializer,
    CompanyCreateUpdateSerializer,
    CompanySwaggerCreateSerializer,
    CompanySwaggerListSerializer
)
from .swagger_params1 import company_list_get_params, company_auth_headers


@extend_schema_view(
    get=extend_schema(
        tags=["Companies"],
        description="Retrieve list of companies with filtering and pagination",
        parameters=company_list_get_params + company_auth_headers,
        responses={
            200: CompanySwaggerListSerializer(many=True),
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden"}
        }
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
            403: {"description": "Forbidden"}
        }
    )
)
class CompanyListView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(tags=["Companies"], parameters=company_list_get_params + company_auth_headers)
    def get(self, request, *args, **kwargs):
        """Get a list of companies with filtering"""
        try:
            print(f"Getting companies for user: {request.user}")
            print(f"Request profile: {getattr(request, 'profile', 'Not found')}")
            companies = CompanyProfile.objects.filter(org=request.profile.org)
            serializer = CompanyListSerializer(companies, many=True)
            return Response(
                {"error": False, "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            import traceback
            print(f"Error getting companies: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": True, "message": f"Error getting companies: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        tags=["Companies"],
        description="Company Create",
        parameters=company_auth_headers,
        request=CompanySwaggerCreateSerializer
    )
    def post(self, request, *args, **kwargs):
        """Create a new company in the organization"""
        try:
            print(f"Creating company with data: {request.data}")
            print(f"Request user: {request.user}")
            print(f"Request profile: {getattr(request, 'profile', 'Not found')}")
            print(f"Request profile org: {getattr(request.profile, 'org', 'Not found') if hasattr(request, 'profile') else 'No profile'}")

            # Check if the request data contains a name
            if not request.data.get('name'):
                return Response(
                    {"error": True, "message": "Company name is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if the user has a valid profile and organization
            if not hasattr(request, 'profile') or not request.profile.org:
                return Response(
                    {"error": True, "message": "Organization is missing or invalid"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            #Validate the request data using the serializer
            company = CompanyCreateUpdateSerializer(
                data=request.data,
                context={'request': request}
            )

            if not company.is_valid():
                error_messages = {}

                for field, errors in company.errors.items():
                    if field == 'non_field_errors':
                        error_messages['general'] = [str(error) for error in errors]
                    else:
                        error_messages[field] = [str(error) for error in errors]

                return Response(
                    {
                        "error": True,
                        "message": "Validation failed",
                        "details": error_messages
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            company_instance = company.save()

            return Response(
                {
                    "error": False,
                    "message": "Company created successfully",
                    "data": CompanyDetailSerializer(company_instance).data
                },
                status=status.HTTP_201_CREATED,
            )

        except IntegrityError as e:
            # Handle unique constraint violations
            error_message = "A company with this information already exists in your organization"

            if "name" in str(e).lower():
                error_message = "Company with this name already exists in your organization"
            elif "email" in str(e).lower():
                error_message = "Company with this email already exists in your organization"

            return Response(
                {"error": True, "message": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ValidationError as e:
            return Response(
                {
                    "error": True,
                    "message": "Validation error",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                },
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
            404: {"description": "Company not found"}
        }
    ),
    put=extend_schema(
        tags=["Companies"],
        parameters=company_auth_headers,
        request=CompanySwaggerCreateSerializer,
        responses={
            200: CompanyDetailSerializer,
            400: {"description": "Bad Request"},
            404: {"description": "Company not found"}
        }
    ),
    delete=extend_schema(
        tags=["Companies"],
        parameters=company_auth_headers,
        responses={
            200: {"description": "Company deleted successfully"},
            404: {"description": "Company not found"}
        }
    )
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
                {"error": True, "message": "User company doesnot match with header...."},
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
        request=CompanySwaggerCreateSerializer
    )
    def put(self, request, pk, format=None):
        """Update company"""
        company = self.get_object(pk)


        if company.org != request.profile.org:
            return Response(
                {"error": True, "message": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CompanyCreateUpdateSerializer(
            company,
            data=request.data,
            context={'request': request})
        if serializer.is_valid():

            updated_company = serializer.save()
            return Response(
                {"error": False, "data": CompanyDetailSerializer(
                    updated_company).data, 'message': 'Updated Successfully'},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, 'message': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Companies"], parameters=company_auth_headers)
    def delete(self, request, pk, format=None):
        """Delete company"""
        company = self.get_object(pk)


        if company.org != request.profile.org:
            return Response(
                {"error": True, "message": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )

        company.delete()
        return Response(
            {"error": False, 'message': 'Company deleted successfully'},
            status=status.HTTP_200_OK,
        )