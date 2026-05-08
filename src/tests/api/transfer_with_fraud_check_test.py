import pytest
import allure

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.random_data import RandomData
from src.main.api.models.accounts.account_transfer_with_fraud_check_response import AccountTransferWithFraudCheckResponse
from src.main.api.fixtures.prepare_data_fixtures import PreparedUserAccount


FRAUD_APPROVED_MOCK = {
    "status": "SUCCESS",
    "decision": "APPROVED",
    "riskScore": 0.2,
    "reason": "Low risk transaction",
    "requiresManualReview": False,
    "additionalVerificationRequired": False,
}

FRAUD_APPROVED_EXPECTED = {
    "fraudRiskScore": FRAUD_APPROVED_MOCK["riskScore"],
    "fraudReason": FRAUD_APPROVED_MOCK["reason"],
    "requiresManualReview": False,
    "requiresVerification": False,
}

TRANSFER_APPROVED_EXPECTED = {
    "status": "APPROVED",
    "message": "Transfer approved and processed immediately",
    **FRAUD_APPROVED_EXPECTED,
}


@pytest.mark.api
@pytest.mark.api_version("with_fraud_check")
@pytest.mark.prepare_users(number=2)
@pytest.mark.prepare_accounts(number=2, deposit=5000)
class TestTransferWithFraudCheck:
    @pytest.mark.fraud_check_mock(
        port=8089,
        # Match any POST path so the backend can reach the mock even if it calls
        # a different fraud-check URL internally (similar to WireMock urlPathMatching).
        endpoint=r"/.*",
        **FRAUD_APPROVED_MOCK,
    )
    def test_transfer_with_fraud_check(
        self,
        api_manager: ApiManager,
        prepared_user_accounts: list[PreparedUserAccount],
    ):
        with allure.step("Prepare sender/receiver accounts (2 accounts with deposit=5000)"):
            sender = prepared_user_accounts[0]
            receiver = prepared_user_accounts[1]

        with allure.step("Transfer with fraud check"):
            transfer_amount = RandomData.get_float(0.1, 4999.9)
            transfer_response = api_manager.user_steps.transfer_with_fraud_check(
                sender.user,
                sender.account.id,
                receiver.account.id,
                transfer_amount,
            )

        with allure.step("Validate transfer response matches mocked fraud decision"):
            assert transfer_response is not None

            expected = AccountTransferWithFraudCheckResponse(
                amount=transfer_amount,
                senderAccountId=sender.account.id,
                receiverAccountId=receiver.account.id,
                **TRANSFER_APPROVED_EXPECTED,
            )

            assert transfer_response.model_dump() == expected.model_dump()
