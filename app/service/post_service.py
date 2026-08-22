from boto3.dynamodb.conditions import Key

from app.core.config import config
from app.core.context import Context
from app.core.exceptions import NotFoundError
from app.core.permissions import validate_permissions
from app.db import Table
from app.model.post_model import Post
from app.service.membership_service import MembershipService
from app.service.notification_service import NotificationService
from app.utils.ids import generate_uuid
from app.utils.time import get_current_time


class PostService:
    def __init__(self):
        self.db = Table(
            table_name=config.posts_table_name, aws_region=config.aws_region
        )
        self.membership_service = MembershipService()
        self.notification_service = NotificationService()

    @staticmethod
    def _build_post(**kwargs) -> Post:
        current_time = get_current_time()
        return Post(
            id=kwargs.get("id", generate_uuid()),
            author_id=kwargs["author_id"],
            location_id=kwargs["location_id"],
            title=kwargs["title"],
            content=kwargs["content"],
            created_at=kwargs.get("created_at", current_time),
            updated_at=kwargs.get("updated_at", current_time),
            deleted_at=kwargs.get("deleted_at", None),
        )

    @staticmethod
    def _serialize_post(post: Post) -> dict:
        item = post.model_dump()
        return item

    def create_post(
        self, context: Context, location_id: str, title: str, content: str
    ) -> Post:
        validate_permissions(context.user_id, location_id, "post:create")

        post = self._build_post(
            author_id=context.user_id,
            location_id=location_id,
            title=title,
            content=content,
        )
        item = self._serialize_post(post)
        self.db.put_item(item=item)

        # Notify location members about new post
        location_memberships = self.membership_service.get_location_memberships(
            location_id
        )
        recipient_user_ids = [membership.user_id for membership in location_memberships]
        self.notification_service.notify(
            recipient_user_ids,
            item["title"],
            item["content"],
            {
                "type": "NEW_POST",
                "post_id": item["id"],
                "location_id": item["location_id"],
            },
        )
        return item

    def get_post_by_id(
        self, context: Context, post_id: str, include_deleted: bool = False
    ) -> Post | None:
        key = {"id": post_id}
        item = self.db.get_item(key)
        if not item:
            raise NotFoundError("Post not found")
        if item.get("deleted_at") and not include_deleted:
            raise NotFoundError("Post not found")

        validate_permissions(context.user_id, item.get("location_id"), "post:read")

        return Post.model_validate(item)

    def get_posts_by_location_id(
        self, context: Context, location_id: str, include_deleted: bool = False
    ) -> list[Post]:
        validate_permissions(context.user_id, location_id, "post:read")

        key_expression = Key("location_id").eq(location_id)
        items = self.db.query_gsi(
            index_name="location-created_at-index",
            key_expression=key_expression,
        )
        if not include_deleted:
            items = [item for item in items if not item.get("deleted_at")]
        return items

    def update_post(self, context: Context, post_id: str, **kwargs) -> Post | None:
        key = {"id": post_id}
        item = self.db.get_item(key)

        # Verify item exists
        if not item or item.get("deleted_at"):
            raise NotFoundError("Post not found")

        is_owner = item.get("author_id") == context.user_id
        validate_permissions(
            context.user_id, item.get("location_id"), "post:update", is_owner
        )

        # Return early if no attributes are provided
        if all(value is None for value in kwargs.values()):
            return Post.model_validate(item)

        # Set updated_at timestamp
        update_expression = "SET #updated_at = :updated_at"
        names = {"#updated_at": "updated_at"}
        values = {":updated_at": get_current_time()}

        if kwargs.get("title"):
            update_expression += ", #title = :title"
            names["#title"] = "title"
            values[":title"] = kwargs["title"]
        if kwargs.get("content"):
            update_expression += ", #content = :content"
            names["#content"] = "content"
            values[":content"] = kwargs["content"]

        updated_item = self.db.update_item(
            key=key,
            update_expression=update_expression,
            attr_names=names,
            attr_values=values,
        )
        return Post.model_validate(updated_item)

    def delete_post(self, context: Context, post_id: str):
        key = {"id": post_id}

        item = self.db.get_item(key)
        # Verify item exists and is not already deleted
        if not item or item.get("deleted_at"):
            raise NotFoundError("Post not found")

        is_owner = item.get("author_id") == context.user_id
        validate_permissions(
            context.user_id, item.get("location_id"), "post:delete", is_owner
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
        return Post.model_validate(updated_item)
