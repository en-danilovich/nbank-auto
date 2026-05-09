import json

import pytest
import allure

from src.main.api.classes.api_manager import ApiManager
from src.main.api.constants.error_messages import ErrorMessages
from src.main.api.generators.random_data import RandomData
from src.main.api.models.accounts.account_transfer_with_fraud_check_request import AccountTransferWithFraudCheckRequest
from src.main.api.models.accounts.account_transfer_with_fraud_check_response import AccountTransferWithFraudCheckResponse
from src.main.api.fixtures.fraud_fixtures import FraudMockServer
from src.main.api.fixtures.prepare_data_fixtures import PreparedUserAccount
from src.main.api.requests.skeleton.endpoint import Endpoint
from src.main.api.requests.skeleton.requesters.crud_requester import CrudRequester
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs


def _fraud_mock(
    decision: str,
    *,
    risk_score: float,
    reason: str,
    requires_manual_review: bool = False,
    additional_verification_required: bool = False,
) -> dict:
    return {
        "status": "SUCCESS",
        "decision": decision,
        "riskScore": risk_score,
        "reason": reason,
        "requiresManualReview": requires_manual_review,
        "additionalVerificationRequired": additional_verification_required,
    }


FRAUD_APPROVED_MOCK = _fraud_mock(
    "APPROVED",
    risk_score=0.2,
    reason="Low risk transaction",
)
# Backend coerces any non-APPROVED decision to MANUAL_REVIEW_REQUIRED.
FRAUD_DECLINED_MOCK = _fraud_mock(
    "DECLINED",
    risk_score=0.95,
    reason="High risk transaction",
)
FRAUD_MANUAL_REVIEW_MOCK = _fraud_mock(
    "MANUAL_REVIEW",
    risk_score=0.6,
    reason="Suspicious activity pattern",
    requires_manual_review=True,
)
FRAUD_REQUIRES_VERIFICATION_MOCK = _fraud_mock(
    "APPROVED",
    risk_score=0.4,
    reason="Unusual transaction location",
    additional_verification_required=True,
)


def _expected_response(
    fraud_mock: dict,
    *,
    status: str,
    message: str,
    amount: float,
    sender_id: int,
    receiver_id: int,
) -> AccountTransferWithFraudCheckResponse:
    return AccountTransferWithFraudCheckResponse(
        status=status,
        message=message,
        amount=amount,
        senderAccountId=sender_id,
        receiverAccountId=receiver_id,
        fraudRiskScore=fraud_mock["riskScore"],
        fraudReason=fraud_mock["reason"],
        requiresManualReview=fraud_mock["requiresManualReview"],
        requiresVerification=fraud_mock["additionalVerificationRequired"],
    )


