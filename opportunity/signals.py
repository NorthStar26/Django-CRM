from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from opportunity.models import Opportunity
from cases.models import Case
from accounts.models import Account
from companies.models import CompanyProfile
from django.utils import timezone


@receiver(pre_save, sender=Opportunity)
def handle_opportunity_closed_won(sender, instance, **kwargs):
    """
    Handle automatic Account creation/linking when Opportunity is marked as Closed Won
    """
    # Check if this is an update (not a new creation)
    if instance.pk:
        try:
            # Get the previous state of the opportunity
            old_instance = Opportunity.objects.get(pk=instance.pk)

            # Check if status changed to "CLOSED WON"
            if old_instance.stage != "CLOSED WON" and instance.stage == "CLOSED WON":
                # Try to find a company through lead first, then through existing account
                company = None
                if (
                    hasattr(instance, "lead")
                    and instance.lead
                    and hasattr(instance.lead, "company")
                ):
                    company = instance.lead.company
                elif (
                    instance.account
                    and hasattr(instance.account, "company")
                    and instance.account.company
                ):
                    company = instance.account.company

                if company:
                    # Check if the company already has an account
                    existing_account = company.account

                    if existing_account:
                        # Link opportunity to existing account
                        instance.account = existing_account
                        # Update the account's updated_at and updated_by
                        existing_account.updated_at = timezone.now()
                        if hasattr(instance, "_current_user"):
                            existing_account.updated_by = instance._current_user
                        existing_account.save()
                    else:
                        # Create new account for the company
                        new_account = Account.objects.create(
                            name=f"Account - {company.name}",
                            email=company.email,
                            phone=company.phone,
                            industry=company.industry,
                            website=company.website,
                            billing_address_line=company.billing_street,
                            billing_city=company.billing_city,
                            billing_state=company.billing_state,
                            billing_postcode=company.billing_postcode,
                            billing_country=company.billing_country,
                            company=company,
                            contact_name=company.name,  # Default to company name
                            is_active=True,
                            org=instance.org,
                            created_at=timezone.now(),
                            updated_at=timezone.now(),
                            created_by=getattr(instance, "_current_user", None),
                            updated_by=getattr(instance, "_current_user", None),
                        )

                        # Link opportunity to new account
                        instance.account = new_account

                        # Update company with account reference
                        company.account = new_account
                        company.save()

        except Opportunity.DoesNotExist:
            pass


@receiver(post_save, sender=Opportunity)
def create_case_for_lost_opportunity(sender, instance, created, **kwargs):
    # Only create a case if stage is Closed Lost and there is no feedback case yet
    if (
        instance.stage == "CLOSED LOST"  # <-- adjust if your value is different!
        and not hasattr(instance, "lost_feedback_case")
    ):
        case = Case.objects.create(
            name=f"Lost Opportunity - {instance.name}",
            case_type="Lost Deal",
            priority="Normal",
            status=False,
            opportunity=instance,
            account=instance.account,
            org=instance.org,
            description=instance.reason or "",
            closed_on=instance.closed_on or timezone.now().date(),
            is_active=True,
        )
        if instance.assigned_to.exists():
            case.assigned_to.set(instance.assigned_to.all())
        if instance.contacts.exists():
            case.contacts.set(instance.contacts.all())
        case.save()
