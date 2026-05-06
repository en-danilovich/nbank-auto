from typing import List

import pytest
from playwright.sync_api import Page

from src.main.api.classes.session_storage import SessionStorage
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.utils.helpers.browsers import norm_browser_name
from src.main.ui.pages.login_page import LoginPage


@pytest.fixture(scope="function")
def user_session_extension(request: pytest.FixtureRequest, page: Page, user_factory):
    mark = request.node.get_closest_marker("user_session")
    if not mark:
        yield
        return

    count: int = max(int(mark.args[0]), 1)
    auth_index: int = int(mark.kwargs.get("auth", 0))

    users: List[CreateUserRequest] = [user_factory() for _ in range(count)]
    SessionStorage.add_users(users)
    LoginPage(page).auth_as_user(users[auth_index])

    yield

    SessionStorage.clear()

@pytest.fixture()
def admin_session_autologin(request: pytest.FixtureRequest, page: Page, admin_user_request: CreateUserRequest):
    mark = request.node.get_closest_marker("admin_session")
    if not mark:
        return

    LoginPage(page).auth_as_user(admin_user_request)

@pytest.fixture()
def browser_match_guard(request):
    mark = request.node.get_closest_marker("browsers")
    if not mark:
        return

    allowed = {norm_browser_name(str(x)) for x in (mark.args or ())}
    if not allowed:
        return

    try:
        current = request.getfixturevalue("browser_name")
    except Exception:
        return

    if norm_browser_name(str(current)) not in allowed:
        pytest.skip(f"Пропущен: текущий браузер '{current}' не в {sorted(allowed)}")