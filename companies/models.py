import re
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import RegexValidator, EmailValidator, URLValidator

from common.models import Org, Profile
from common.base import BaseModel
from common.utils import COUNTRIES, INDCHOICES
from emails.models import Email


class CompanyProfile(BaseModel):
    name = models.CharField(
        _("Company Name"),
        max_length=255,
        blank=False,
        null=False,
        db_index=True, # Indexing for faster lookups
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\.\&\(\)]+$',
                message='Company name can only contain letters, numbers, spaces, hyphens, dots, ampersands, and parentheses'
            )
        ]
    )

    website = models.CharField(
        _("Website"),
        max_length=255,
        blank=False,
        null=False,
        help_text=_("Website URL of the company"),
        validators=[
            URLValidator(
                schemes=['http', 'https'],
                message='Website must be a valid URL starting with http:// or https://'
            )
        ]
    )

    email = models.EmailField(
        _("Email"),
        max_length=255,
        blank=False,
        null=False,
        db_index=True,  # Indexing for faster lookups
        validators=[
            EmailValidator(
                message=_("Enter a valid email address."),
                code='invalid_email'
            )
        ]

    )

    phone = PhoneNumberField(
        _("Phone Number"),
        blank=False,
        null=False,
        help_text="International format: +31234567890"
    )

    industry = models.CharField(
        _("Industry Type"),
        max_length=255,
        choices=INDCHOICES,
        blank=False,
        null=False,
        help_text=_("Select the industry type of the company"),
        db_index=True # Indexing for faster lookups
    )

    # Billing Address
    billing_street = models.CharField(
        _("Billing Street"),
        max_length=255,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\.\,\'\"]+$',
                message='Street address contains invalid characters'
            )
        ]
    )

    billing_address_number = models.CharField(
        _("Billing Address Number"),
        max_length=50,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\-\/\s]+$',
                message='Address number can only contain letters, numbers, hyphens, slashes, and spaces'
            )
        ]
    )

    billing_postcode = models.CharField(
        _("Billing Postcode"),
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9\s\-]+$',
                message='Postcode format is invalid'
            )
        ]
    )

    billing_city = models.CharField(
        _("Billing City"),
        max_length=100,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.]+$',
                message='City name can only contain letters, spaces, hyphens, apostrophes, and dots'
            )
        ]
    )

    billing_country = models.CharField(
        _("Billing Country"),
        max_length=3,
        choices=COUNTRIES,
        blank=True,
        null=True
    )

 # Control system
    org = models.ForeignKey(
        Org,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="companies",
        verbose_name=_("Organization"),
        db_index=True
    )

    class Meta:
        verbose_name = _("Company Profile")
        verbose_name_plural = _("Company Profiles")
        db_table = "companies"
        ordering = ("-created_at",)
        unique_together = [('name', 'org'), # Uniqueness of the name within the organization
                           ('email', 'org'), # Uniqueness of email within the organization
                           ('website', 'org')  # Uniqueness of website within the organization
                           ]
        indexes = [
            models.Index(fields=['name', 'org']),
            models.Index(fields=['email', 'org']),
            models.Index(fields=['website', 'org']),
            models.Index(fields=['industry']),
            models.Index(fields=['created_at']),
        ]


    def clean(self):

        errors = {}

        if self.name:
            self.name = self.name.strip()
            if len(self.name) < 2:
                errors['name'] = _("Company name must be at least 2 characters long")
            elif len(self.name) > 255:
                errors['name'] = _("Company name cannot exceed 255 characters")

        if not self.industry:
            errors['industry'] = _("Industry is required")
        elif self.industry not in dict(INDCHOICES):
            errors['industry'] = _("Please select a valid industry")

        if self.email:
            self.email = self.email.strip().lower()
            # Check for corporate domains
            forbidden_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
            if any(domain in self.email for domain in forbidden_domains):
                errors['email'] = _("Please use a business email address")

        # Validate address completeness
        billing_fields = [self.billing_street, self.billing_city, self.billing_country]
        billing_provided = [field for field in billing_fields if field]

        if billing_provided and len(billing_provided) < len(billing_fields):
            errors['billing_address'] = _("If billing address is provided, street, city, and country are required")
        if errors:
            raise ValidationError(errors)



    def __str__(self):
        return f"{self.name}"

    @property
    def full_billing_address(self):
        """Returns the full billing address"""
        address_parts = [
            self.billing_street,
            self.billing_address_number,
            self.billing_city,
            self.billing_postcode,
            self.get_billing_country_display() if self.billing_country else None
        ]
        return ", ".join([part for part in address_parts if part])

    @property
    def contact_info(self):
        """Returns contact information"""
        contacts = []
        if self.email:
            contacts.append(f"Email: {self.email}")
        if self.phone:
            contacts.append(f"Phone: {self.phone}")
        if self.website:
            contacts.append(f"Website: {self.website}")
        return " | ".join(contacts)