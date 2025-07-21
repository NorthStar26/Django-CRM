from django.urls import path

from opportunity import views

app_name = "api_opportunities"

urlpatterns = [
    path("", views.OpportunityListView.as_view()),
    path("<str:pk>/", views.OpportunityDetailView.as_view()),
    path("<str:pk>/pipeline/", views.OpportunityPipelineView.as_view()),
    path("comment/<str:pk>/", views.OpportunityCommentView.as_view()),


    path("attachment/", views.OpportunityAttachmentView.as_view()),
    path("attachment/<str:pk>/", views.OpportunityAttachmentView.as_view()),

    # Удаление и получение вложений (требуется pk opportunity)
    path("attachment/<str:pk>/<str:attachment_id>/", views.OpportunityAttachmentView.as_view()),
    path("attachment/<str:attachment_id>/", views.OpportunityAttachmentView.as_view()),
    path("<str:pk>/attachment/", views.OpportunityAttachmentView.as_view())
]

