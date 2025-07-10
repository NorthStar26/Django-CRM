from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

organization_params_in_header = organization_params_in_header = OpenApiParameter(
    "org", OpenApiTypes.STR, OpenApiParameter.HEADER
)

organization_params = [
    organization_params_in_header,
]

lead_list_get_params = [
    organization_params_in_header,
    OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("lead_source", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter(
        "status",
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        enum=["assigned", "in process", "converted", "recycled", "closed"],
    ),
]

