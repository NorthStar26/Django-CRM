import re

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from common.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from common.models import (
    Address,
    APISettings,
    Attachments,
    Comment,
    Document,
    Org,
    Profile,
    User,
)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Org
        fields = ("id", "name", "api_key")


class SocialLoginSerializer(serializers.Serializer):
    token = serializers.CharField()


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            "id",
            "comment",
            "commented_on",
            "commented_by",
            "account",
            "lead",
            "opportunity",
            "contact",
            "case",
            "task",
            "invoice",
            "event",
            "profile",
        )


class LeadCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            "id",
            "comment",
            "commented_on",
            "commented_by",
            "lead",
        )


class OrgProfileCreateSerializer(serializers.ModelSerializer):
    """
    It is for creating organization
    """

    name = serializers.CharField(max_length=255)

    class Meta:
        model = Org
        fields = ["name"]
        extra_kwargs = {"name": {"required": True}}

    def validate_name(self, name):
        if bool(re.search(r"[~\!_.@#\$%\^&\*\ \(\)\+{}\":;'/\[\]]", name)):
            raise serializers.ValidationError(
                "organization name should not contain any special characters"
            )
        if Org.objects.filter(name=name).exists():
            raise serializers.ValidationError(
                "Organization already exists with this name"
            )
        return name


class ShowOrganizationListSerializer(serializers.ModelSerializer):
    """
    we are using it for show orjanization list
    """

    org = OrganizationSerializer()

    class Meta:
        model = Profile
        fields = (
            "role",
            "alternate_phone",
            "has_sales_access",
            "has_marketing_access",
            "is_organization_admin",
            "org",
        )


class BillingAddressSerializer(serializers.ModelSerializer):
    country_display = serializers.SerializerMethodField()

    def get_country_display(self, obj):
        return obj.get_country_display()

    class Meta:
        model = Address
        fields = ("address_line", "street", "city", "state", "postcode", "country", "country_display")

    def __init__(self, *args, **kwargs):
        account_view = kwargs.pop("account", False)

        super().__init__(*args, **kwargs)

        if account_view:
            self.fields["address_line"].required = True
            self.fields["street"].required = True
            self.fields["city"].required = True
            self.fields["state"].required = True
            self.fields["postcode"].required = True
            self.fields["country"].required = True


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "profile_pic",
        )

    def __init__(self, *args, **kwargs):
        self.org = kwargs.pop("org", None)
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def validate_email(self, email):
        if self.instance:
            if self.instance.email != email:
                if not Profile.objects.filter(user__email=email, org=self.org).exists():
                    return email
                raise serializers.ValidationError("Email already exists")
            return email
        if not Profile.objects.filter(user__email=email.lower(), org=self.org).exists():
            return email
        raise serializers.ValidationError("Given Email id already exists")

    def create(self, validated_data):
        """
        Override user creation to use UserManager
        """
        # Extract is_active from validated_data
        is_active = validated_data.pop("is_active", False)

        # Use create_user instead of create for automatic generation activation_key
        user = User.objects.create_user(is_active=is_active, **validated_data)
        return user


class CreateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "role",
            "phone",
            "alternate_phone",
            "has_sales_access",
            "has_marketing_access",
            "is_organization_admin",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alternate_phone"].required = False
        self.fields["role"].required = True
        self.fields["phone"].required = True


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "profile_pic"]


class ProfileSerializer(serializers.ModelSerializer):
    address = BillingAddressSerializer(
        read_only=True
    )  # Add this line to serialize address details

    class Meta:
        model = Profile
        fields = (
            "id",
            "user_details",
            "role",
            "address",
            "has_marketing_access",
            "has_sales_access",
            "phone",
            "alternate_phone",
            "date_of_joining",
            "is_active",
        )


class AttachmentsSerializer(serializers.ModelSerializer):
    file_path = serializers.SerializerMethodField()

    def get_file_path(self, obj):
        if obj.attachment:
            return obj.attachment.url
        None

    class Meta:
        model = Attachments
        fields = ["id", "created_by", "file_name", "created_at", "file_path"]


class DocumentSerializer(serializers.ModelSerializer):
    shared_to = ProfileSerializer(read_only=True, many=True)
    teams = serializers.SerializerMethodField()
    created_by = UserSerializer()
    org = OrganizationSerializer()

    def get_teams(self, obj):
        return obj.teams.all().values()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "document_file",
            "status",
            "shared_to",
            "teams",
            "created_at",
            "created_by",
            "org",
        ]


class DocumentCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.fields["title"].required = True
        self.org = request_obj.profile.org

    def validate_title(self, title):
        if self.instance:
            if (
                Document.objects.filter(title__iexact=title, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Document with this Title already exists"
                )
        if Document.objects.filter(title__iexact=title, org=self.org).exists():
            raise serializers.ValidationError("Document with this Title already exists")
        return title

    class Meta:
        model = Document
        fields = ["title", "document_file", "status", "org"]


def find_urls(string):
    # website_regex = "^((http|https)://)?([A-Za-z0-9.-]+\.[A-Za-z]{2,63})?$"  # (http(s)://)google.com or google.com
    # website_regex = "^https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,63})?$"  # (http(s)://)google.com
    # http(s)://google.com
    website_regex = "^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$"
    # http(s)://google.com:8000
    website_regex_port = "^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,63}:[0-9]{2,4}$"
    url = re.findall(website_regex, string)
    url_port = re.findall(website_regex_port, string)
    if url and url[0] != "":
        return url
    return url_port


class APISettingsSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = APISettings
        fields = ("title", "website")

    def validate_website(self, website):
        if website and not (
            website.startswith("http://") or website.startswith("https://")
        ):
            raise serializers.ValidationError("Please provide valid schema")
        if not len(find_urls(website)) > 0:
            raise serializers.ValidationError(
                "Please provide a valid URL with schema and without trailing slash - Example: http://google.com"
            )
        return website


class APISettingsListSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    lead_assigned_to = ProfileSerializer(read_only=True, many=True)
    tags = serializers.SerializerMethodField()
    org = OrganizationSerializer()

    def get_tags(self, obj):
        return obj.tags.all().values()

    class Meta:
        model = APISettings
        fields = [
            "title",
            "apikey",
            "website",
            "created_at",
            "created_by",
            "lead_assigned_to",
            "tags",
            "org",
        ]


class APISettingsSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = APISettings
        fields = [
            "title",
            "website",
            "lead_assigned_to",
            "tags",
        ]


class DocumentCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "title",
            "document_file",
            "teams",
            "shared_to",
        ]


class DocumentEditSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["title", "document_file", "teams", "shared_to", "status"]


class UserCreateSwaggerSerializer(serializers.Serializer):
    """
    It is swagger for creating or updating user
    """

    ROLE_CHOICES = ["ADMIN", "USER"]

    email = serializers.CharField(max_length=1000, required=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, required=True)
    phone = serializers.CharField(max_length=12)
    alternate_phone = serializers.CharField(max_length=12)
    address_line = serializers.CharField(max_length=10000, required=True)
    street = serializers.CharField(max_length=1000)
    city = serializers.CharField(max_length=1000)
    state = serializers.CharField(max_length=1000)
    postcode = serializers.CharField(
        max_length=1000
    )  # Changed from pincode to postcode
    country = serializers.CharField(max_length=1000)


class UserUpdateStatusSwaggerSerializer(serializers.Serializer):
    STATUS_CHOICES = ["Active", "Inactive"]

    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=True)


from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class SetPasswordSerializer(serializers.Serializer):
    """setting a password by email and activation code"""

    email = serializers.EmailField(required=True, help_text="User's email")
    # activation_key = serializers.CharField(
    #     required=True,
    #     help_text="Activation key sent to the user's email"
    # )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="New Password",
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Confirm new password",
    )

    def validate_password(self, value):
        """Checking password strength"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e))
        return value

    def validate(self, attrs):
        """Checking if passwords match and user exists"""
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords don't match"}
            )

        # Checking if a user with such email exists
        email = attrs.get("email")
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email not found"}
            )

        return attrs



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Check the existence of a user with such email
        email = attrs.get("email")
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email not found"}
            )

        # If the user exists, call the standard validation
        try:
            return super().validate(attrs)
        except serializers.ValidationError as e:
            # If the password is incorrect, return a specific error
            if "detail" in e.detail:
                raise serializers.ValidationError({"password": "Invalid password"})
            raise e
        
class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User's email to reset password")

class ResetPasswordConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset"""
    uidb64  = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"}
    )
    
    def validate_password(self, value):
        """Checking password strength"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e))
        return value
        
    def validate(self, attrs):
        """Checking if passwords match"""
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords don't match"}
            )
        return attrs
