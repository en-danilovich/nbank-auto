from src.main.api.fixtures.user_fixtures import *
from src.main.api.fixtures.api_fixtures import *
from src.main.api.fixtures.object_fixtures import *
from src.main.api.fixtures.setup_hook import *

def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    preferred = "chromium"

    filtered: list[pytest.Item] = []

    for item in items:
        is_ui = bool(item.get_closest_marker("ui"))
        fixts = getattr(item, "fixturenames", ()) or ()

        if (not is_ui) and ("browser_name" in fixts):
            callspec = getattr(item, "callspec", None)
            if callspec is not None and "browser_name" in callspec.params:
                bn = norm_browser_name(callspec.params.get("browser_name"))
                if bn != preferred:
                    continue

        filtered.append(item)

    items[:] = filtered