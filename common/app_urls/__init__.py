from django.urls import include, path

app_name = "common_urls"
urlpatterns = [
    path("", include(("common.urls"))),
    path("accounts/", include("accounts.urls", namespace="api_accounts")),
    path("contacts/", include("contacts.urls", namespace="api_contacts")),
    path("leads/", include("leads.urls", namespace="api_leads")),
    path("opportunities/", include("opportunity.urls", namespace="api_opportunities")),
    path("companies/", include("companies.urls", namespace="api_companies")),
    path("teams/", include("teams.urls", namespace="api_teams")),
    path("tasks/", include("tasks.urls", namespace="api_tasks")),
    path("events/", include("events.urls", namespace="api_events")),
    path("cases/", include("cases.urls", namespace="api_cases")),

    path("emails/", include("emails.urls", namespace="api_emails")),
    #path("invoices/", include("invoices.urls", namespace="api_invoices")),
    #path("planner/", include("planner.urls", namespace="api_planner")),
]

