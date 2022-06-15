from django.apps import AppConfig
from django.conf import settings

from bot_app.client import SlackClient


class BotAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bot_app"
    slack_client: SlackClient

    def ready(self) -> None:
        self.slack_client = SlackClient(token=settings.SLACK_BOT_TOKEN)
