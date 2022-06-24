import logging

from slack_sdk import WebClient
from slack_sdk.web import SlackResponse


class SlackClient:
    _bot_id: str = None

    def __init__(self, token: str) -> None:
        self._token = token
        self._client = WebClient(token=self._token)
        self._client._logger.setLevel(level=logging.INFO)  # It's DEBUG by default for some reason.

    @property
    def bot_id(self) -> str:
        if not self._bot_id:
            self._bot_id = self._client.api_call("auth.test")["user_id"]
        return self._bot_id

    def open_view(self, trigger_id: str, view: dict) -> SlackResponse:
        return self._client.views_open(trigger_id=trigger_id, view=view)

    def post_chat_message(self, message: dict, text: str) -> SlackResponse:
        return self._client.chat_postMessage(**message, text=text)

    def users_list(self) -> SlackResponse:
        return self._client.users_list()
