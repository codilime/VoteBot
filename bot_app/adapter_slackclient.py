import logging
from pyee import EventEmitter
from slack_sdk import WebClient
from django.conf import settings


logging.getLogger().setLevel(logging.INFO)


SLACK_VERIFICATION_TOKEN = settings.SLACK_VERIFICATION_TOKEN
SLACK_BOT_TOKEN = settings.SLACK_BOT_TOKEN


CLIENT = WebClient(SLACK_BOT_TOKEN)


class SlackEventAdapter(EventEmitter):
    def __init__(self, verification_token):
        EventEmitter.__init__(self)
        self.verification_token = verification_token


slack_events_adapter = SlackEventAdapter(SLACK_VERIFICATION_TOKEN)


# # Example reaction emoji echo
# @slack_events_adapter.on("reaction_added")
# def reaction_added(event_data):
#     event = event_data["event"]
#     emoji = event["reaction"]
#     channel = event["item"]["channel"]
#     text = ":%s:" % emoji
#     logging.info("chat.postMessage: channel: %s text: %s" % (channel, text))
#     CLIENT.api_call("chat.postMessage", channel=channel, text=text)
