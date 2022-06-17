import json
from unittest import mock

from bot_app.models import VotingResults
from tests.base import BaseTestCase


class TestInteractiveEndpoint(BaseTestCase):
    url = "/interactive"
    token = "very_important_slack_token"

    def setUp(self) -> None:
        self._mock_slack_client()
        self._add_simple_test_data(add_voting=False)

    @mock.patch("bot_app.events.SLACK_VERIFICATION_TOKEN", token)
    def test_vote(self) -> None:
        vote_modal = {
            "type": "view_submission",
            "user": {
                "id": self.slack_user1.slack_id,
                "username": self.slack_user1.name,
                "name": self.slack_user1.name,
                "team_id": "team_id",
            },
            "token": self.token,
            "view": {
                "blocks": [
                    {
                        "type": "section",
                        "block_id": "K0I",
                    },
                    {
                        "type": "input",
                        "block_id": "field1",
                    },
                    {
                        "type": "input",
                        "block_id": "field2",
                    },
                    {
                        "type": "input",
                        "block_id": "field3",
                    },
                    {
                        "type": "input",
                        "block_id": "field4",
                    },
                    {"type": "divider", "block_id": "CBb"},
                    {
                        "type": "context",
                        "block_id": "MkQ",
                    },
                ],
                "state": {
                    "values": {
                        "field1": {
                            "user_select-action": {
                                "type": "users_select",
                                "selected_user": self.slack_user2.slack_id,
                            }
                        },
                        "field2": {
                            "static_select-action": {
                                "type": "static_select",
                                "selected_option": {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "0",
                                        "emoji": True,
                                    },
                                    "value": "value-0",
                                },
                            }
                        },
                        "field3": {
                            "static_select-action": {
                                "type": "static_select",
                                "selected_option": {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "2",
                                        "emoji": True,
                                    },
                                    "value": "value-2",
                                },
                            }
                        },
                        "field4": {
                            "static_select-action": {
                                "type": "static_select",
                                "selected_option": {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "1",
                                        "emoji": True,
                                    },
                                    "value": "value-1",
                                },
                            }
                        },
                    }
                },
            },
        }

        with self.assertRaises(VotingResults.DoesNotExist):
            VotingResults.objects.latest("created")

        response = self.client.post(self.url, data={"payload": json.dumps(vote_modal)})
        assert response.status_code == 200

        vote = VotingResults.objects.latest("created")
        assert vote.voting_user_id == self.slack_user1
        assert vote.voted_user == self.slack_user2
        assert vote.points_team_up_to_win == 0
        assert vote.points_act_to_deliver == 2
        assert vote.points_disrupt_to_grow == 1

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["text"] == "Check your votes."  # TODO move to common var
        assert call_args["channel"] == self.slack_user1.slack_id

        msg = str(call_args["blocks"][1])
        assert self.slack_user2.name in msg
        assert f"Team up to win przyznano {vote.points_team_up_to_win}" in msg
        assert f"Act to deliver przyznano {vote.points_act_to_deliver}" in msg
        assert f"Disrupt to grow przyznano {vote.points_disrupt_to_grow}" in msg
