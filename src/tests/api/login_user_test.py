import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.models.create_user_request import CreateUserRequest


@pytest.mark.api
class TestLoginUser:
    @pytest.mark.usefixtures('user_request', 'api_manager')
    def test_login_user(self, api_manager: ApiManager, user_request: CreateUserRequest):
        api_manager.user_steps.login(user_request)

    @pytest.mark.usefixtures('api_manager', 'admin_user_request')
    def test_login_admin_user(self, api_manager: ApiManager, admin_user_request: CreateUserRequest):
        api_manager.user_steps.login(admin_user_request)
