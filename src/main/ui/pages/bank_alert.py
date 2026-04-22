from enum import Enum


class BankAlert(str, Enum):
    USER_CREATED_SUCCESSFULLY = "✅ User created successfully!"
    USERNAME_MUST_BE_BETWEEN_3_AND_15_CHARACTERS = "Username must be between 3 and 15 characters"
    NEW_ACCOUNT_CREATED = "✅ New Account Created! Account Number:"
    SELECT_ACCOUNT = "❌ Please select an account."
    ENTER_VALID_AMOUNT = "❌ Please enter a valid amount."
    MAX_DEPOSIT_EXCEEDED = "❌ Please deposit less or equal to 5000$."
    PROFILE_UPDATED_SUCCESSFULLY = "✅ Name updated successfully!"
    ENTER_VALID_NAME = "❌ Please enter a valid name."
    NAME_MUST_CONTAIN_TWO_WORDS = "Name must contain two words with letters only"
    FILL_ALL_FIELDS = "❌ Please fill all fields and confirm."
    RECIPIENT_NAME_MISMATCH = "❌ The recipient name does not match the registered name."
    TRANSFER_MIN_AMOUNT = "❌ Error: Transfer amount must be at least 0.01"
    TRANSFER_MAX_AMOUNT = "❌ Error: Transfer amount cannot exceed 10000"
    TRANSFER_INSUFFICIENT_FUNDS = "❌ Error: Invalid transfer: insufficient funds or invalid accounts"

    @staticmethod
    def get_deposit_balance_success_msg(amount: float, account_number: str) -> str:
        return f"✅ Successfully deposited ${amount} to account {account_number}!"

    @staticmethod
    def get_transfer_success_msg(amount: float, account_number: str) -> str:
        return f"✅ Successfully transferred ${amount} to account {account_number}!"