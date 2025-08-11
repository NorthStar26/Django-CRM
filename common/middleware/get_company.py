# import jwt
# from django.conf import settings
# from django.contrib.auth import logout
# from django.core.exceptions import ValidationError,PermissionDenied
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.exceptions import AuthenticationFailed
# from crum import get_current_user
# from django.utils.functional import SimpleLazyObject

# from common.models import Org, Profile, User


# # def set_profile_request(request, org, token):
# #     # we are decoding the token
# #     decoded = jwt.decode(token, (settings.SECRET_KEY), algorithms=[settings.JWT_ALGO])

# #     request.user = User.objects.get(id=decoded["user_id"])

# #     if request.user:
# #         request.profile = Profile.objects.get(
# #             user=request.user, org=org, is_active=True
# #         )
# #         request.profile.role = "ADMIN"
# #         request.profile.save()
# #         if request.profile is None:
# #             logout(request)
# #             return Response(
# #                 {"error": False},
# #                 status=status.HTTP_200_OK,
#             # )

# def get_actual_value(request):
#     if request.user is None:
#         return None

#     return request.user #here should have value, so any code using request.user will work

# class GetProfileAndOrg(object):
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         self.process_request(request)
#         return self.get_response(request)

#     def process_request(self, request):
#         try :
#             request.profile = None
#             user_id = None
#             # here I am getting the the jwt token passing in header
#             if request.headers.get("Authorization"):
#                 token1 = request.headers.get("Authorization")
#                 token = token1.split(" ")[1]  # getting the token value
#                 decoded = jwt.decode(token, (settings.SECRET_KEY), algorithms=[settings.JWT_ALGO])
#                 user_id = decoded['user_id']
#             api_key = request.headers.get('Token')  # Get API key from request query params
#             if api_key:
#                 try:
#                     organization = Org.objects.get(api_key=api_key)
#                     api_key_user = organization
#                     request.META['org'] = api_key_user.id
#                     profile = Profile.objects.filter(org=api_key_user, role="ADMIN").first()
#                     user_id = profile.user.id
#                 except Org.DoesNotExist:
#                     raise AuthenticationFailed('Invalid API Key')
#             if user_id is not None:
#                 if request.headers.get("org"):
#                     profile = Profile.objects.get(
#                         user_id=user_id, org=request.headers.get("org"), is_active=True
#                     )
#                     if profile:
#                         request.profile = profile
#         except :
#              print('test1')
#              raise PermissionDenied()
import jwt
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from common.models import Org, Profile
import logging

logger = logging.getLogger(__name__)

