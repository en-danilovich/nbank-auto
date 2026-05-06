import pytest

from src.main.api.fixtures.user_fixtures import *
from src.main.api.fixtures.api_fixtures import *
from src.main.api.fixtures.object_fixtures import *
from src.main.api.fixtures.setup_hook import *
from src.main.api.fixtures.assertions_fixtures import *
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
        help="Seed for random generators. If not set, a new seed is generated per run (and shared across xdist workers).",
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
        fixts = getattr(item, "fixturenames", ()) or ()

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

@pytest.fixture(autouse=True, scope="function")
def clear_storage():
    SessionStorage.clear()
