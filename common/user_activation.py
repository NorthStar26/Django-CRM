from django.urls import path
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils import timezone
import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from common.models import User
from common.token_generator import account_activation_token


class UserActivationView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request, uid, token, activation_key):
        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if (
            user is not None
            and account_activation_token.check_token(user, token)
            and user.activation_key == activation_key
        ):
            # Check if the activation key is still valid (within 2 hours)
            current_time = timezone.now()
            key_time_str = activation_key.replace(token, "")
            try:
                key_time = datetime.datetime.strptime(key_time_str, "%Y-%m-%d-%H-%M-%S")
                key_time = timezone.make_aware(key_time)
                if current_time > key_time:
                    return Response(
                        {"error": True, "errors": "Activation link has expired"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except ValueError:
                return Response(
                    {"error": True, "errors": "Invalid activation link"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Set password from request data
            password = request.data.get("password")
            if not password:
                return Response(
                    {"error": True, "errors": "Password is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(password)
            user.is_active = True
            user.activation_key = ""  # Clear the activation key after use
            user.save()

            return Response(
                {
                    "error": False,
                    "message": "Account activated successfully. You can now login.",
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": True, "errors": "Invalid activation link"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get(self, request, uid, token, activation_key):
        # Just validate the activation link is valid, without setting the password
        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if (
            user is not None
            and account_activation_token.check_token(user, token)
            and user.activation_key == activation_key
        ):
            # Check if the activation key is still valid (within 2 hours)
            current_time = timezone.now()
            key_time_str = activation_key.replace(token, "")
            try:
                key_time = datetime.datetime.strptime(key_time_str, "%Y-%m-%d-%H-%M-%S")
                key_time = timezone.make_aware(key_time)
                if current_time > key_time:
                    return Response(
                        {"error": True, "errors": "Activation link has expired"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except ValueError:
                return Response(
                    {"error": True, "errors": "Invalid activation link"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "error": False,
                    "message": "Activation link is valid",
                    "email": user.email,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": True, "errors": "Invalid activation link"},
                status=status.HTTP_400_BAD_REQUEST,
            )
