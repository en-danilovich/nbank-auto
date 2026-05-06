import pytest
from playwright.sync_api import Page

from src.main.api.classes.api_manager import ApiManager
from src.main.ui.pages.bank_alert import BankAlert
from src.main.ui.pages.user_dashboard import UserDashboard
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.customer.update_customer_profile_request import UpdateCustomerProfileRequest

@pytest.mark.ui
@pytest.mark.usefixtures("user_session_extension", "browser_match_guard")
class TestUpdateCustomerProfile:
    DEFAULT_NAME = "Noname"

    @pytest.mark.user_session(10)
    @pytest.mark.check_profile_name(expected_source="update_customer_profile_request.name")
    def test_update_customer_profile(self, page: Page, api_manager: ApiManager, user_request: CreateUserRequest,
                                     update_customer_profile_request: UpdateCustomerProfileRequest):
        UserDashboard(page).open()\
            .verify_welcome_text(self.DEFAULT_NAME)\
            .verify_header_username(self.DEFAULT_NAME)\
            .click_username_in_header()\
            .verify_page_is_visible()\
            .enter_name(update_customer_profile_request.name)\
            .check_alert_message_and_accept(BankAlert.PROFILE_UPDATED_SUCCESSFULLY)\
            .click_save()\
            .verify_header_username(update_customer_profile_request.name)\
            .click_home()\
            .verify_welcome_text(update_customer_profile_request.name)

    @pytest.mark.user_session(10)
    @pytest.mark.check_profile_name()
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
            .verify_welcome_text(self.DEFAULT_NAME)\
            .verify_header_username(self.DEFAULT_NAME)\
            .click_username_in_header()\
            .verify_page_is_visible()\
            .enter_name(invalid_name)\
            .check_alert_message_and_accept(alert_msg)\
            .click_save()\
            .verify_header_username(self.DEFAULT_NAME)\
            .click_home()\
            .verify_welcome_text(self.DEFAULT_NAME)