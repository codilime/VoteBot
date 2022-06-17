from django.apps import AppConfig
from django.conf import settings

from bot_app.client import SlackClient


class BotAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bot_app"
    slack_client: SlackClient

    def ready(self) -> None:
        self.slack_client = SlackClient(token=settings.SLACK_BOT_TOKEN)

        from bot_app.scrap_users import create_users_from_slack
        create_users_from_slack()

        if settings.ENABLE_SCHEDULER:
            from bot_app.scheduler.scheduler import Scheduler, schedule_jobs
            schedule = Scheduler()
            schedule_jobs(scheduler=schedule)
            schedule.run()
