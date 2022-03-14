from dataclasses import dataclass
from datetime import datetime
from platform import platform
from enum import Enum
from typing import List, Optional

class ForecastType(Enum):
    binary = "binary"
    time_guess = "time"
    unknown = "unk"

@dataclass
class ForecastCommonData:
    platform: str
    id_on_platform: str | int

    forecast_type: ForecastType

    question_title: str
    question_url: str

    created_time: datetime


@dataclass
class MetaculusCommunityFullPrediction:
    y: List[float]
    q1: int
    q2: int
    q3: int

@dataclass
class MetaculusCommunityPrediction:
    full: MetaculusCommunityFullPrediction

@dataclass
class ForecastMetaculusData(ForecastCommonData):
    votes: int
    activity: float

    community_prediction: Optional[MetaculusCommunityPrediction]
    total_predictions: int

    close_time: datetime
    resolve_time: datetime
    
