from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.context import Context, get_context
from app.core.exceptions import (
    DatabaseError,
    InvalidListModificationError,
    NotFoundError,
    PermissionDeniedError,
)

from app.model.training_model import (
    CreateTrainingModuleReq,
    CreateTrainingModuleResp,
    CreateTrainingTaskReq,
    CreateTrainingTaskResp,
    DeleteTrainingModuleResp,
    GetTrainingModulesByLocationIdResp,
    UpdateTrainingModuleReq,
    UpdateTrainingModuleResp,
    UpdateTrainingTaskReq,
    UpdateTrainingTaskResp,
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
            tasks=req.tasks,
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
            tasks=req.tasks,
        )
    except DatabaseError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except PermissionDeniedError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err
    except InvalidListModificationError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
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
def get_training_modules_by_location_id(
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


@router.post(
    "/locations/{location_id}/training-modules/{module_id}/tasks",
    response_model=CreateTrainingTaskResp,
)
def create_training_task(
    location_id: str,
    module_id: str,
    req: CreateTrainingTaskReq,
    ctx: Context = Depends(get_context),
    training_service: TrainingService = Depends(),
) -> CreateTrainingTaskResp:
    try:
        created_task = training_service.create_training_task(
            context=ctx,
            location_id=location_id,
            module_id=module_id,
            task_name=req.name,
            task_url=req.link_url,
        )
    except DatabaseError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except PermissionDeniedError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err
    return created_task


@router.patch(
    "/locations/{location_id}/training-modules/{module_id}/tasks/{task_id}",
    response_model=UpdateTrainingTaskResp,
)
def update_training_task(
    location_id: str,
    module_id: str,
    task_id: str,
    req: UpdateTrainingTaskReq,
    ctx: Context = Depends(get_context),
    training_service: TrainingService = Depends(),
) -> UpdateTrainingTaskResp:
    try:
        updated_training_task = training_service.update_training_task(
            context=ctx,
            location_id=location_id,
            module_id=module_id,
            task_id=task_id,
            name=req.name,
            link_url=req.link_url,
        )
    except DatabaseError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except PermissionDeniedError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err
    return updated_training_task


@router.delete("/locations/{location_id}/training-modules/{module_id}/tasks/{task_id}")
def delete_training_task(
    location_id: str,
    module_id: str,
    task_id: str,
    ctx: Context = Depends(get_context),
    training_service: TrainingService = Depends(),
) -> Response:
    try:
        training_service.delete_training_task(
            context=ctx,
            location_id=location_id,
            module_id=module_id,
            task_id=task_id,
        )
    except DatabaseError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except PermissionDeniedError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err
    return Response(content=None)
