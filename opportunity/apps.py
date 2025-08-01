from django.apps import AppConfig


class OpportunityConfig(AppConfig):
    name = "opportunity"
    def ready(self):
        import opportunity.signals