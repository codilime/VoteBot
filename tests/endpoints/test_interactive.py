import json
import urllib.parse

from django.test import override_settings

from bot_app.models import Vote
from tests.base import BaseTestCase, get_signature_headers


def get_sent_vote_modal(
        voting_user: str,
        voted_user: str,
        points_team_up_to_win: int,
        points_act_to_deliver: int,
        points_disrupt_to_grow: int,
) -> dict:
    return {
        "type": "view_submission",
        "user": {
            "id": voting_user,
        },
        "view": {
            "state": {
                "values": {
                    "select_user": {
                        "select_user-action": {"selected_user": voted_user}
                    },
                    "points_team_up_to_win": {
                        "points_team_up_to_win-action": {
                            "selected_option": {
                                "text": {
                                    "text": str(points_team_up_to_win),
                                },
                            }
                        }
                    },
                    "points_act_to_deliver": {
                        "points_act_to_deliver-action": {
                            "selected_option": {
                                "text": {
                                    "text": str(points_act_to_deliver),
                                },
                            }
                        }
                    },
                    "points_disrupt_to_grow": {
                        "points_disrupt_to_grow-action": {
                            "selected_option": {
                                "text": {
                                    "text": str(points_disrupt_to_grow),
                                },
                            }
                        }
                    },
                }
            },
        },
    }


@override_settings(SIGNING_SECRET='signing_secret')
class TestInteractiveEndpoint(BaseTestCase):
    url = "/interactive"

    def setUp(self) -> None:
        self._mock_slack_client()
        self._add_simple_test_data(add_voting=False)

    def test_vote(self) -> None:
        # Save new vote.
        points_team_up_to_win = 0
        points_act_to_deliver = 1
        points_disrupt_to_grow = 2

        vote_modal = get_sent_vote_modal(
            voting_user=self.slack_user1.slack_id,
            voted_user=self.slack_user2.slack_id,
            points_team_up_to_win=points_team_up_to_win,
            points_act_to_deliver=points_act_to_deliver,
            points_disrupt_to_grow=points_disrupt_to_grow,
        )

        with self.assertRaises(Vote.DoesNotExist):
            Vote.objects.latest("created")

        data = {"payload": json.dumps(vote_modal)}
        data = urllib.parse.urlencode(data)
        response = self.client.post(
            self.url,
            data=data,
            content_type='application/x-www-form-urlencoded',
            **get_signature_headers(data=data)
        )
        assert response.status_code == 200

        vote = Vote.objects.latest("created")
        assert vote.voting_user == self.slack_user1
        assert vote.voted_user == self.slack_user2
        assert vote.points_team_up_to_win == points_team_up_to_win
        assert vote.points_act_to_deliver == points_act_to_deliver
        assert vote.points_disrupt_to_grow == points_disrupt_to_grow

        # Update vote.
        points_team_up_to_win = 3
        points_act_to_deliver = 0
        points_disrupt_to_grow = 0

        vote_modal = get_sent_vote_modal(
            voting_user=self.slack_user1.slack_id,
            voted_user=self.slack_user2.slack_id,
            points_team_up_to_win=points_team_up_to_win,
            points_act_to_deliver=points_act_to_deliver,
            points_disrupt_to_grow=points_disrupt_to_grow,
        )

        data = {"payload": json.dumps(vote_modal)}
        data = urllib.parse.urlencode(data)
        response = self.client.post(
            self.url,
            data=data,
            content_type='application/x-www-form-urlencoded',
            **get_signature_headers(data=data)
        )
        assert response.status_code == 200
        assert len(Vote.objects.all()) == 1

        vote = Vote.objects.latest("created")
        assert vote.voting_user == self.slack_user1
        assert vote.voted_user == self.slack_user2
        assert vote.points_team_up_to_win == points_team_up_to_win
        assert vote.points_act_to_deliver == points_act_to_deliver
        assert vote.points_disrupt_to_grow == points_disrupt_to_grow
        assert vote.created != vote.modified
