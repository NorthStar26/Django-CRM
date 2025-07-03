from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    path("", views.CompanyListView.as_view(), name="company_list"),
    path("<str:pk>/", views.CompanyDetailView.as_view(), name="company_detail"),
]