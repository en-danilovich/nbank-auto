from __future__ import annotations

from typing import Any

from src.main.api.models.comparison.model_comparator import ModelComparator
from src.main.api.models.comparison.model_comparison_configuration import ModelComparisonConfigLoader


class DaoAndModelAssertions:
    """
    Compare DTO (API response) with DAO (DB row representation) using mapping rules
    from resources/dao-comparison.properties.
    """

    def __init__(self, left: Any, right: Any):
        self.left = left
        self.right = right

    @staticmethod
    def assert_that(left: Any, right: Any) -> "DaoAndModelAssertions":
        return DaoAndModelAssertions(left, right)

    def match(self) -> "DaoAndModelAssertions":
        config_loader = ModelComparisonConfigLoader("dao-comparison.properties")
        rule = config_loader.get_rule_for(self.left)

        if rule is None:
            raise AssertionError(f"No comparion rule found for class {self.left.__class__.__name__}")

        result = ModelComparator.compare_fields(self.left, self.right, rule.field_mapping)
        if not result.is_success():
            raise AssertionError(f"DAO/DTO comparison failed with mismatches fields: \n{result.mismatches}")
        return self