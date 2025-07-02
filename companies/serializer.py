from rest_framework import serializers
from common.serializer import UserSerializer, OrganizationSerializer
from .models import CompanyProfile


class CompanySwaggerCreateSerializer(serializers.ModelSerializer):
    """Swagger serializer for company creation"""
    class Meta:
        model = CompanyProfile
        fields = [
            'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country'
        ]


class CompanySwaggerListSerializer(serializers.ModelSerializer):
    """Swagger serializer for list of companies"""
    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'name', 'email', 'phone', 'website', 'industry',
            'billing_city', 'billing_country', 'created_at'
        ]


class CompanyListSerializer(serializers.ModelSerializer):
    """Serializer for list of companies"""
    created_by = UserSerializer(read_only=True)
    organization = OrganizationSerializer(source='org', read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country',
            'created_by', 'organization', 'created_at', 'updated_at'
        ]


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed company information"""
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    organization = OrganizationSerializer(source='org', read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country',
            'created_by', 'updated_by', 'organization',
            'created_at', 'updated_at'
        ]


class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating a company"""

    class Meta:
        model = CompanyProfile
        fields = [
            'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country'
        ]