class GetProfileAndOrg:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):
        # ✅ Обновленный список URL для пропуска
        skip_urls = [
            '/admin/', '/api/auth/', '/api/docs/', '/api/schema/',
            '/static/', '/media/', '/favicon.ico',
            '/api/org/',
            '/api/accounts/',   ]

        # Особая обработка для /api/profile/ - нужно установить profile, но не требовать org
        profile_needs_auth = ['/api/profile/']
        is_profile_endpoint = any(request.path.startswith(url) for url in profile_needs_auth)

        if any(request.path.startswith(url) for url in skip_urls):
            logger.info(f"⏭️ SKIPPING: {request.path}")
            return None

        logger.info(f"🔍 PROCESSING: {request.method} {request.path}")

        try:
            request.profile = None
            user_id = None

            #JWT token from Authorization header
            if request.headers.get("Authorization"):
                token1 = request.headers.get("Authorization")
                if not token1.startswith("Bearer "):
                    logger.error("Invalid token format - missing Bearer prefix")
                    return JsonResponse(
                        {"error": True, "message": "Invalid token format"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                token = token1.split(" ")[1]

                # Проверяем структуру токена
                if len(token.split('.')) != 3:
                    logger.error(f"Invalid token structure: {len(token.split('.'))} parts")
                    return JsonResponse(
                        {"error": True, "message": "Invalid token structure"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                try:
                    # Use settings.JWT_ALGO (which is equal to "HS256")
                    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])
                    user_id = decoded.get('user_id')
                    logger.info(f"✅ Token decoded successfully for user_id: {user_id}")
                except jwt.ExpiredSignatureError:
                    logger.error("❌ Token expired")
                    return JsonResponse(
                        {"error": True, "message": "Token expired"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                except jwt.InvalidTokenError as e:
                    logger.error(f"❌ Invalid token: {str(e)}")
                    return JsonResponse(
                        {"error": True, "message": "Invalid token"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                except Exception as e:
                    logger.error(f"❌ Token decode error: {str(e)}")
                    return JsonResponse(
                        {"error": True, "message": "Token decode error"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

          # API key alternative authentication
            api_key = request.headers.get('Token')
            if api_key:
                try:
                    organization = Org.objects.get(api_key=api_key)
                    request.META['org'] = str(organization.id)
                    profile = Profile.objects.filter(org=organization, role="ADMIN").first()
                    if profile:
                        user_id = profile.user.id
                        logger.info(f"✅ API key auth successful for user: {profile.user.email}")
                except Org.DoesNotExist:
                    logger.error(f"❌ Invalid API key: {api_key}")
                    return JsonResponse(
                        {"error": True, "message": "Invalid API Key"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

# Check that there is authentication
            if not request.headers.get("Authorization") and not api_key:
                logger.warning("❌ No authentication provided")
                return JsonResponse(
                    {"error": True, "message": "No authentication provided"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
# Getting profile by user_id and org
            if user_id and request.headers.get("org"):
                org_id = request.headers.get("org")
                logger.info(f"🔍 Looking for profile: user_id={user_id}, org={org_id}")

                try:
                    profile = Profile.objects.select_related('user', 'org').get(
                        user_id=user_id,
                        org=org_id,
                        is_active=True
                    )
                    request.profile = profile
                    logger.info(f"✅ Profile set: {profile.user.email} - {profile.org.name}")

                except Profile.DoesNotExist:
                    logger.error(f"❌ Profile not found for user {user_id} in org {org_id}")

                    try:
                        user_profiles = Profile.objects.filter(user_id=user_id, is_active=True)
                        logger.info(f"📊 Found {user_profiles.count()} active profiles for user {user_id}")

                        if user_profiles.exists():
                            logger.info("📋 Available organizations for user:")
                            for p in user_profiles:
                                logger.info(f"  - {p.org.name} (ID: {p.org.id})")
                    except Exception as debug_e:
                        logger.error(f"Debug query failed: {str(debug_e)}")

                    return JsonResponse(
                        {"error": True, "message": "Profile not found or user not in organization"},
                        status=status.HTTP_404_NOT_FOUND
                    )

            elif user_id and not request.headers.get("org"):
              # For /api/profile/ we allow working without org - we just take the first active profile
                if is_profile_endpoint:
                    try:
                        profile = Profile.objects.select_related('user', 'org').filter(
                            user_id=user_id,
                            is_active=True
                        ).first()
                        if profile:
                            request.profile = profile
                            logger.info(f"✅ Profile set for profile endpoint: {profile.user.email} - {profile.org.name}")
                        else:
                            logger.error(f"❌ No active profile found for user {user_id}")
                            return JsonResponse(
                                {"error": True, "message": "No active profile found"},
                                status=status.HTTP_404_NOT_FOUND
                            )
                    except Exception as e:
                        logger.error(f"❌ Error getting profile for user {user_id}: {str(e)}")
                        return JsonResponse(
                            {"error": True, "message": "Error getting profile"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                else:
                    logger.error("❌ No organization header provided")
                    return JsonResponse(
                        {"error": True, "message": "Organization header required"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        except Exception as e:
            logger.error(f"❌ Unexpected middleware error: {str(e)}")
            import traceback
            logger.error(f"TRACEBACK: {traceback.format_exc()}")
            return JsonResponse(
                {"error": True, "message": "Authentication error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info("✅ Middleware processing completed successfully")
        return None