from src.main.api.models.base_model import BaseModel


class AccountTransferRequest(BaseModel):
    senderAccountId: int
    receiverAccountId: int
    amount: float