@pytest.mark.api
@pytest.mark.api_version("with_fraud_check")
@pytest.mark.prepare_users(number=2)
@pytest.mark.prepare_accounts(number=2, deposit=5000)
class TestTransferWithFraudCheck:
    @pytest.mark.parametrize(
        ("fraud_mock_body", "expected_status", "expected_message"),
        [
            pytest.param(
                FRAUD_APPROVED_MOCK,
                "APPROVED",
                "Transfer approved and processed immediately",
                id="approved_low_risk",
                marks=pytest.mark.fraud_check_mock(
                    port=8089, endpoint=r"/.*", **FRAUD_APPROVED_MOCK
                ),
            ),
            pytest.param(
                FRAUD_DECLINED_MOCK,
                "MANUAL_REVIEW_REQUIRED",
                "Transfer requires manual review",
                id="declined_high_risk",
                marks=pytest.mark.fraud_check_mock(
                    port=8089, endpoint=r"/.*", **FRAUD_DECLINED_MOCK
                ),
            ),
            pytest.param(
                FRAUD_MANUAL_REVIEW_MOCK,
                "MANUAL_REVIEW_REQUIRED",
                "Transfer requires manual review",
                id="manual_review_required",
                marks=pytest.mark.fraud_check_mock(
                    port=8089, endpoint=r"/.*", **FRAUD_MANUAL_REVIEW_MOCK
                ),
            ),
            pytest.param(
                FRAUD_REQUIRES_VERIFICATION_MOCK,
                "APPROVED",
                "Transfer approved and processed immediately",
                id="additional_verification_required",
                marks=pytest.mark.fraud_check_mock(
                    port=8089, endpoint=r"/.*", **FRAUD_REQUIRES_VERIFICATION_MOCK
                ),
            ),
        ],
    )
    def test_transfer_with_fraud_check(
        self,
        api_manager: ApiManager,
        prepared_user_accounts: list[PreparedUserAccount],
        fraud_check_mock_server: FraudMockServer,
        fraud_mock_body: dict,
        expected_status: str,
        expected_message: str,
    ):
        with allure.step("Prepare sender/receiver accounts (2 accounts with deposit=5000)"):
            sender = prepared_user_accounts[0]
            receiver = prepared_user_accounts[1]

        with allure.step(f"Transfer with fraud check (mock decision={fraud_mock_body['decision']})"):
            transfer_amount = RandomData.get_float(0.1, 4999.9)
            transfer_response = api_manager.user_steps.transfer_with_fraud_check(
                sender.user,
                sender.account.id,
                receiver.account.id,
                transfer_amount,
            )

        with allure.step(f"Validate response matches mocked fraud decision (expected status={expected_status})"):
            assert transfer_response is not None

            expected = _expected_response(
                fraud_mock_body,
                status=expected_status,
                message=expected_message,
                amount=transfer_amount,
                sender_id=sender.account.id,
                receiver_id=receiver.account.id,
            )

            assert transfer_response.model_dump() == expected.model_dump()

        with allure.step("Verify fraud service was called exactly once with correct payload"):
            assert fraud_check_mock_server.call_count == 1, (
                f"Expected fraud service to be called exactly once, "
                f"but recorded {fraud_check_mock_server.call_count} call(s): "
                f"{fraud_check_mock_server.calls}"
            )
            recorded = fraud_check_mock_server.calls[0]
            assert recorded["method"] == "POST", f"Fraud service was called with {recorded['method']}, expected POST"
            payload = json.loads(recorded["body"])
            assert payload["accountId"] == sender.account.id, (
                f"Fraud service got senderAccountId={payload.get('accountId')}, expected {sender.account.id}"
            )
            assert payload["relatedAccountId"] == receiver.account.id, (
                f"Fraud service got receiverAccountId={payload.get('relatedAccountId')}, expected {receiver.account.id}"
            )
            assert payload["amount"] == transfer_amount, (
                f"Fraud service got amount={payload.get('amount')}, expected {transfer_amount}"
            )
            assert payload["transactionType"] == "TRANSFER_OUT", (
                f"Fraud service got transactionType={payload.get('transactionType')}, expected TRANSFER_OUT"
            )

        with allure.step("Verify DB balances: APPROVED applies the transfer, MANUAL_REVIEW_REQUIRED does not"):
            sender_dao = api_manager.database_steps.get_account_by_account_number(sender.account.accountNumber)
            receiver_dao = api_manager.database_steps.get_account_by_account_number(receiver.account.accountNumber)
            if expected_status == "APPROVED":
                assert sender_dao.balance == round(sender.account.balance - transfer_amount, 2), (
                    f"Sender DB balance mismatch after APPROVED transfer: "
                    f"expected {sender.account.balance - transfer_amount}, got {sender_dao.balance}"
                )
                assert receiver_dao.balance == round(receiver.account.balance + transfer_amount, 2), (
                    f"Receiver DB balance mismatch after APPROVED transfer: "
                    f"expected {receiver.account.balance + transfer_amount}, got {receiver_dao.balance}"
                )
            else:
                assert sender_dao.balance == sender.account.balance, (
                    f"Sender DB balance changed despite MANUAL_REVIEW_REQUIRED: "
                    f"was {sender.account.balance}, now {sender_dao.balance}"
                )
                assert receiver_dao.balance == receiver.account.balance, (
                    f"Receiver DB balance changed despite MANUAL_REVIEW_REQUIRED: "
                    f"was {receiver.account.balance}, now {receiver_dao.balance}"
                )

    def test_transfer_with_fraud_check_no_auth(self):
        CrudRequester(
            request_spec=RequestSpecs.unauth_spec(),
            endpoint=Endpoint.ACCOUNTS_TRANSFER_WITH_FRAUD_CHECK,
            response_spec=ResponseSpecs.unauthorized_request()
        ).post()

    @pytest.mark.parametrize('transfer_amount, error_message', [
        (-0.01, ErrorMessages.INVALID_FRAUD_TRANSFER),
        (0, ErrorMessages.INVALID_FRAUD_TRANSFER),
        (10000.1, ErrorMessages.MAX_TRANSFER_AMOUNT_MSG),
    ])
    @pytest.mark.fraud_check_mock(port=8089, endpoint=r"/.*", **FRAUD_APPROVED_MOCK)
    def test_transfer_with_fraud_check_invalid_amount(
        self,
        api_manager: ApiManager,
        prepared_user_accounts: list[PreparedUserAccount],
        fraud_check_mock_server: FraudMockServer,
        transfer_amount: float,
        error_message: str,
    ):
        sender = prepared_user_accounts[0]
        receiver = prepared_user_accounts[1]
        transfer_request = AccountTransferWithFraudCheckRequest(
            senderAccountId=sender.account.id,
            receiverAccountId=receiver.account.id,
            amount=transfer_amount,
        )
        api_manager.user_steps.transfer_with_fraud_check_invalid_data(sender.user, transfer_request, error_message)

        assert fraud_check_mock_server.call_count == 0, (
            f"Fraud service must not be called when input validation fails, "
            f"but it received {fraud_check_mock_server.call_count} call(s): "
            f"{fraud_check_mock_server.calls}"
        )

        sender_dao = api_manager.database_steps.get_account_by_account_number(sender.account.accountNumber)
        receiver_dao = api_manager.database_steps.get_account_by_account_number(receiver.account.accountNumber)
        assert sender_dao.balance == sender.account.balance, f"Sender DB balance changed: {sender_dao.balance}"
        assert receiver_dao.balance == receiver.account.balance, f"Receiver DB balance changed: {receiver_dao.balance}"

    @pytest.mark.fraud_check_mock(port=8089, endpoint=r"/.*", **FRAUD_APPROVED_MOCK)
    def test_transfer_with_fraud_check_user_has_no_access_to_other_user_account(
        self,
        api_manager: ApiManager,
        prepared_user_accounts: list[PreparedUserAccount],
        fraud_check_mock_server: FraudMockServer,
    ):
        first = prepared_user_accounts[0]
        second = prepared_user_accounts[1]
        transfer_request = AccountTransferWithFraudCheckRequest(
            senderAccountId=first.account.id,
            receiverAccountId=second.account.id,
            amount=RandomData.get_deposit_balance(),
        )
        api_manager.user_steps.transfer_with_fraud_check_forbidden_action(second.user, transfer_request)

        assert fraud_check_mock_server.call_count == 0, (
            f"Fraud service must not be called when ownership check fails, "
            f"but it received {fraud_check_mock_server.call_count} call(s): "
            f"{fraud_check_mock_server.calls}"
        )

        first_dao = api_manager.database_steps.get_account_by_account_number(first.account.accountNumber)
        second_dao = api_manager.database_steps.get_account_by_account_number(second.account.accountNumber)
        assert first_dao.balance == first.account.balance, f"Sender DB balance changed: {first_dao.balance}"
        assert second_dao.balance == second.account.balance, f"Receiver DB balance changed: {second_dao.balance}"

    @pytest.mark.fraud_check_mock(port=8089, endpoint=r"/.*", **FRAUD_APPROVED_MOCK)
    def test_transfer_with_fraud_check_insufficient_funds(
        self,
        api_manager: ApiManager,
        prepared_user_accounts: list[PreparedUserAccount],
        fraud_check_mock_server: FraudMockServer,
    ):
        sender = prepared_user_accounts[0]
        receiver = prepared_user_accounts[1]
        transfer_request = AccountTransferWithFraudCheckRequest(
            senderAccountId=sender.account.id,
            receiverAccountId=receiver.account.id,
            amount=sender.account.balance + 1,
        )
        api_manager.user_steps.transfer_with_fraud_check_invalid_data(
            sender.user, transfer_request, ErrorMessages.INSUFFICIENT_FUNDS
        )

        assert fraud_check_mock_server.call_count == 0, (
            f"Fraud service must not be called when funds check fails, "
            f"but it received {fraud_check_mock_server.call_count} call(s)"
        )

        sender_dao = api_manager.database_steps.get_account_by_account_number(sender.account.accountNumber)
        receiver_dao = api_manager.database_steps.get_account_by_account_number(receiver.account.accountNumber)
        assert sender_dao.balance == sender.account.balance, f"Sender DB balance changed: {sender_dao.balance}"
        assert receiver_dao.balance == receiver.account.balance, f"Receiver DB balance changed: {receiver_dao.balance}"

    @pytest.mark.fraud_check_mock(port=8089, endpoint=r"/.*", **FRAUD_APPROVED_MOCK)
    def test_transfer_with_fraud_check_non_existing_receiver(
        self,
        api_manager: ApiManager,
        prepared_user_accounts: list[PreparedUserAccount],
        fraud_check_mock_server: FraudMockServer,
    ):
        sender = prepared_user_accounts[0]
        transfer_request = AccountTransferWithFraudCheckRequest(
            senderAccountId=sender.account.id,
            receiverAccountId=RandomData.get_invalid_account_id(),
            amount=RandomData.get_deposit_balance(),
        )
        api_manager.user_steps.transfer_with_fraud_check_invalid_data(
            sender.user, transfer_request, ErrorMessages.INVALID_FRAUD_TRANSFER
        )

        assert fraud_check_mock_server.call_count == 0, (
            f"Fraud service must not be called for non-existing receiver, "
            f"but it received {fraud_check_mock_server.call_count} call(s)"
        )

        sender_dao = api_manager.database_steps.get_account_by_account_number(sender.account.accountNumber)
        assert sender_dao.balance == sender.account.balance, f"Sender DB balance changed: {sender_dao.balance}"

    @pytest.mark.fraud_check_mock(port=8089, endpoint=r"/.*", **FRAUD_APPROVED_MOCK)
    def test_transfer_with_fraud_check_non_existing_sender(
        self,
        api_manager: ApiManager,
        prepared_user_accounts: list[PreparedUserAccount],
        fraud_check_mock_server: FraudMockServer,
    ):
        receiver = prepared_user_accounts[0]
        transfer_request = AccountTransferWithFraudCheckRequest(
            senderAccountId=RandomData.get_invalid_account_id(),
            receiverAccountId=receiver.account.id,
            amount=RandomData.get_deposit_balance(),
        )
        api_manager.user_steps.transfer_with_fraud_check_forbidden_action(receiver.user, transfer_request)

        assert fraud_check_mock_server.call_count == 0, (
            f"Fraud service must not be called for non-existing sender, "
            f"but it received {fraud_check_mock_server.call_count} call(s)"
        )

        receiver_dao = api_manager.database_steps.get_account_by_account_number(receiver.account.accountNumber)
        assert receiver_dao.balance == receiver.account.balance, f"Receiver DB balance changed: {receiver_dao.balance}"

    @pytest.mark.parametrize('transfer_amount', [
        pytest.param(0.01, id="min_boundary"),
        pytest.param(5000.0, id="full_balance"),
    ])
    @pytest.mark.fraud_check_mock(port=8089, endpoint=r"/.*", **FRAUD_APPROVED_MOCK)
    def test_transfer_with_fraud_check_boundary_amounts(
        self,
        api_manager: ApiManager,
        prepared_user_accounts: list[PreparedUserAccount],
        fraud_check_mock_server: FraudMockServer,
        transfer_amount: float,
    ):
        sender = prepared_user_accounts[0]
        receiver = prepared_user_accounts[1]
        api_manager.user_steps.transfer_with_fraud_check(
            sender.user, sender.account.id, receiver.account.id, transfer_amount
        )

        assert fraud_check_mock_server.call_count == 1, (
            f"Expected fraud service to be called exactly once, "
            f"got {fraud_check_mock_server.call_count}"
        )

        sender_dao = api_manager.database_steps.get_account_by_account_number(sender.account.accountNumber)
        receiver_dao = api_manager.database_steps.get_account_by_account_number(receiver.account.accountNumber)
        assert sender_dao.balance == round(sender.account.balance - transfer_amount, 2), (
            f"Sender DB balance mismatch: expected {sender.account.balance - transfer_amount}, got {sender_dao.balance}"
        )
        assert receiver_dao.balance == round(receiver.account.balance + transfer_amount, 2), (
            f"Receiver DB balance mismatch: expected {receiver.account.balance + transfer_amount}, got {receiver_dao.balance}"
        )

    @pytest.mark.parametrize('transfer_amount', [
        pytest.param(10000.0, id="max_boundary"),
    ])
    @pytest.mark.prepare_accounts(number=2, deposit=10000)
    @pytest.mark.fraud_check_mock(port=8089, endpoint=r"/.*", **FRAUD_APPROVED_MOCK)
    def test_transfer_with_fraud_check_max_boundary_amount(
        self,
        api_manager: ApiManager,
        prepared_user_accounts: list[PreparedUserAccount],
        fraud_check_mock_server: FraudMockServer,
        transfer_amount: float,
    ):
        """Per-call backend cap is 10000 and that exact value should be accepted."""
        sender = prepared_user_accounts[0]
        receiver = prepared_user_accounts[1]
        api_manager.user_steps.transfer_with_fraud_check(
            sender.user, sender.account.id, receiver.account.id, transfer_amount
        )

        assert fraud_check_mock_server.call_count == 1, (
            f"Expected fraud service to be called exactly once, got {fraud_check_mock_server.call_count}"
        )

        sender_dao = api_manager.database_steps.get_account_by_account_number(sender.account.accountNumber)
        receiver_dao = api_manager.database_steps.get_account_by_account_number(receiver.account.accountNumber)
        assert sender_dao.balance == round(sender.account.balance - transfer_amount, 2)
        assert receiver_dao.balance == round(receiver.account.balance + transfer_amount, 2)
