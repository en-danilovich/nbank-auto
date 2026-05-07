import pytest

from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_data import RandomData
from src.main.api.models.comparison.dao_and_model_assertions import DaoAndModelAssertions
from src.main.api.models.create_user_request import CreateUserRequest


@pytest.mark.api
@pytest.mark.api_version("with_database")
class TestCreateUser:
    @pytest.mark.usefixtures('api_manager')
    @pytest.mark.parametrize('create_user_request', [RandomModelGenerator.generate(CreateUserRequest)])
    @pytest.mark.check_all_users_change(delta=1, username_source="create_user_request.username", should_exist=True)
    def test_create_valid_user(self, api_manager: ApiManager, create_user_request: CreateUserRequest):
        create_user_response = api_manager.admin_steps.create_user(create_user_request)

        user_dao = api_manager.database_steps.get_user_by_username(create_user_response.username)
        DaoAndModelAssertions.assert_that(create_user_response, user_dao).match()
    
    @pytest.mark.parametrize(
        argnames='username, password, role, error_key, error_value',
        argvalues=[
            ('', RandomData.get_password(), 'USER', 'username', 'Username cannot be blank'),
            ('ab', RandomData.get_password(), 'USER', 'username', 'Username must be between 3 and 15 characters'),
            ('qwertyuiopqwerty', RandomData.get_password(), 'USER', 'username', 'Username must be between 3 and 15 characters'),
            ('@john_doe', RandomData.get_password(), 'USER', 'username', 'Username must contain only letters, digits, dashes, underscores, and dots'),
        ]
    )
    @pytest.mark.usefixtures('api_manager')
    @pytest.mark.check_all_users_change(delta=0, username_source="username", should_exist=False)
    def test_create_invalid_user(self, api_manager: ApiManager, username: str, password: str, role: str, error_key: str, error_value: str):
        create_user_request = CreateUserRequest(username=username, password=password, role=role)
        api_manager.admin_steps.create_invalid_user(create_user_request, error_key, error_value)

        # DB negative check: invalid create must not write user into customers table.
        user_dao = api_manager.database_steps.find_user_by_username(username)
        assert user_dao is None, f"User '{username}' should NOT exist in DB after invalid create, but was found: {user_dao}"
    