from src.main.api.models.base_model import BaseModel


class FraudCheckServiceRequest(BaseModel):
    accountId: int
    relatedAccountId: int
    amount: float
    transactionType: str
