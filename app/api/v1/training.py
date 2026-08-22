from fastapi import APIRouter, Depends, HTTPException

from app.core.context import Context, get_context
from app.core.exceptions import DatabaseError, NotFoundError, PermissionDeniedError

from app.model.training_model import (
    CreateTrainingModuleReq,
    CreateTrainingModuleResp,
    DeleteTrainingModuleResp,
    GetTrainingModulesByLocationIdResp,
    UpdateTrainingModuleReq,
    UpdateTrainingModuleResp,
)
from app.service.training_service import TrainingService

router = APIRouter()


@router.post(
    "/locations/{location_id}/training-modules", response_model=CreateTrainingModuleResp
)
def create_training_module(
    location_id: str,
    req: CreateTrainingModuleReq,
    ctx: Context = Depends(get_context),
    training_service: TrainingService = Depends(),
) -> CreateTrainingModuleResp:
    try:
        new_training_module = training_service.create_training_module(
            context=ctx,
            location_id=location_id,
            name=req.name,
            group_name=req.group_name,
            icon=req.icon,
        )
    except DatabaseError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except PermissionDeniedError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err
    return new_training_module


@router.patch(
    "/locations/{location_id}/training-modules/{module_id}",
    response_model=UpdateTrainingModuleResp,
)
def update_training_module(
    req: UpdateTrainingModuleReq,
    location_id: str,
    module_id: str,
    ctx: Context = Depends(get_context),
    training_service: TrainingService = Depends(),
) -> UpdateTrainingModuleResp:
    try:
        updated_training_module = training_service.update_training_module(
            context=ctx,
            location_id=location_id,
            module_id=module_id,
            name=req.name,
            group_name=req.group_name,
            icon=req.icon,
        )
    except DatabaseError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except PermissionDeniedError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err
    return updated_training_module


@router.delete(
    "/locations/{location_id}/training-modules/{module_id}",
    response_model=DeleteTrainingModuleResp,
)
def delete_training_module(
    location_id: str,
    module_id: str,
    ctx: Context = Depends(get_context),
    training_service: TrainingService = Depends(),
) -> DeleteTrainingModuleResp:
    try:
        deleted_training_module = training_service.delete_training_module(
            context=ctx, location_id=location_id, module_id=module_id
        )
    except DatabaseError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except PermissionDeniedError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err
    return deleted_training_module


@router.get(
    "/locations/{location_id}/training-modules",
    response_model=GetTrainingModulesByLocationIdResp,
)
def get_posts_by_location_id(
    location_id: str,
    include_deleted: bool = False,
    ctx: Context = Depends(get_context),
    training_service: TrainingService = Depends(),
) -> GetTrainingModulesByLocationIdResp:
    try:
        training_modules = training_service.get_training_modules_by_location_id(
            context=ctx, location_id=location_id, include_deleted=include_deleted
        )
    except DatabaseError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except PermissionDeniedError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err
    return GetTrainingModulesByLocationIdResp(training_modules=training_modules)
