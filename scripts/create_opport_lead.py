import os
import django
import random
from faker import Faker

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Django-CRM.settings")
django.setup()

from leads.models import Lead
from opportunity.models import Opportunity
from contacts.models import Contact
from companies.models import CompanyProfile
from common.models import Profile, Org

fake = Faker("en_US")

ORG_ID = "b9a47cc9-4dca-4309-a6b0-4d1f1a9dc9f4"
USER_ID = "89033ca1-3738-4953-9c2d-cbddc9d0509e"
org = Org.objects.get(id=ORG_ID)
profile = Profile.objects.filter(org=org).first()
company = CompanyProfile.objects.filter(org=org).first()
contact = Contact.objects.filter(org=org).first()

LEAD_STATUSES = ["new", "qualified", "disqualified", "recycled"]
OPPORTUNITY_STAGES = [
    "PROPOSAL",
    "QUALIFICATION",
    "IDENTIFY_DECISION_MAKERS",
    "NEGOTIATION",
]

# Создание лидов
for i in range(50):
    status = random.choice(LEAD_STATUSES)
    lead = Lead.objects.create(
        lead_title=fake.company(),
        description=fake.text(max_nb_chars=100),
        status=status,
        organization=org,
        company=company,
        contact=contact,
        notes=fake.sentence(),
        attachment_links=[{"file_name": fake.file_name(), "url": fake.url()}],
        lead_source=random.choice([
            "call", "email", "existing customer", "partner",
            "public relations", "compaign", "other"
        ]),
        probability=random.randint(0, 100),
        amount=random.randint(1000, 10000),
        link=fake.url(),
        assigned_to=profile,
    )
    # Обновляем напрямую в базе, чтобы обойти кастомный save()
    Lead.objects.filter(id=lead.id).update(created_by_id=USER_ID, updated_by_id=USER_ID)
    print(f"Created Lead: {lead.lead_title} with status {status}")

# Создание opportunities
for i in range(50):
    stage = random.choice(OPPORTUNITY_STAGES)
    opportunity = Opportunity.objects.create(
        name=fake.bs().capitalize(),
        org=org,
        stage=stage,
        expected_revenue=random.randint(1000, 10000),
        expected_close_date=fake.date_between(start_date='+10d', end_date='+90d'),
        meeting_date=fake.date_between(start_date='-30d', end_date='+30d') if stage in ["PROPOSAL", "NEGOTIATION"] else None,
        feedback=fake.sentence() if stage in ["NEGOTIATION"] else "",
        reason=fake.sentence() if stage in [] else "",
        attachment_links=[{"file_name": fake.file_name(), "url": fake.url()}] if stage in ["PROPOSAL", "NEGOTIATION"] else [],
        contract_attachment=[],
        is_active=True,
        probability=random.randint(10, 90),
    )
    Opportunity.objects.filter(id=opportunity.id).update(created_by_id=USER_ID, updated_by_id=USER_ID)
    opportunity.assigned_to.set([profile])
    print(f"Created Opportunity: {opportunity.name} with stage {stage}")