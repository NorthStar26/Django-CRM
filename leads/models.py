import arrow
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import Org, Profile
from common.base import BaseModel
from common.utils import (
    LEAD_SOURCE,
    LEAD_STATUS,
)
from contacts.models import Contact


class Company(BaseModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    org = models.ForeignKey(Org, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        db_table = "company"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}"

class Lead(BaseModel):
    description = models.TextField(blank=True, null=True)
    link = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    probability = models.IntegerField(default=0, blank=True, null=True)
    status = models.CharField(
        _("Status of Lead"), max_length=255, blank=True, null=True, choices=LEAD_STATUS
    )
    lead_source = models.CharField(
        _("Source of Lead"), max_length=255, blank=True, null=True, choices=LEAD_SOURCE
    )
    notes = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="lead_assigned_user"
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name="lead_contact"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_company",
    )
    organization = models.ForeignKey(
        Org, on_delete=models.SET_NULL, null=True, blank=True, related_name="lead_organization"
    )

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        db_table = "lead"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Lead {self.id}"

    @property
    def created_on_arrow(self):
        return arrow.get(self.created_at).humanize()

    # def save(self, *args, **kwargs):
    #     super(Lead, self).save(*args, **kwargs)
    #     queryset = Lead.objects.all().exclude(status='converted').select_related('created_by'
    #         ).prefetch_related('tags', 'assigned_to',)
    #     open_leads = queryset.exclude(status='closed')
    #     close_leads = queryset.filter(status='closed')
    #     cache.set('admin_leads_open_queryset', open_leads, 60*60)
    #     cache.set('admin_leads_close_queryset', close_leads, 60*60)
