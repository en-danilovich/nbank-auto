import pytest
from playwright.sync_api import Page, expect

from src.tests.ui.base_test import BaseUITest
from src.main.api.models.create_user_request import CreateUserRequest


@pytest.mark.ui
class TestLoginUser(BaseUITest):
    @pytest.mark.usefixtures("admin_user_request")
    def test_admin_can_login_with_correct_data(self, page: Page, admin_user_request: CreateUserRequest):
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(f"{self.UI_BASE_URL}/login", wait_until="domcontentloaded")

        page.get_by_placeholder("Username").fill(admin_user_request.username)
        page.get_by_placeholder("Password").fill(admin_user_request.password)
        page.get_by_role("button", name="Login").click()

        expect(page.get_by_text("Admin Panel")).to_be_visible()

    @pytest.mark.usefixtures("user_request")
    def test_user_can_login_with_correct_data(self, page: Page, user_request: CreateUserRequest):
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(f"{self.UI_BASE_URL}/login", wait_until="domcontentloaded")

        page.get_by_placeholder("Username").fill(user_request.username)
        page.get_by_placeholder("Password").fill(user_request.password)
        page.get_by_role("button").click()

        expect(page.get_by_text("User Dashboard")).to_be_visible()