from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from companies.models import CompanyProfile
from contacts.models import SALUTATION_CHOICES, LANGUAGE_CHOICES


organization_params_in_header = OpenApiParameter(
    name="org",
    description="Organization ID",
    required=True,
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.HEADER,
)


organization_params = [
    organization_params_in_header,
]

contact_list_get_params = [
    organization_params_in_header,
    OpenApiParameter(
        name="name",
        description="Search by name",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
    ),
    OpenApiParameter(
        name="email",
        description="Search by email",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
    ),
]


contact_create_post_params = [
    organization_params_in_header,

#    # Salutation - выпадающий список
#     OpenApiParameter(
#         name="salutation",
#         description="Salutation (Mr or Ms)",
#         required=False,
#         type=OpenApiTypes.STR,
#         location=OpenApiParameter.QUERY,
#         enum=[choice[0] fo r choice in SALUTATION_CHOICES],
#     ),

#     # First name - обязательное поле
#     OpenApiParameter(
#         name="first_name",
#         description="First name",
#         required=True,
#         type=OpenApiTypes.STR,
#         location=OpenApiParameter.QUERY,
#     ),

#     # Last name - обязательное поле
#     OpenApiParameter(
#         name="last_name",
#         description="Last name",
#         required=True,
#         type=OpenApiTypes.STR,
#         location=OpenApiParameter.QUERY,
#     ),

#     # Title - опционально
#     OpenApiParameter(
#         name="title",
#         description="Job title",
#         required=False,
#         type=OpenApiTypes.STR,
#         location=OpenApiParameter.QUERY,
#     ),

#     # Primary email - обязательное поле
#     OpenApiParameter(
#         name="primary_email",
#         description="Primary email address",
#         required=True,
#         type=OpenApiTypes.STR,
#         location=OpenApiParameter.QUERY,
#     ),

#     # Mobile number - опционально
#     OpenApiParameter(
#         name="mobile_number",
#         description="Mobile phone number",
#         required=False,
#         type=OpenApiTypes.STR,
#         location=OpenApiParameter.QUERY,
#     ),

#     # Language - выпадающий список
#     OpenApiParameter(
#         name="language",
#         description="Preferred language",
#         required=False,
#         type=OpenApiTypes.STR,
#         location=OpenApiParameter.QUERY,
#         enum=[choice[0] for choice in LANGUAGE_CHOICES],
#     ),

#     # Do not call - checkbox
#     OpenApiParameter(
#         name="do_not_call",
#         description="Do not call flag",
#         required=False,
#         type=OpenApiTypes.BOOL,
#         location=OpenApiParameter.QUERY,
#     ),

#     # Description - текстовое поле
#     OpenApiParameter(
#         name="description",
#         description="Contact description",
#         required=False,
#         type=OpenApiTypes.STR,
#         location=OpenApiParameter.QUERY,
#     ),

#     # Company ID - выпадающий список компаний
#     OpenApiParameter(
#         name="company_id",
#         description="Select company",
#         required=False,
#         type=OpenApiTypes.UUID,
#         location=OpenApiParameter.QUERY,
#     ),
]