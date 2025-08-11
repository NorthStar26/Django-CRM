from drf_spectacular.utils import OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes
from enum import Enum
from common.utils import COUNTRIES, INDCHOICES


company_list_get_params = [

    OpenApiParameter(
        name="name",
        description="Search companies by name (partial match, case insensitive)",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
    ),

    OpenApiParameter(
        name="billing_country",
        description="Filter by country",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        enum=[choice[0] for choice in COUNTRIES],
    ),


    OpenApiParameter(
        name="industry",
        description="Filter by industry",
        required=False,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        enum=[choice[0] for choice in INDCHOICES],
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