import random
import sys

from faker import Faker

faker = Faker()


class RandomData:
    @staticmethod
    def get_username(length: int | None = None) -> str:
        return ''.join(faker.random_letters(length or random.randint(3, 15)))
    
    @staticmethod
    def get_password() -> str:
        upper = [letter.upper() for letter in faker.random_letters(length=3)]
        lower = [letter.lower() for letter in faker.random_letters(length=3)]
        digits = [str(faker.random_digit()) for _ in range(3)]
        special = [random.choice('!@#$%^&')]
        password = upper + lower + digits + special
        random.shuffle(password)
        return ''.join(password)

    @staticmethod
    def get_deposit_balance(min_value=0.01, max_value=5000.0, right_digits=2) -> float:
        return faker.pyfloat(min_value=min_value, max_value=max_value, right_digits=right_digits)

    @staticmethod
    def get_special_symbol() -> str:
        return random.choice('!@#$%^&')

    @staticmethod
    def get_word():
        return faker.word()

    @staticmethod
    def get_int(min_val, max_val) -> int:
        return faker.pyint(min_value=min_val, max_value=max_val)

    @staticmethod
    def get_float(min_val, max_val) -> float:
        return faker.pyfloat(min_value=min_val, max_value=max_val)

    @staticmethod
    def get_invalid_account_id():
        return faker.pyint(min_value=999999, max_value=sys.maxsize)