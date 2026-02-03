from src.main.api.models.base_model import BaseModel


class AccountTransferResponse(BaseModel):
    message: str
    amount: float
    receiverAccountId: int
    senderAccountId: int
