from django.urls import path

from bot_app.views.events import slack_event
from bot_app.views.index import index
from bot_app.views.interactive import interactive
from bot_app.views.slash import vote, check_comments, check_votes, check_points, check_winners, about, check_top5

urlpatterns = [
    path("", index, name="index"),

    path("about", about, name="about"),
    path("vote", vote, name="vote"),
    path("check-comments", check_comments, name="check_comments"),
    path("check-votes", check_votes, name="check_votes"),
    path("check-points", check_points, name="check_points"),
    path("check-winners", check_winners, name="check_winner_month"),
    path("check-top5",  check_top5, name="check_top5_month"),
    path("interactive", interactive, name="interactive"),
    path("event/hook/", slack_event, name="slack_events"),
]
