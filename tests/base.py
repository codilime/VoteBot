import time
from typing import Any
from unittest import mock

from django.apps import apps
from django.test import TestCase

from bot_app.apps import BotAppConfig
from bot_app.hmac import hash_data
from bot_app.models import SlackUser
from bot_app.models import Vote


class BaseTestCase(TestCase):
    def _mock_slack_client(self) -> None:
        self.slack_client_mock = mock.MagicMock()
        apps.get_app_config(BotAppConfig.name).slack_client._client = self.slack_client_mock

    def _add_simple_test_data(self, add_voting: bool = True) -> None:
        self.slack_user1 = SlackUser.objects.create(slack_id="slack_user1_id", name="test.user.1")
        self.slack_user2 = SlackUser.objects.create(slack_id="slack_user2_id", name="test.user.2")

        if add_voting:
            self.voting_result = Vote.objects.create(
                voted_user=self.slack_user2,
                voting_user=self.slack_user1,
                points_team_up_to_win=0,
                points_act_to_deliver=1,
                points_disrupt_to_grow=2,
            )


def get_signature_headers(data: Any) -> dict:
    timestamp = int(time.time())
    hash_string = f'v0:{timestamp}:{data}'
    signature = f'v0={hash_data(data=hash_string)}'
    return dict(
        HTTP_X_Slack_Request_Timestamp=timestamp,
        HTTP_X_Slack_Signature=signature,
    )
