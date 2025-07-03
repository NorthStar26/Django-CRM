from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes


company_list_get_params = [
    OpenApiParameter(
        name="name",
        description="Filter by company name",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
    ),
    OpenApiParameter(
        name="email",
        description="Filter by company email",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
    ),
]

company_auth_headers = [
    OpenApiParameter(
        name="org",
        description="Organization ID",
        required=True,
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.HEADER,
    ),
]