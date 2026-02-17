from dataclasses import dataclass


@dataclass
class RegexGeneratingRule:
    regex: str

@dataclass
class MinMaxFloatGeneratingRule:
    min: float
    max: float
    right_digits: int = 2