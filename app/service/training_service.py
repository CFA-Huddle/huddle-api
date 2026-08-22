from boto3.dynamodb.conditions import Key

from app.core.config import config
from app.core.context import Context
from app.core.exceptions import NotFoundError
from app.core.permissions import validate_permissions
from app.db import Table
from app.model.training_model import TrainingModule, TrainingModuleIcon
from app.utils.ids import generate_uuid
from app.utils.time import get_current_time


class TrainingService:
    def __init__(self):
        self.db = Table(
            table_name=config.training_modules_table_name, aws_region=config.aws_region
        )

    @staticmethod
    def _build_training_module_item(**kwargs) -> dict:
        current_time = get_current_time()
        module_id = kwargs.get("id", generate_uuid())
        return {
            "PK": f"LOCATION#{kwargs["location_id"]}",
            "SK": f"MODULE#{module_id}",
            "id": module_id,
            "location_id": kwargs["location_id"],
            "name": kwargs["name"],
            "group_name": kwargs["group_name"],
            "icon": kwargs["icon"],
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
    ) -> TrainingModule:
        validate_permissions(context.user_id, location_id, "training-module:create")

        training_module_item = self._build_training_module_item(
            location_id=location_id,
            name=name,
            group_name=group_name,
            icon=icon,
        )

        self.db.put_item(item=training_module_item)
        return TrainingModule(**training_module_item)

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

        validate_permissions(
            context.user_id, item.get("location_id"), "training-module:update"
        )

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
            item.get("location_id"),
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
