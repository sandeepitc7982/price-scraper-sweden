from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BusinessRulesReport:
    """
    Represents the overall report of business rules checks.

    Attributes:
        vendor (str): The vendor for which the rules were checked.
        market (str): The market for which the rules were checked.
        rule_results (List[BusinessRuleResult]): A list of results from all business rules.
    """

    vendor: str
    market: str
    rule_name: str
    column_name: str
    success_percentage: Optional[float] = None
    violations: Optional[int] = None
    total_rows: Optional[int] = None


@dataclass
class QualityReport:
    vendor: str
    market: str
    column: str
    total_row_count: int
    null_count: int
    null_percentage: float
    distinct_count: int
    distinct_percentage: float
    non_distinct_count: int
    non_distinct_percentage: float
    zero_count: int
    zero_percentage: float
    data_types: List[str]
    special_char_count: int
    special_char_percentage: float
    mean: Optional[
        float
    ]  # Optional, because mean might not be calculated for non-numeric columns
    min: Optional[float]  # Optional
    max: Optional[float]  # Optional
    percentile_25: Optional[float]  # Optional
    percentile_50: Optional[float]  # Optional
    percentile_75: Optional[float]  # Optional
    std_dev: Optional[float]  # Optional


@dataclass
class QualityReportOutput:
    total_count: int
    null_count: int
    zero_count: int
    distinct_count: int
    non_distinct_count: int
    mean_value: float
    min_value: float
    max_value: float
    percentile_25: float
    percentile_50: float
    percentile_75: float
    std_dev: float
    unique_types: List[str]
    inconsistent_type: bool


@dataclass
class QualityMetricsOutput:
    vendor: str
    market: str
    insight: str
    insight_type: str
    metric: str
    score: float


@dataclass
class QualityRulesOutput:
    vendor: str
    market: str
    insight: str
    insight_type: str
    metric: str
    score: float
    severity: str
