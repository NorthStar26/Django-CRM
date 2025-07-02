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
        summary="Get companies list",
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
        summary="Create new company",
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
            companies = CompanyProfile.objects.filter(org=request.profile.org)
            serializer = CompanyListSerializer(companies, many=True)
            return Response(
                {"error": False, "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except:
            return Response(
                {"error": True, "message": "Organization is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        tags=["Companies"],
        description="Company Create",
        parameters=company_auth_headers,
        request=CompanySwaggerCreateSerializer
    )
    def post(self, request, *args, **kwargs):
        """Создать новую компанию"""
        print(request.data)

        company = CompanyCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )

        if company.is_valid():
            # ✅ Передаем org как объект в save()
            company_instance = company.save(org=request.profile.org)
            return Response(
                {"error": False, "message": "Company created successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": True, "message": company.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema_view(
    get=extend_schema(
        tags=["Companies"],
        summary="Get company details",
        parameters=company_auth_headers,
        responses={
            200: CompanyDetailSerializer,
            404: {"description": "Company not found"}
        }
    ),
    put=extend_schema(
        tags=["Companies"],
        summary="Update company",
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
        summary="Delete company",
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
        description="Company Update",
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

        serializer = CompanyCreateUpdateSerializer(company, data=request.data)
        if serializer.is_valid():

            serializer.save()
            return Response(
                {"error": False, "data": CompanyDetailSerializer(company).data, 'message': 'Updated Successfully'},
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