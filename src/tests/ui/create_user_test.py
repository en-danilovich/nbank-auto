import re
import pytest
from playwright.sync_api import Page, expect, Dialog

from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.classes.api_manager import ApiManager
from src.main.api.models.comparison.model_assertions import ModelAssertions
from src.tests.ui.base_test import BaseUITest


@pytest.mark.ui
class TestCreateUser(BaseUITest):
    def test_admin_can_create_user(self, page: Page, admin_user_request: CreateUserRequest, api_manager: ApiManager):
        page.set_viewport_size({"width": 1920, "height": 1080})

        # ШАГ 1: админ залогинился в банке
        page.goto(f"{self.UI_BASE_URL}/login", wait_until="domcontentloaded")
        page.get_by_placeholder("Username").fill(admin_user_request.username)
        page.get_by_placeholder("Password").fill(admin_user_request.password)
        page.get_by_role("button", name="Login").click()
        expect(page.get_by_text("Admin Panel")).to_be_visible()

        # ШАГ 2: админ создает юзера в банке
        new_user_request: CreateUserRequest = RandomModelGenerator.generate(CreateUserRequest)
        page.get_by_placeholder("Username").fill(new_user_request.username)
        page.get_by_placeholder("Password").fill(new_user_request.password)
        page.get_by_role("button", name="Add User").click()

        # ШАГ 3: проверяем текст алерта
        def handle_create_user_dialog(dialog: Dialog):
            assert dialog.message == "✅ User created successfully!" 
            dialog.accept()

        page.on("dialog", lambda dialog: handle_create_user_dialog(dialog))

        # ШАГ 4: проверяем, что пользователь есть на UI
        items = page.locator("xpath=//*[text()='All Users']/..//li")
        target = items.filter(has_text=re.compile(rf"^{re.escape(new_user_request.username)}(\s+|.*)USER$", re.IGNORECASE))
        expect(target).to_be_visible()

        # ШАГ 5: проверка, что юзер создан на API
        users = api_manager.admin_steps.get_all_users()
        created = [u for u in users if u.username == new_user_request.username]
        assert len(created) == 1, "Ожидался ровно один созданный пользователь в API"
        ModelAssertions(created[0], new_user_request).match()

    def test_admin_cannot_create_user_with_invalid_data(self, page: Page, admin_user_request: CreateUserRequest, api_manager: ApiManager):
        # ШАГ 1: админ залогинился в банке
        page.goto(f"{self.UI_BASE_URL}/login", wait_until="domcontentloaded")
        page.get_by_placeholder("Username").fill(admin_user_request.username)
        page.get_by_placeholder("Password").fill(admin_user_request.password)
        page.get_by_role("button", name="Login").click()
        expect(page.get_by_text("Admin Panel")).to_be_visible()

        # ШАГ 2: создание пользователя c невалидным username
        new_user_request: CreateUserRequest = RandomModelGenerator.generate(CreateUserRequest)
        new_user_request.username = "a"
        page.get_by_placeholder("Username").fill(new_user_request.username)
        page.get_by_placeholder("Password").fill(new_user_request.password)
        page.get_by_role("button", name="Add User").click()

        # ШАГ 3: проверка текста алерта (contains)
        def handle_create_invalid_user_dialog(dialog: Dialog):
            assert "Username must be between 3 and 15 characters" in dialog.message
            dialog.accept()
        
        page.on("dialog", lambda dialog: handle_create_invalid_user_dialog(dialog))

        # ШАГ 4: на UI пользователя быть не должно
        items = page.locator("xpath=//*[text()='All Users']/..//li")
        target = items.filter(
            has_text=re.compile(rf"^{re.escape(new_user_request.username)}\s+USER$", re.IGNORECASE)
        )
        expect(target).to_have_count(0)

        # ШАГ 5: и в API не должно быть такого пользователя
        users = api_manager.admin_steps.get_all_users()
        assert not any(u.username == new_user_request.username for u in users)
