from django.db.models.signals import post_save
from django.dispatch import receiver
from opportunity.models import Opportunity
from cases.models import Case

@receiver(post_save, sender=Opportunity)
def create_case_for_lost_opportunity(sender, instance, created, **kwargs):
    # Only act if result is False (lost) and there is no feedback case yet
    if instance.result is False and not hasattr(instance, "lost_feedback_case"):
        case = Case.objects.create(
            name=f"Lost Opportunity - {instance.name}",
            case_type="Lost Deal",  # Updated to match acceptance criteria
            status=True,            # True = Open (adjust if you use a status field/choice)
            opportunity=instance,
            account=instance.account,
            org=instance.org,
            description=instance.reason or "",
            closed_on=instance.closed_on,
            is_active=True,         # Mark as active/open
        )
        # Assign users (Opportunity owner)
        if instance.assigned_to.exists():
            case.assigned_to.set(instance.assigned_to.all())
        # Link contacts
        if instance.contacts.exists():
            case.contacts.set(instance.contacts.all())
        case.save()