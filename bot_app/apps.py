import sys

from django.apps import AppConfig
from django.conf import settings

from bot_app.slack.client import SlackClient


class BotAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bot_app"
    slack_client: SlackClient

    def ready(self) -> None:
        self.slack_client = SlackClient(token=settings.SLACK_BOT_TOKEN)

        if 'runserver' not in str(sys.argv) or 'gunicorn' not in str(sys.argv):
            # Skip users sync and scheduler if server is not starting.
            return

        # Sync users from slack on the startup.
        from bot_app.scheduler.jobs import create_users_from_slack
        create_users_from_slack()

        # Run scheduler only if settings say so.
        if settings.ENABLE_SCHEDULER:
            from bot_app.scheduler.scheduler import Scheduler, schedule_jobs
            schedule = Scheduler()
            schedule_jobs(scheduler=schedule)
            schedule.run()
