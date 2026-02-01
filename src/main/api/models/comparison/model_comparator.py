from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class Mismatch:
    field_name: str
    expected: Any
    actual: Any


class ComparisonResult:
    def __init__(self, mismatches: List[Mismatch]):
        self._mismatches = mismatches

    def is_success(self) -> bool:
        return not self.mismatches
    
    @property
    def mismatches(self) -> List[Mismatch]:
        return self._mismatches 
    

class ModelComparator:
    @staticmethod
    def compare_fields(request: Any, response: Any, field_mapping: Dict[str, str]):
        mismatches = []

        for request_field, response_field in field_mapping.items():
            request_value = ModelComparator._get_field_value(request, request_field)
            response_value = ModelComparator._get_field_value(response, response_field)

            if str(request_value) != str(response_value):
                mismatches.append(Mismatch(f'{request_field} -> {response_field}', request_value, response_value))
        
        return ComparisonResult(mismatches)

    def _get_field_value(obj: Any, field_name: str):
        current_class = obj.__class__

        while current_class:
            if hasattr(obj, field_name):
                return getattr(obj, field_name)
            current_class = current_class.__base__

        raise AttributeError(f'Field {field_name} not found in class {obj.__class__.__name__}')
