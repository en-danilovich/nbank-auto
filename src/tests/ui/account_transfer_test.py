from typing import List

import pytest
from playwright.sync_api import Page

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_data import RandomData
from src.main.api.generators.random_model_generator import RandomModelGenerator
from src.main.ui.pages.bank_alert import BankAlert
from src.main.ui.pages.user_dashboard import UserDashboard
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.customer.update_customer_profile_request import UpdateCustomerProfileRequest
from src.main.api.models.user_account_context import UserAccountContext


@pytest.mark.ui
@pytest.mark.usefixtures("browser_match_guard")
class TestAccountTransfer:
    @pytest.mark.usefixtures("user_session_extension")
    @pytest.mark.user_session(10)
    def test_transfer_money_between_own_accounts(self, page: Page, api_manager: ApiManager,
                                                 user_request: CreateUserRequest):
        deposit_amount = RandomData.get_deposit_balance()
        transfer_amount = RandomData.get_deposit_balance(max_value=deposit_amount)

        profile_request = RandomModelGenerator.generate(UpdateCustomerProfileRequest)
        api_manager.user_steps.update_profile(user_request, profile_request)

        user_dashboard = UserDashboard(page).open()
        sender_account = user_dashboard.create_new_account()
        receiver_account = user_dashboard.create_new_account()

        user_dashboard.click_deposit_money()\
            .select_account(sender_account)\
            .enter_amount(deposit_amount)\
            .click_deposit()\
            .check_alert_message_and_accept(BankAlert.get_deposit_balance_success_msg(deposit_amount, sender_account))\
            .get_page(UserDashboard)\
            .click_make_transfer()\
            .select_account(sender_account)\
            .enter_recipient_name(profile_request.name)\
            .enter_recipient_account(receiver_account)\
            .enter_amount(transfer_amount)\
            .check_confirm()\
            .check_alert_message_and_accept(BankAlert.get_transfer_success_msg(transfer_amount, receiver_account))\
            .click_send()

        user_accounts = api_manager.user_steps.get_all_accounts(user_request)
        sender = next(a for a in user_accounts if a.accountNumber == sender_account)
        receiver = next(a for a in user_accounts if a.accountNumber == receiver_account)
        assert sender.balance == deposit_amount - transfer_amount
        assert receiver.balance == transfer_amount

    @pytest.mark.with_users(accounts_count=1)
    def test_transfer_empty_form(self, page: Page, api_manager: ApiManager,
                                 accounts_with_balance: List[UserAccountContext]):
        user_context = accounts_with_balance[0]
        account = user_context.accounts[0]
        user_dashboard = UserDashboard(page)
        user_dashboard.auth_as_user(user_context.user)
        user_dashboard.open()\
            .click_make_transfer()\
            .check_alert_message_and_accept(BankAlert.FILL_ALL_FIELDS)\
            .click_send()
        api_manager.user_steps.verify_account_balance(user_context.user, account.id, account.balance)

    @pytest.mark.with_users(accounts_count=2, balance=100)
    def test_transfer_confirmation_not_checked(self, page: Page, api_manager: ApiManager,
                                               accounts_with_balance: List[UserAccountContext]):
        user_context = accounts_with_balance[0]
        sender_account, receiver_account = user_context.accounts[0], user_context.accounts[1]
        profile_request = RandomModelGenerator.generate(UpdateCustomerProfileRequest)
        api_manager.user_steps.update_profile(user_context.user, profile_request)

        user_dashboard = UserDashboard(page)
        user_dashboard.auth_as_user(user_context.user)
        user_dashboard.open()\
            .click_make_transfer()\
            .select_account(sender_account.accountNumber)\
            .enter_recipient_name(profile_request.name)\
            .enter_recipient_account(receiver_account.accountNumber)\
            .enter_amount(RandomData.get_deposit_balance(max_value=100))\
            .check_alert_message_and_accept(BankAlert.FILL_ALL_FIELDS)\
            .click_send()
        api_manager.user_steps.verify_account_balance(user_context.user, sender_account.id, sender_account.balance)
        api_manager.user_steps.verify_account_balance(user_context.user, receiver_account.id, receiver_account.balance)

    @pytest.mark.with_users(accounts_count=2, balance=15000)
    @pytest.mark.parametrize('amount, alert_msg', [
        (0, BankAlert.TRANSFER_INSUFFICIENT_FUNDS),
        (10000.01, BankAlert.TRANSFER_INSUFFICIENT_FUNDS),
    ])
    def test_transfer_invalid_amount(self, page: Page, api_manager: ApiManager,
                                     accounts_with_balance: List[UserAccountContext],
                                     amount: float, alert_msg: str):
        user_context = accounts_with_balance[0]
        sender_account, receiver_account = user_context.accounts[0], user_context.accounts[1]
        profile_request = RandomModelGenerator.generate(UpdateCustomerProfileRequest)
        api_manager.user_steps.update_profile(user_context.user, profile_request)

        user_dashboard = UserDashboard(page)
        user_dashboard.auth_as_user(user_context.user)
        user_dashboard.open()\
            .click_make_transfer()\
            .select_account(sender_account.accountNumber)\
            .enter_recipient_name(profile_request.name)\
            .enter_recipient_account(receiver_account.accountNumber)\
            .enter_amount(amount)\
            .check_confirm()\
            .check_alert_message_and_accept(alert_msg)\
            .click_send()
        api_manager.user_steps.verify_account_balance(user_context.user, sender_account.id, sender_account.balance)
        api_manager.user_steps.verify_account_balance(user_context.user, receiver_account.id, receiver_account.balance)

    @pytest.mark.with_users(accounts_count=2, balance=100)
    def test_transfer_wrong_recipient_name(self, page: Page, api_manager: ApiManager,
                                           accounts_with_balance: List[UserAccountContext]):
        user_context = accounts_with_balance[0]
        sender_account, receiver_account = user_context.accounts[0], user_context.accounts[1]
        profile_request = RandomModelGenerator.generate(UpdateCustomerProfileRequest)
        api_manager.user_steps.update_profile(user_context.user, profile_request)
        wrong_name = RandomModelGenerator.generate(UpdateCustomerProfileRequest).name

        user_dashboard = UserDashboard(page)
        user_dashboard.auth_as_user(user_context.user)
        user_dashboard.open()\
            .click_make_transfer()\
            .select_account(sender_account.accountNumber)\
            .enter_recipient_name(wrong_name)\
            .enter_recipient_account(receiver_account.accountNumber)\
            .enter_amount(RandomData.get_deposit_balance(max_value=100))\
            .check_confirm()\
            .check_alert_message_and_accept(BankAlert.RECIPIENT_NAME_MISMATCH)\
            .click_send()
        api_manager.user_steps.verify_account_balance(user_context.user, sender_account.id, sender_account.balance)
        api_manager.user_steps.verify_account_balance(user_context.user, receiver_account.id, receiver_account.balance)

    @pytest.mark.with_users(accounts_count=2)
    def test_transfer_insufficient_funds(self, page: Page, api_manager: ApiManager,
                                         accounts_with_balance: List[UserAccountContext]):
        user_context = accounts_with_balance[0]
        sender_account, receiver_account = user_context.accounts[0], user_context.accounts[1]
        profile_request = RandomModelGenerator.generate(UpdateCustomerProfileRequest)
        api_manager.user_steps.update_profile(user_context.user, profile_request)

        user_dashboard = UserDashboard(page)
        user_dashboard.auth_as_user(user_context.user)
        user_dashboard.open()\
            .click_make_transfer()\
            .select_account(sender_account.accountNumber)\
            .enter_recipient_name(profile_request.name)\
            .enter_recipient_account(receiver_account.accountNumber)\
            .enter_amount(RandomData.get_deposit_balance())\
            .check_confirm()\
            .check_alert_message_and_accept(BankAlert.TRANSFER_INSUFFICIENT_FUNDS)\
            .click_send()
        api_manager.user_steps.verify_account_balance(user_context.user, sender_account.id, sender_account.balance)
        api_manager.user_steps.verify_account_balance(user_context.user, receiver_account.id, receiver_account.balance)

    @pytest.mark.with_users(accounts_count=1, balance=100)
    def test_transfer_to_same_account(self, page: Page, api_manager: ApiManager,
                                      accounts_with_balance: List[UserAccountContext]):
        user_context = accounts_with_balance[0]
        account = user_context.accounts[0]
        profile_request = RandomModelGenerator.generate(UpdateCustomerProfileRequest)
        api_manager.user_steps.update_profile(user_context.user, profile_request)
        transfer_amount = RandomData.get_deposit_balance(max_value=100)

        user_dashboard = UserDashboard(page)
        user_dashboard.auth_as_user(user_context.user)
        user_dashboard.open()\
            .click_make_transfer()\
            .select_account(account.accountNumber)\
            .enter_recipient_name(profile_request.name)\
            .enter_recipient_account(account.accountNumber)\
            .enter_amount(transfer_amount)\
            .check_confirm()\
            .check_alert_message_and_accept(BankAlert.get_transfer_success_msg(transfer_amount, account.accountNumber))\
            .click_send()
        api_manager.user_steps.verify_account_balance(user_context.user, account.id, account.balance)