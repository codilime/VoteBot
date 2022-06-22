from unittest import mock

from django.apps import apps
from django.test import TestCase

from bot_app.apps import BotAppConfig
from bot_app.models import SlackUser, Vote


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
