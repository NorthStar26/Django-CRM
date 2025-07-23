from django.urls import path
from . import views

app_name = "api_companies"

urlpatterns = [
    path("", views.CompanyListView.as_view(), name="company_list"),
    path("<str:pk>/", views.CompanyDetailView.as_view(), name="company_detail"),
    path('<str:pk>/logo/', views.CompanyLogoUploadView.as_view(), name='company-logo-upload'),

]