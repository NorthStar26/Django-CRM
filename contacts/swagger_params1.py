# from drf_spectacular.types import OpenApiTypes
# from drf_spectacular.utils import OpenApiParameter

# organization_params_in_header = organization_params_in_header = OpenApiParameter(
#     "org", OpenApiTypes.STR, OpenApiParameter.HEADER
# )

# organization_params = [
#     organization_params_in_header,
# ]

# contact_list_get_params = [
#     organization_params_in_header,
#     OpenApiParameter("name", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("city", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("assigned_to", OpenApiTypes.STR,OpenApiParameter.QUERY),
# ]

# contact_create_post_params = [
#     organization_params_in_header,
#     OpenApiParameter(
#         "salutation", OpenApiParameter.QUERY, OpenApiTypes.STR
#     ),
#     OpenApiParameter(
#         "first_name", OpenApiParameter.QUERY, OpenApiTypes.STR
#     ),
#     OpenApiParameter(
#         "last_name", OpenApiParameter.QUERY, OpenApiTypes.STR
#     ),
#     OpenApiParameter(
#         "date_of_birth",
#         OpenApiParameter.QUERY,
#         OpenApiTypes.STR
#     ),
#     OpenApiParameter("organization", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter(
#         "title", OpenApiParameter.QUERY, OpenApiTypes.STR
#     ),
#     OpenApiParameter("primary_email", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("secondary_email", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("mobile_number", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("secondary_number", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("department", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("language", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("do_not_call", OpenApiParameter.QUERY, OpenApiTypes.BOOL),
#     OpenApiParameter(
#         "address_line", OpenApiParameter.QUERY, OpenApiTypes.STR
#     ),
#     OpenApiParameter("street", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("city", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("state", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("pincode", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("country", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("description", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("linked_in_url", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("facebook_url", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("twitter_username", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("teams", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("assigned_to", OpenApiTypes.STR,OpenApiParameter.QUERY),
#     OpenApiParameter("contact_attachment", OpenApiParameter.QUERY, OpenApiTypes.BINARY),
# ]
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