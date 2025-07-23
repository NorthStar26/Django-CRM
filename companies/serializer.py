from rest_framework import serializers
from common.serializer import UserSerializer, OrganizationSerializer
from .models import CompanyProfile
from django.utils.translation import gettext_lazy as _
import re
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from urllib.parse import urlparse

class CompanySwaggerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = [
            'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country', 'billing_state','logo_url'
        ]


class CompanySwaggerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'name', 'email', 'phone', 'website', 'industry',
            'billing_city', 'billing_country', 'billing_state', 'created_at'
        ]


class CompanyListSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    organization = OrganizationSerializer(source='org', read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country', 'billing_state',
            'logo_url',
            'created_by', 'organization', 'created_at', 'updated_at'
        ]


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed information about the company"""
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    organization = OrganizationSerializer(source='org', read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country', 'billing_state',
            'logo_url',
            'created_by', 'updated_by', 'organization',
            'created_at', 'updated_at'
        ]


class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = [
            'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country', 'billing_state','logo_url'
        ]
    def update(self, instance, validated_data):
        request = self.context.get('request')

        if request and hasattr(request, 'profile'):
            org = request.profile.org

            # Duplicate Name Check (Excluding Current Company)
            if 'name' in validated_data:
                if CompanyProfile.objects.filter(
                    name__iexact=validated_data['name'],
                    org=org
                ).exclude(id=instance.id).exists():
                    raise serializers.ValidationError({
                        'name': [_("Another company with this name already exists in your organization")]
                    })
            if 'email' in validated_data and validated_data['email']:
                if CompanyProfile.objects.filter(
                    email=validated_data['email'],
                    org=org
                ).exclude(id=instance.id).exists():
                    raise serializers.ValidationError({
                        'email': [_("Another company with this email already exists in your organization")]
                    })
            if 'website' in validated_data and validated_data['website']:
                if CompanyProfile.objects.filter(
                    website=validated_data['website'],
                    org=org
                ).exclude(id=instance.id).exists():
                    raise serializers.ValidationError({
                        'website': [_("Another company with this website already exists in your organization")]
                    })

        return super().update(instance, validated_data)

    def create(self, validated_data):
        """Create with org"""
        request = self.context.get('request')

        # Set org from request
        if request and hasattr(request, 'profile') and request.profile.org:
            validated_data['org'] = request.profile.org

        # Check for duplicates
        if 'org' in validated_data:
            org = validated_data['org']

            # Check duplicate by name
            if CompanyProfile.objects.filter(
                name__iexact=validated_data['name'],
                org=org
            ).exists():
                raise serializers.ValidationError({
                    'name': [_("Company with this name already exists in your organization")]
                })

            if 'email' in validated_data and validated_data['email']:
                if CompanyProfile.objects.filter(
                    email=validated_data['email'],
                    org=org
                ).exists():
                    raise serializers.ValidationError({
                        'email': [_("Another company with this email already exists in your organization")]
                    })
            if 'website' in validated_data and validated_data['website']:
                if CompanyProfile.objects.filter(
                    website=validated_data['website'],
                    org=org
                ).exists():
                    raise serializers.ValidationError({
                        'website': [_("Another company with this website already exists in your organization")]
                    })

        return super().create(validated_data)

    def validate_website(self, value):

        if not value:
            return None

        value = value.strip()
        if not value.startswith(('http://', 'https://')):
            value = f'https://{value}'

        url_validator = URLValidator(schemes=['http', 'https'])
        try:
            url_validator(value)
        except DjangoValidationError:
            raise serializers.ValidationError(
                _("Enter a valid website URL (e.g., https://example.com)")
            )

        if len(value) > 255:
            raise serializers.ValidationError(
                _("Website URL is too long (maximum 255 characters)")
            )

        return value

class CompanyLogoUpdateSerializer(serializers.ModelSerializer):
    logo_url = serializers.URLField(required=False, allow_null=True)
    class Meta:
        model = CompanyProfile
        fields = ['logo_url']
