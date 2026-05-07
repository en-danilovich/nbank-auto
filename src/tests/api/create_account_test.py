import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.models.comparison.dao_and_model_assertions import DaoAndModelAssertions
from src.main.api.models.create_user_request import CreateUserRequest


@pytest.mark.api
@pytest.mark.api_version("with_database")
class TestCreateAccount:
    @pytest.mark.usefixtures('user_request', 'api_manager')
    @pytest.mark.check_accounts_change(delta=1)
    def test_create_account(self, api_manager: ApiManager, user_request: CreateUserRequest):
        created_account = api_manager.user_steps.create_account(user_request)
        assert created_account.balance == 0

        account_dao = api_manager.database_steps.get_account_by_account_number(created_account.accountNumber)
        DaoAndModelAssertions.assert_that(created_account, account_dao).match()
