from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class TrainingModuleIcon(str, Enum):
    CFA_ICON_SANDWICH = "CFA_ICON_SANDWICH"
    CFA_ICON_NUGGETS = "CFA_ICON_NUGGETS"
    CFA_ICON_FRIES = "CFA_ICON_FRIES"
    CFA_ICON_PRESSURE_FRYER = "CFA_ICON_PRESSURE_FRYER"
    CFA_ICON_RAW_STATION = "CFA_ICON_RAW_STATION"
    CFA_ICON_LETTUCE_TOMATO = "CFA_ICON_LETTUCE_TOMATO"


class TrainingModule(BaseModel):
    id: str
    location_id: str
    name: str
    group_name: str
    icon: TrainingModuleIcon
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None


class CreateTrainingModuleReq(BaseModel):
    name: str
    group_name: str
    icon: TrainingModuleIcon


class CreateTrainingModuleResp(TrainingModule):
    pass


class UpdateTrainingModuleReq(BaseModel):
    name: Optional[str] = None
    group_name: Optional[str] = None
    icon: Optional[TrainingModuleIcon] = None


class UpdateTrainingModuleResp(TrainingModule):
    pass


class DeleteTrainingModuleResp(TrainingModule):
    pass


class GetTrainingModulesByLocationIdResp(BaseModel):
    training_modules: List[TrainingModule]
