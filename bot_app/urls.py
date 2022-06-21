from django.urls import path

from .events import slack_events
from .interactive import interactive
from .slash import (
    vote,
    check_votes,
    check_points,
    check_winners,
    about,
)

urlpatterns = [
    path("about", about, name="about"),
    path("vote", vote, name="vote"),
    path("check-votes", check_votes, name="check_votes"),
    path("check-points", check_points, name="check_points"),
    path("check-winners", check_winners, name="check_winner_month"),

    path("interactive", interactive, name="interactive"),
    path("event/hook/", slack_events, name="slack_events"),
]
