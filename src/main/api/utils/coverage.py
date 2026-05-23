from swagger_coverage_tool import SwaggerCoverageTracker

from src.main.api.configs.config import Config


SERVICE_KEY = "nbank"


_tracker: SwaggerCoverageTracker | None = None


def get_tracker() -> SwaggerCoverageTracker:
    global _tracker
    if _tracker is None:
        _tracker = SwaggerCoverageTracker(service=SERVICE_KEY)
    return _tracker


def coverage_path_for(endpoint, id_in_path: bool = False) -> str:
    """
    Build the swagger-relative path template (e.g. ``/api/v1/admin/users/{id}``)
    for a given Endpoint enum value: prefix the endpoint URL with the API
    version, appending ``/{id}`` when the caller used an id (DELETE/GET/PUT by id).
    """
    api_version = Config.get("SERVER_API_VERSION", "")
    path = endpoint.value.url
    if id_in_path:
        path = f"{path}/{{id}}"
    return f"{api_version}{path}"
