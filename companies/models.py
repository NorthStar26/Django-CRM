from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from common.models import Org, Profile
from common.base import BaseModel
from common.utils import COUNTRIES, INDCHOICES


class CompanyProfile(BaseModel):
    name = models.CharField(
        _("Company Name"),
        max_length=255,
        blank=False,
        null=False
    )

    website = models.URLField(
        _("Website"),
        max_length=255,
        blank=True,
        null=True
    )

    email = models.EmailField(
        _("Email"),
        max_length=255,
        blank=True,
        null=True
    )

    phone = PhoneNumberField(
        _("Phone Number"),
        blank=True,
        null=True
    )

    industry = models.CharField(
        _("Industry Type"),
        max_length=255,
        choices=INDCHOICES,
        blank=True,
        null=True
    )

    # Billing Address
    billing_street = models.CharField(
        _("Billing Street"),
        max_length=255,
        blank=True,
        null=True
    )

    billing_address_number = models.CharField(
        _("Billing Address Number"),
        max_length=50,
        blank=True,
        null=True
    )

    billing_postcode = models.CharField(
        _("Billing Postcode"),
        max_length=20,
        blank=True,
        null=True
    )

    billing_city = models.CharField(
        _("Billing City"),
        max_length=100,
        blank=True,
        null=True
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
        verbose_name=_("Organization")
    )

    class Meta:
        verbose_name = _("Company Profile")
        verbose_name_plural = _("Company Profiles")
        db_table = "companies"
        ordering = ("-created_at",)
        unique_together = ('name', 'org')

    def __str__(self):
        return f"{self.name}"

    @property
    def full_billing_address(self):
        """""Returns the full billing address"""""
        address_parts = [
            self.billing_street,
            self.billing_address_number,
            self.billing_city,
            self.billing_postcode,
            self.get_billing_country_display() if self.billing_country else None
        ]
        return ", ".join([part for part in address_parts if part])

    def save(self, *args, **kwargs):
        """Overriding save to automatically update updated_by"""
        if 'updated_by' in kwargs:
            self.updated_by = kwargs.pop('updated_by')
        super(CompanyProfile, self).save(*args, **kwargs)