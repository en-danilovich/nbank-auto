import allure
import pytest

from src.main.api.fixtures.user_fixtures import *  # noqa: F401,F403
from src.main.api.fixtures.api_fixtures import *  # noqa: F401,F403
from src.main.api.fixtures.object_fixtures import *  # noqa: F401,F403
from src.main.api.fixtures.setup_hook import *  # noqa: F401,F403
from src.main.api.fixtures.assertions_fixtures import *  # noqa: F401,F403
from src.main.api.fixtures.fraud_fixtures import *  # noqa: F401,F403
from src.main.api.fixtures.prepare_data_fixtures import *  # noqa: F401,F403
from src.main.api.classes.session_storage import SessionStorage
from src.main.api.utils.helpers.browsers import norm_browser_name
import os
import time
import random


def _apply_global_seed(seed: int) -> None:
    random.seed(seed)
    try:
        from faker import Faker
        Faker.seed(seed)
    except Exception:
        pass

    try:
        from src.main.api.generators import random_data
        if hasattr(random_data, "faker"):
            random_data.faker.seed_instance(seed)
    except Exception:
        pass


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--seed",
        action="store",
        default=os.getenv("PYTEST_SEED"),
        help=(
            "Seed for random generators. If not set, a new seed is generated per run "
            "(and shared across xdist workers)."
        ),
    )
    parser.addoption(
        "--api-version",
        action="store",
        default=os.getenv("API_VERSION"),
        help=(
            "Backend version under test. Used with @pytest.mark.api_version(...). "
            "Example: --api-version with_database"
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    seed = None
    if hasattr(config, "workerinput"):
        seed = config.workerinput.get("seed")

    if seed is None:
        opt = config.getoption("--seed")
        seed = int(opt) if opt is not None else int(time.time_ns() % 2_000_000_000)

    config._nbank_seed = int(seed)
    _apply_global_seed(int(seed))

    api_version = config.getoption("--api-version")
    if api_version:
        os.environ["API_VERSION"] = str(api_version)


def pytest_configure_node(node) -> None:
    seed = getattr(node.config, "_nbank_seed", None)
    if seed is not None:
        node.workerinput["seed"] = int(seed)


def pytest_collection_finish(session: pytest.Session) -> None:
    config = session.config
    base_seed = getattr(config, "_nbank_seed", None)
    if base_seed is None:
        return

    workerid = None
    if hasattr(config, "workerinput"):
        workerid = config.workerinput.get("workerid")

    if workerid and str(workerid).startswith("gw"):
        try:
            idx = int(str(workerid)[2:])
        except Exception:
            idx = 0
        runtime_seed = int(base_seed) + (idx + 1) * 1_000_000
    else:
        runtime_seed = int(base_seed)

    _apply_global_seed(runtime_seed)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    preferred = "chromium"

    filtered: list[pytest.Item] = []

    for item in items:
        is_ui = bool(item.get_closest_marker("ui"))
        browsers_mark = item.get_closest_marker("browsers")
        api_ver_mark = item.get_closest_marker("api_version")
        fixts = getattr(item, "fixturenames", ()) or ()

        # Backend version filtering: if test is tagged with @api_version("..."),
        # it runs only when --api-version matches. Otherwise, skip it.
        if api_ver_mark:
            expected = str(api_ver_mark.args[0]) if api_ver_mark.args else ""
            actual = str(config.getoption("--api-version") or "")
            if not actual or actual != expected:
                continue

        if browsers_mark:
            allowed = {norm_browser_name(str(x)) for x in (browsers_mark.args or ())}
            callspec = getattr(item, "callspec", None)
            if allowed and callspec is not None and "browser_name" in getattr(callspec, "params", {}):
                current = norm_browser_name(callspec.params.get("browser_name"))
                if current not in allowed:
                    continue

        if (not is_ui) and ("browser_name" in fixts):
            callspec = getattr(item, "callspec", None)
            if callspec is not None and "browser_name" in callspec.params:
                bn = norm_browser_name(callspec.params.get("browser_name"))
                if bn != preferred:
                    continue

        filtered.append(item)

    items[:] = filtered


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("page")
    if page is None:
        return
    try:
        png = page.screenshot(full_page=True)
    except Exception:
        return
    allure.attach(png, name="failure-screenshot", attachment_type=allure.attachment_type.PNG)


@pytest.fixture(autouse=True, scope="function")
def clear_storage():
    SessionStorage.clear()
