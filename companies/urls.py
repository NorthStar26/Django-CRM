from django.urls import path
from . import views
from companies.dashboard_comp_views import JobTitlesDistributionView

app_name = "api_companies"

urlpatterns = [
    path("", views.CompanyListView.as_view(), name="company_list"),
     path("job-titles/", JobTitlesDistributionView.as_view(), name="job_titles_distribution"),
    path("<str:pk>/", views.CompanyDetailView.as_view(), name="company_detail"),
    path('<str:pk>/logo/', views.CompanyLogoUploadView.as_view(), name='company-logo-upload'),

]