import pytest
from playwright.sync_api import Page, expect

from src.main.ui.pages.admin_panel import AdminPanel
from src.main.ui.pages.login_page import LoginPage
from src.main.ui.pages.user_dashboard import UserDashboard
from src.main.api.models.create_user_request import CreateUserRequest


@pytest.mark.ui
@pytest.mark.browsers('webkit')
class TestLoginUser:
    @pytest.mark.usefixtures("admin_user_request")
    def test_admin_can_login_with_correct_data(self, page: Page, admin_user_request: CreateUserRequest):
        admin_page = LoginPage(page).open()\
            .login(admin_user_request.username, admin_user_request.password)\
            .get_page(AdminPanel)

        expect(admin_page.admin_panel_text).to_be_visible()

    @pytest.mark.usefixtures("user_request")
    def test_user_can_login_with_correct_data(self, page: Page, user_request: CreateUserRequest):
        user_dashboard = LoginPage(page).open() \
            .login(user_request.username, user_request.password) \
            .get_page(UserDashboard)

        expect(user_dashboard.dashboard_text).to_be_visible()