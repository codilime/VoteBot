from django.urls import path
from .reminders import *
from .events import slack_events
from .slash import (
    vote,
    interactive,
    check_votes,
    check_points,
    check_winner_month,
    about,
)

app_name = "bot_app"

urlpatterns = [
    path("event/hook/", slack_events, name="slack_events"),
    path("about", about, name="about"),
    path("vote", vote, name="vote"),
    path("interactive", interactive, name="interactive"),
    path("check-votes", check_votes, name="check_votes"),
    path("check-points", check_points, name="check_points"),
    path("check-winner-month", check_winner_month, name="check_winner_month"),
]
