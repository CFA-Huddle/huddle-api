from collections import Counter

from boto3.dynamodb.conditions import Key

from app.core.config import config
from app.core.context import Context
from app.core.exceptions import InvalidListModificationError, NotFoundError
from app.core.permissions import validate_permissions
from app.db import Table
from app.model.training_model import (
    CreateTrainingTaskReq,
    TrainingModule,
    TrainingModuleIcon,
    TrainingTask,
)
from app.utils.ids import generate_uuid
from app.utils.time import get_current_time


class TrainingService:
    def __init__(self):
        self.db = Table(
            table_name=config.training_modules_table_name, aws_region=config.aws_region
        )

    @staticmethod
    def _build_training_task(**kwargs) -> TrainingTask:
        return TrainingTask(
            id=generate_uuid(), name=kwargs["name"], link_url=kwargs["link_url"]
        )

    @staticmethod
    def _serialize_training_task(task: TrainingTask) -> dict:
        item = task.model_dump()
        return item

    @staticmethod
    def _serialize_training_tasks(tasks: list[TrainingTask]) -> list[dict]:
        return [task.model_dump() for task in tasks]

    @staticmethod
    def _build_training_module_item(**kwargs) -> dict:
        current_time = get_current_time()
        module_id = kwargs.get("id", generate_uuid())
        return {
            "PK": f"LOCATION#{kwargs["location_id"]}",
            "SK": f"MODULE#{module_id}",
            "id": module_id,
            "name": kwargs["name"],
            "group_name": kwargs["group_name"],
            "icon": kwargs["icon"],
            "tasks": kwargs.get("tasks", []),
            "created_at": kwargs.get("created_at", current_time),
            "updated_at": kwargs.get("updated_at", current_time),
            "deleted_at": kwargs.get("deleted_at", None),
        }

    def create_training_module(
        self,
        context: Context,
        location_id: str,
        name: str,
        group_name: str,
        icon: TrainingModuleIcon,
        tasks: list[CreateTrainingTaskReq],
    ) -> TrainingModule:
        validate_permissions(context.user_id, location_id, "training-module:create")

        training_tasks = []
        for task in tasks:
            new_task = self._build_training_task(name=task.name, link_url=task.link_url)
            task_item = self._serialize_training_task(new_task)
            training_tasks.append(task_item)

        training_module_item = self._build_training_module_item(
            location_id=location_id,
            name=name,
            group_name=group_name,
            icon=icon,
            tasks=training_tasks,
        )

        self.db.put_item(item=training_module_item)
        return TrainingModule(**training_module_item)

    @staticmethod
    def contains_same_ids(incoming_list, existing_list):
        return Counter(item["id"] for item in incoming_list) == Counter(
            item["id"] for item in existing_list
        )

    def update_training_module(
        self, context: Context, location_id: str, module_id: str, **kwargs
    ) -> TrainingModule:
        key = {
            "PK": f"LOCATION#{location_id}",
            "SK": f"MODULE#{module_id}",
        }

        item = self.db.get_item(key)
        # Verify item exists
        if not item or item.get("deleted_at"):
            raise NotFoundError("Training module not found")

        validate_permissions(context.user_id, location_id, "training-module:update")

        # Return early if no attributes are provided
        if all(value is None for value in kwargs.values()):
            return TrainingModule.model_validate(item)

        # Set updated_at timestamp
        update_expression = "SET #updated_at = :updated_at"
        names = {"#updated_at": "updated_at"}
        values = {":updated_at": get_current_time()}

        if kwargs.get("name"):
            update_expression += ", #name = :name"
            names["#name"] = "name"
            values[":name"] = kwargs["name"]
        if kwargs.get("group_name"):
            update_expression += ", #group_name = :group_name"
            names["#group_name"] = "group_name"
            values[":group_name"] = kwargs["group_name"]
        if kwargs.get("icon"):
            update_expression += ", #icon = :icon"
            names["#icon"] = "icon"
            values[":icon"] = kwargs["icon"]
        if "tasks" in kwargs and kwargs["tasks"] is not None:
            new_tasks = self._serialize_training_tasks(tasks=kwargs.get("tasks", []))
            if not self.contains_same_ids(new_tasks, item["tasks"]):
                raise InvalidListModificationError(
                    "Cannot add or remove tasks. You may only reorder or edit existing tasks."
                )

            update_expression += ", #tasks = :tasks"
            names["#tasks"] = "tasks"
            values[":tasks"] = new_tasks

        updated_item = self.db.update_item(
            key=key,
            update_expression=update_expression,
            attr_names=names,
            attr_values=values,
        )
        return TrainingModule.model_validate(updated_item)

    def delete_training_module(
        self, context: Context, location_id: str, module_id: str
    ) -> TrainingModule:
        key = {
            "PK": f"LOCATION#{location_id}",
            "SK": f"MODULE#{module_id}",
        }

        item = self.db.get_item(key)
        # Verify item exists and is not already deleted
        if not item or item.get("deleted_at"):
            raise NotFoundError("Training module not found")

        validate_permissions(
            context.user_id,
            location_id,
            "training-module:delete",
        )

        update_expression = "SET #deleted_at = :deleted_at"
        names = {"#deleted_at": "deleted_at"}
        values = {":deleted_at": get_current_time()}

        updated_item = self.db.update_item(
            key=key,
            update_expression=update_expression,
            attr_names=names,
            attr_values=values,
        )
        return TrainingModule(**updated_item)

    def get_training_modules_by_location_id(
        self,
        context: Context,
        location_id: str,
        include_deleted: bool = False,
    ) -> list[TrainingModule]:
        validate_permissions(context.user_id, location_id, "training-module:read")

        key_expression = Key("PK").eq(f"LOCATION#{location_id}")
        items = self.db.query(
            key_expression=key_expression,
        )

        training_modules = list(map(lambda item: TrainingModule(**item), items))

        if not include_deleted:
            training_modules = [
                module for module in training_modules if not module.deleted_at
            ]
        return training_modules

    def create_training_task(
        self,
        context: Context,
        location_id: str,
        module_id: str,
        task_name: str,
        task_url: str,
    ) -> TrainingTask:
        key = {
            "PK": f"LOCATION#{location_id}",
            "SK": f"MODULE#{module_id}",
        }

        item = self.db.get_item(key)
        # Verify item exists
        if not item or item.get("deleted_at"):
            raise NotFoundError("Training module not found")

        validate_permissions(context.user_id, location_id, "training-task:create")

        existing_tasks = item.get("tasks", [])
        new_task = self._build_training_task(name=task_name, link_url=task_url)
        task_item = self._serialize_training_task(new_task)
        existing_tasks.append(task_item)

        # Update tasks list in dynamodb

        update_expression = "SET #tasks = :tasks"
        names = {"#tasks": "tasks"}
        values = {":tasks": existing_tasks}

        self.db.update_item(
            key=key,
            update_expression=update_expression,
            attr_names=names,
            attr_values=values,
        )
        return TrainingTask(**task_item)

    def update_training_task(
        self,
        context: Context,
        location_id: str,
        module_id: str,
        task_id: str,
        **kwargs,
    ) -> TrainingTask:
        key = {
            "PK": f"LOCATION#{location_id}",
            "SK": f"MODULE#{module_id}",
        }

        item = self.db.get_item(key)
        # Verify item exists
        if not item or item.get("deleted_at"):
            raise NotFoundError("Training module not found")

        validate_permissions(context.user_id, location_id, "training-task:update")

        existing_tasks = item.get("tasks", [])

        # Find the item first
        task_to_update = next(
            (task for task in existing_tasks if task.get("id") == task_id), None
        )

        # If it exists, update the item
        if task_to_update:
            if kwargs.get("name"):
                task_to_update["name"] = kwargs["name"]
            if kwargs.get("link_url"):
                task_to_update["link_url"] = kwargs["link_url"]
        else:
            raise NotFoundError("Training task not found")

        # Update tasks list in dynamodb
        update_expression = "SET #tasks = :tasks"
        names = {"#tasks": "tasks"}
        values = {":tasks": existing_tasks}

        self.db.update_item(
            key=key,
            update_expression=update_expression,
            attr_names=names,
            attr_values=values,
        )
        return TrainingTask(**task_to_update)

    def delete_training_task(
        self,
        context: Context,
        location_id: str,
        module_id: str,
        task_id: str,
    ) -> TrainingTask:
        key = {
            "PK": f"LOCATION#{location_id}",
            "SK": f"MODULE#{module_id}",
        }

        item = self.db.get_item(key)
        # Verify item exists
        if not item or item.get("deleted_at"):
            raise NotFoundError("Training module not found")

        validate_permissions(context.user_id, location_id, "training-task:delete")

        existing_tasks = item.get("tasks", [])

        # Find the item first
        task_to_delete = next(
            (task for task in existing_tasks if task.get("id") == task_id), None
        )

        # If it exists, remove it from the list
        if task_to_delete:
            existing_tasks.remove(task_to_delete)
        else:
            raise NotFoundError("Training task not found")

        # Update tasks list in dynamodb
        update_expression = "SET #tasks = :tasks"
        names = {"#tasks": "tasks"}
        values = {":tasks": existing_tasks}

        self.db.update_item(
            key=key,
            update_expression=update_expression,
            attr_names=names,
            attr_values=values,
        )
