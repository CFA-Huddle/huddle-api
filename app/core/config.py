import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    app_name: str = "Huddle"
    environment: str = os.getenv("ENVIRONMENT", "dev")
    aws_region: str = os.getenv("AWS_REGION", "us-east-2")
    cognito_user_pool_id: str = os.getenv("COGNITO_USER_POOL_ID")

    @property
    def jwks_uri(self):
        return f"https://cognito-idp.{self.aws_region}.amazonaws.com/{self.cognito_user_pool_id}/.well-known/jwks.json"

    @property
    def profile_picture_bucket_name(self):
        return f"{self.environment}-huddle-profile-pictures"

    # Database Configuration
    @property
    def posts_table_name(self):
        return f"{self.environment}-huddle-posts"

    @property
    def memberships_table_name(self):
        return f"{self.environment}-huddle-memberships"

    @property
    def training_modules_table_name(self):
        return f"{self.environment}-huddle-training-modules"


config = Config()
