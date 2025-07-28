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

ORG_ID = "b9a47cc9-4dca-4309-a6b0-4d1f1a9dc9f4"  # замените на актуальный id вашей организации
org = Org.objects.get(id=ORG_ID)
profile = Profile.objects.filter(org=org).first()
user = profile.user

company = CompanyProfile.objects.filter(org=org).first()
contact = Contact.objects.filter(org=org).first()

LEAD_STATUSES = ["NEW", "QUALIFIED", "DISQUALIFIED", "RECYCLED"]
OPPORTUNITY_STAGES = [
    "QUALIFICATION",
    "IDENTIFY_DECISION_MAKERS",
    "PROPOSAL",
    "NEGOTIATION",
    "CLOSE",
    "CLOSED WON",
    "CLOSED LOST",
]

# Создание лидов с заполнением только существующих полей
for i in range(50):
    status = random.choice(LEAD_STATUSES)
    lead = Lead.objects.create(
        lead_title=fake.company(),
        description=fake.text(max_nb_chars=100),
        status=status,
        organization=org,
        created_by=user,

        company=company,
        contact=contact,
        notes=fake.sentence(),
        attachment_links=[{"file_name": fake.file_name(), "url": fake.url()}],
        lead_source=random.choice(["EMAIL", "PHONE", "WEBSITE", "SOCIAL", "OTHER"]),
        probability=random.randint(0, 100),
        amount=random.randint(1000, 10000),
        link=fake.url(),
        assigned_to=profile,
    )

    print(f"Created Lead: {lead.lead_title} with status {status}")

# Создание opportunities с заполнением всех ключевых полей pipeline
for i in range(50):
    stage = random.choice(OPPORTUNITY_STAGES)
    opportunity = Opportunity.objects.create(
        name=fake.bs().capitalize(),
        org=org,
        stage=stage,
        expected_revenue=random.randint(1000, 10000),
        created_by=user,


        meeting_date=fake.date_between(start_date='-30d', end_date='+30d') if stage in ["PROPOSAL", "NEGOTIATION", "CLOSE", "CLOSED WON", "CLOSED LOST"] else None,
        feedback=fake.sentence() if stage in ["NEGOTIATION", "CLOSE", "CLOSED WON", "CLOSED LOST"] else "",
        reason=fake.sentence() if stage in ["CLOSE", "CLOSED LOST"] else "",
        attachment_links=[{"file_name": fake.file_name(), "url": fake.url()}] if stage in ["PROPOSAL", "NEGOTIATION", "CLOSE", "CLOSED WON", "CLOSED LOST"] else [],
        contract_attachment=[{"file_name": fake.file_name(extension="pdf"), "url": fake.url()}] if stage in ["CLOSE", "CLOSED WON"] else [],
        is_active=(stage not in ["CLOSED WON", "CLOSED LOST"]),
        probability=100 if stage == "CLOSED WON" else (0 if stage == "CLOSED LOST" else random.randint(10, 90)),
    )
    opportunity.assigned_to.set([profile])
    print(f"Created Opportunity: {opportunity.name} with stage {stage}")