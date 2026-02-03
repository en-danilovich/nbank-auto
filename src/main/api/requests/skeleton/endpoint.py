from dataclasses import dataclass
from enum import Enum
from typing import List

from src.main.api.models.accounts.account_deposit_request import AccountDepositRequest
from src.main.api.models.accounts.account_deposit_response import AccountDepositResponse
from src.main.api.models.accounts.account_transfer_request import AccountTransferRequest
from src.main.api.models.accounts.account_transfer_response import AccountTransferResponse
from src.main.api.models.create_account_response import CreateAccountResponse
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.create_user_response import CreateUserResponse
from src.main.api.models.customer.get_customer_profile_response import GetCustomerProfileResponse
from src.main.api.models.customer.update_customer_profile_request import UpdateCustomerProfileRequest
from src.main.api.models.customer.update_customer_profile_response import UpdateCustomerProfileResponse
from src.main.api.models.login_user_request import LoginUserRequest
from src.main.api.models.login_user_response import LoginUserResponse
from src.main.api.models.base_model import BaseModel


@dataclass(frozen=True)
class EndpointConfig:
    url: str
    request_model: BaseModel
    response_model: BaseModel


class Endpoint(Enum):
    ADMIN_CREATE_USER = EndpointConfig(
        url='/admin/users',
        request_model=CreateUserRequest,
        response_model=CreateUserResponse
    )
    
    ADMIN_DELETE_USER = EndpointConfig(
        url='/admin/users',
        request_model=None,
        response_model=None
    )
    
    ADMIN_GET_ALL_USERS = EndpointConfig(
        url='/admin/users',
        request_model=None,
        response_model=List[CreateUserRequest]
    )
    
    LOGIN_USER = EndpointConfig(
        url='/auth/login',
        request_model=LoginUserRequest,
        response_model=LoginUserResponse
    )
    
    CREATE_ACCOUNT = EndpointConfig(
        url='/accounts',
        request_model=None,
        response_model=CreateAccountResponse
    )

    GET_CUSTOMER_ACCOUNTS = EndpointConfig(
        url='/customer/accounts',
        request_model=None,
        response_model=List[CreateAccountResponse]
    )

    ACCOUNTS_DEPOSIT = EndpointConfig(
        url='/accounts/deposit',
        request_model=AccountDepositRequest,
        response_model=AccountDepositResponse,
    )

    ACCOUNTS_TRANSFER = EndpointConfig(
        url='/accounts/transfer',
        request_model=AccountTransferRequest,
        response_model=AccountTransferResponse,
    )

    UPDATE_CUSTOMER_PROFILE = EndpointConfig(
        url='/customer/profile',
        request_model=UpdateCustomerProfileRequest,
        response_model=UpdateCustomerProfileResponse,
    )

    GET_CUSTOMER_PROFILE = EndpointConfig(
        url='/customer/profile',
        request_model=None,
        response_model=GetCustomerProfileResponse,
    )