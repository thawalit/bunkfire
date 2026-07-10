from typing import Literal, Optional

from pydantic import BaseModel


class RocketResult(BaseModel):
    rocket_name: str
    metric_a: Optional[int] = None
    metric_b: Optional[int] = None
    metric_category_text: Optional[str] = None
    achieved_raw: Optional[str] = None
    achieved_value: Optional[int] = None
    outcome_icon: Literal["win", "loss", "tie"]
    is_champion: bool = False


class ExtractionResult(BaseModel):
    is_result_board: bool
    event_venue: Optional[str] = None
    event_date_day: Optional[int] = None
    event_date_month_th: Optional[str] = None
    event_date_year_be: Optional[int] = None
    rockets: list[RocketResult] = []
