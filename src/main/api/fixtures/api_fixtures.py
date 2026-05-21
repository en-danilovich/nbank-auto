import pytest

from src.main.api.classes.api_manager import ApiManager


@pytest.fixture
def api_manager(created_objects):
    return ApiManager(created_objects)
