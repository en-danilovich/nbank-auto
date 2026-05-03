import pytest
from playwright.sync_api import Page

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.ui.pages.bank_alert import BankAlert
from src.main.ui.pages.user_dashboard import UserDashboard
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.customer.update_customer_profile_request import UpdateCustomerProfileRequest

@pytest.mark.ui
class TestUpdateCustomerProfile:
    @pytest.mark.user_session(10)
    def test_update_customer_profile(self, page: Page, api_manager: ApiManager, user_request: CreateUserRequest):
        default_name = "Noname"
        new_name = RandomModelGenerator.generate(UpdateCustomerProfileRequest).name

        UserDashboard(page).open()\
            .verify_welcome_text(default_name)\
            .verify_header_username(default_name)\
            .click_username_in_header()\
            .verify_page_is_visible()\
            .enter_name(new_name)\
            .check_alert_message_and_accept(BankAlert.PROFILE_UPDATED_SUCCESSFULLY)\
            .click_save()\
            .verify_header_username(new_name)\
            .click_home()\
            .verify_welcome_text(new_name)

        profile = api_manager.user_steps.get_profile(user_request)
        assert profile.name == new_name

    @pytest.mark.user_session(10)
    @pytest.mark.parametrize('invalid_name, alert_msg', [
        ("", BankAlert.ENTER_VALID_NAME),
        ("John", [BankAlert.ENTER_VALID_NAME, BankAlert.NAME_MUST_CONTAIN_TWO_WORDS]),
        ("John123 Smith", [BankAlert.ENTER_VALID_NAME, BankAlert.NAME_MUST_CONTAIN_TWO_WORDS]),
        ("John@ Smith", [BankAlert.ENTER_VALID_NAME, BankAlert.NAME_MUST_CONTAIN_TWO_WORDS]),
        ("John Michael Smith", [BankAlert.ENTER_VALID_NAME, BankAlert.NAME_MUST_CONTAIN_TWO_WORDS]),
    ])
    def test_update_customer_profile_invalid_name(self, page: Page, api_manager: ApiManager,
                                                  user_request: CreateUserRequest,
                                                  invalid_name: str, alert_msg: str | list[str]):
        UserDashboard(page).open()\
            .click_username_in_header()\
            .verify_page_is_visible()\
            .enter_name(invalid_name)\
            .check_alert_message_and_accept(alert_msg)\
            .click_save()

        profile = api_manager.user_steps.get_profile(user_request)
        assert profile.name is None