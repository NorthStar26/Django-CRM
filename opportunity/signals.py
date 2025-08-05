from django.db.models.signals import post_save
from django.dispatch import receiver
from opportunity.models import Opportunity
from cases.models import Case
from django.utils import timezone

@receiver(post_save, sender=Opportunity)
def create_case_for_lost_opportunity(sender, instance, created, **kwargs):
    # Only create a case if stage is Closed Lost and there is no feedback case yet
    print("Signal fired for Opportunity:", instance.name, "stage:", instance.stage)

    if (
        instance.stage == "CLOSED LOST"  # <-- adjust if your value is different!
        and not hasattr(instance, "lost_feedback_case")
    ):
        print("Opportunity reason at signal:", instance.reason)

        case = Case.objects.create(
            name=f"Lost Opportunity - {instance.name}",
            case_type="Lost Deal",
            priority="Normal",
            status=False,
            opportunity=instance,
            account=instance.account,
            org=instance.org,
            description="Case created from lost opportunity",
            reason=instance.reason or "",
            closed_on=instance.closed_on or timezone.now().date(),
            is_active=True,
        )
        if instance.assigned_to.exists():
            case.assigned_to.set(instance.assigned_to.all())
        if instance.contacts.exists():
            case.contacts.set(instance.contacts.all())
        case.save()