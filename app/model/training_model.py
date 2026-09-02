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


class TrainingTask(BaseModel):
    id: str
    name: str
    link_url: Optional[str] = None


class TrainingModule(BaseModel):
    id: str
    name: str
    group_name: str
    icon: TrainingModuleIcon
    tasks: List[TrainingTask]
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None


class CreateTrainingTaskReq(BaseModel):
    name: str
    link_url: Optional[str] = None


class CreateTrainingTaskResp(TrainingTask):
    pass


class UpdateTrainingTaskReq(BaseModel):
    name: Optional[str] = None
    link_url: Optional[str] = None


class UpdateTrainingTaskResp(TrainingTask):
    pass


class CreateTrainingModuleReq(BaseModel):
    name: str
    group_name: str
    icon: TrainingModuleIcon
    tasks: Optional[List[CreateTrainingTaskReq]] = []


class CreateTrainingModuleResp(TrainingModule):
    pass


class UpdateTrainingModuleReq(BaseModel):
    name: Optional[str] = None
    group_name: Optional[str] = None
    icon: Optional[TrainingModuleIcon] = None
    tasks: Optional[List[TrainingTask]] = None


class UpdateTrainingModuleResp(TrainingModule):
    pass


class DeleteTrainingModuleResp(TrainingModule):
    pass


class GetTrainingModulesByLocationIdResp(BaseModel):
    training_modules: List[TrainingModule]
