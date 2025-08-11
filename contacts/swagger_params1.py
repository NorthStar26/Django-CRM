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
    OpenApiParameter(
        name="company",
        description="Filter by company ID",
        required=False,
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
    ),
    OpenApiParameter(
        name="company_name",
        description="Filter by company name",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
    ),
    OpenApiParameter(
        name="department",
        description="Filter by department",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
    ),


    OpenApiParameter(
        name="sort_by",
        description="Field to sort by (e.g. department, first_name, last_name)",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY
    ),
    OpenApiParameter(
        name="sort_order",
        description="Sort order: asc or desc",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY
    ),

]


contact_create_post_params = [
    organization_params_in_header,

]