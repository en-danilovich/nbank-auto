import pytest
from playwright.sync_api import Page, expect

from src.main.api.generators.random_data import RandomData
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.classes.api_manager import ApiManager
from src.main.api.models.comparison.model_assertions import ModelAssertions
from src.main.api.models.role import Role
from src.main.ui.pages.admin_panel import AdminPanel
from src.main.ui.pages.bank_alert import BankAlert


@pytest.mark.ui
class TestCreateUser:
    @pytest.mark.admin_session
    @pytest.mark.usefixtures('api_manager')
    @pytest.mark.parametrize('new_user_request', [RandomModelGenerator.generate(CreateUserRequest)])
    def test_admin_can_create_user(self, page: Page, api_manager: ApiManager, new_user_request: CreateUserRequest):
        api_manager.admin_steps.created_objects.append(new_user_request)

        admin_page = AdminPanel(page).open()\
            .create_user(new_user_request.username, new_user_request.password)\
            .check_alert_message_and_accept(BankAlert.USER_CREATED_SUCCESSFULLY)\
            .wait_for_username(new_user_request.username)

        assert any(u.username == new_user_request.username for u in admin_page.get_all_users())

        created_user = next(
            u for u in api_manager.admin_steps.get_all_users()
            if u.username == new_user_request.username
        )
        ModelAssertions(created_user, new_user_request).match()

    @pytest.mark.admin_session
    @pytest.mark.usefixtures('api_manager')
    @pytest.mark.parametrize('new_user_request',
                             [CreateUserRequest(username=RandomData.get_username(1), password=RandomData.get_password(), role=Role.USER)])
    def test_admin_cannot_create_user_with_invalid_data(self, page: Page, api_manager: ApiManager, new_user_request: CreateUserRequest):
        admin_page = AdminPanel(page).open() \
            .create_user(new_user_request.username, new_user_request.password) \
            .check_alert_message_and_accept(BankAlert.USERNAME_MUST_BE_BETWEEN_3_AND_15_CHARACTERS)
        expect(admin_page.admin_panel_text).to_be_visible()

        assert not any(u.username == new_user_request.username for u in admin_page.get_all_users())
        assert not any(u.username == new_user_request.username for u in api_manager.admin_steps.get_all_users())
