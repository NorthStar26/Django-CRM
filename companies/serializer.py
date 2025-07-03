from rest_framework import serializers
from common.serializer import UserSerializer, OrganizationSerializer
from .models import CompanyProfile
from django.utils.translation import gettext_lazy as _


class CompanySwaggerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = [
            'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country'
        ]


class CompanySwaggerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'name', 'email', 'phone', 'website', 'industry',
            'billing_city', 'billing_country', 'created_at'
        ]


class CompanyListSerializer(serializers.ModelSerializer):
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
    """Serializer for detailed information about the company"""
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
    class Meta:
        model = CompanyProfile
        fields = [
            'name', 'email', 'phone', 'website', 'industry',
            'billing_street', 'billing_address_number', 'billing_city',
            'billing_postcode', 'billing_country'
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

        return super().create(validated_data)