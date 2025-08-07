from drf_spectacular.utils import OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

organization_header = OpenApiParameter(
    name="org",
    description="Organization ID",
    required=True,
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.HEADER,
    examples=[
        OpenApiExample(
            "Example UUID",
            value="2f551f66-1b1e-4eca-8b10-9a1ba44ea619",
            description="Organization UUID in string format"
        )
    ]
)

cases_list_get_params = [
    organization_header,  
    OpenApiParameter(
        name="search",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Search term to filter cases (searches in case name, contact names, and company industry)"
    ),
    OpenApiParameter(
        name="industry",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Filter by Industry"
    ),
    OpenApiParameter(
        name="contact_name",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Filter by Contact"
    )
]

organization_params = [organization_header]  
