from src.main.api.models.base_model import BaseModel


class AccountTransferWithFraudCheckRequest(BaseModel):
    senderAccountId: int
    receiverAccountId: int
    amount: float
