from typing import List
import pytest, re
from playwright.sync_api import Page, Dialog, expect

from src.tests.ui.base_test import BaseUITest
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.create_account_response import CreateAccountResponse
from src.main.api.requests.skeleton.requesters.validated_crud_requester import ValidatedCrudRequester
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs
from src.main.api.requests.skeleton.endpoint import Endpoint


@pytest.mark.ui
class TestCreateAccount(BaseUITest):
    @pytest.mark.usefixtures("user_request")
    def test_user_can_create_account(self, page: Page, user_request: CreateUserRequest):
        page.set_viewport_size({"width": 1920, "height": 1080})

        """
        ШАГИ ПО НАСТРОЙКЕ ОКРУЖЕНИЯ
        ШАГ 1: админ логинится в банке
        ШАГ 2: админ создает юзера
        ШАГ 3: юзер логинится в банке
        """

        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(f"{self.UI_BASE_URL}/login", wait_until="domcontentloaded")

        page.get_by_placeholder("Username").fill(user_request.username)
        page.get_by_placeholder("Password").fill(user_request.password)
        page.get_by_role("button").click()

        expect(page.get_by_text("User Dashboard")).to_be_visible()

        # ШАГИ ТЕСТА
        # ШАГ 4: юзер создает аккаунт
        page.get_by_role("button", name="➕ Create New Account").click()

        # ШАГ 5: проверка, что аккаунт создался на UI
        def handle_create_account_dialog(dialog: Dialog):
            assert "✅ New Account Created! Account Number:" in dialog.message
            pattern = re.compile(r'Account Number: (\w+)')
            matcher = pattern.search(dialog.message)
            matcher.group(1)
            dialog.accept()

        page.on("dialog", lambda dialog: handle_create_account_dialog(dialog))
        
        # ШАГ 6: проверка, что аккаунт был создан на API
        user_accounts: List[CreateAccountResponse] = ValidatedCrudRequester(
            RequestSpecs.auth_as_user(user_request.username, user_request.password),
            Endpoint.GET_CUSTOMER_ACCOUNTS,
            ResponseSpecs.request_returns_ok()
        ).get()

        assert len(user_accounts) == 1
        assert user_accounts[0] and user_accounts[0].balance == 0