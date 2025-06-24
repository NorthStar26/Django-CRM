from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from common.views import CustomTokenObtainPairView, ResetPasswordRequestView, ResetPasswordConfirmView
from common import views

app_name = "api_common"


urlpatterns = [
    path("dashboard/", views.ApiHomeView.as_view()),
    path(
        "auth/refresh-token/",
        jwt_views.TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    # GoogleLoginView
    #path("auth/login/", jwt_views.TokenObtainPairView.as_view(), name="token_obtain_pair"),  # autenticate with username and password
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/logout/", jwt_views.TokenBlacklistView.as_view(), name="token_blacklist"),
    path("auth/google/", views.GoogleLoginView.as_view()),
    path("auth/set-password/", views.SetPasswordView.as_view(), name="set_password"),
    path("auth/password-reset/", ResetPasswordRequestView.as_view(), name="password_reset"),
    path("auth/password-reset-confirm/", ResetPasswordConfirmView.as_view(), name="password_reset_confirm"),

    path("org/", views.OrgProfileCreateView.as_view()),
    path("profile/", views.ProfileView.as_view()),
    path("users/get-teams-and-users/", views.GetTeamsAndUsersView.as_view()),
    path("users/", views.UsersListView.as_view()),
    path("user/<str:pk>/", views.UserDetailView.as_view()),
    path("documents/", views.DocumentListView.as_view()),
    path("documents/<str:pk>/", views.DocumentDetailView.as_view()),
    path("api-settings/", views.DomainList.as_view()),
    path("api-settings/<str:pk>/", views.DomainDetailView.as_view()),
    path("user/<str:pk>/status/", views.UserStatusView.as_view()),
]
