import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.models.create_user_request import CreateUserRequest


@pytest.mark.api
class TestCreateAccount:
    @pytest.mark.usefixtures('user_request', 'api_manager')
    @pytest.mark.check_accounts_change(delta=1)
    def test_create_account(self, api_manager: ApiManager, user_request: CreateUserRequest):
        created_account = api_manager.user_steps.create_account(user_request)
        assert created_account.balance == 0
