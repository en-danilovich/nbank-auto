import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.models.create_user_request import CreateUserRequest


@pytest.mark.api
class TestLoginUser:
    @pytest.mark.prepare_users(number=1)
    def test_login_user(self, api_manager: ApiManager, prepared_users):
        user = prepared_users[0]
        api_manager.user_steps.login(user)
        profile = api_manager.user_steps.get_profile(user)
        assert profile.username == user.username

    @pytest.mark.usefixtures('api_manager', 'admin_user_request')
    def test_login_admin_user(self, api_manager: ApiManager, admin_user_request: CreateUserRequest):
        api_manager.user_steps.login(admin_user_request)
        users = api_manager.admin_steps.get_all_users_as(admin_user_request)
        assert isinstance(users, list)
