import logging
from typing import Any, List
import pytest

from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.create_user_response import CreateUserResponse
from src.main.api.models.customer.update_customer_profile_request import UpdateCustomerProfileRequest
from src.main.api.classes.api_manager import ApiManager


@pytest.fixture
def update_customer_profile_request() -> UpdateCustomerProfileRequest:
    return RandomModelGenerator.generate(UpdateCustomerProfileRequest)


@pytest.fixture
def created_objects():
    objects: List[Any] = []
    yield objects

    cleanup_objects(objects)


def cleanup_objects(objects: List[Any]):
    api_manager = ApiManager(objects)
    for obj in objects:
        if isinstance(obj, CreateUserResponse):
            api_manager.admin_steps.delete_user(obj.id)
        elif isinstance(obj, CreateUserRequest):
            try:
                profile = api_manager.user_steps.get_profile(obj)
            except Exception as e:
                logging.warning(f"Skip cleanup for user '{getattr(obj, 'username', obj)}': {e}")
                continue
            api_manager.admin_steps.delete_user(profile.id)
        else:
            logging.warning(f'Object type: {type(obj)} is not deleted')