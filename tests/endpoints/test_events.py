import json

from django.test import override_settings

from bot_app.slack.events import KEYWORDS
from bot_app.models import SlackUser
from tests.base import BaseTestCase, get_signature_headers
from tests.data import get_text_from_file


@override_settings(SIGNING_SECRET='signing_secret')
class TestEventEndpoint(BaseTestCase):
    url = '/event/hook/'
    token = 'very_important_slack_token'

    def setUp(self) -> None:
        self._mock_slack_client()
        self.slack_user1 = SlackUser.objects.create(slack_id="slack_user1_id", name="test.user.1")

    def test_slack_api_challenge(self) -> None:
        challenge = 'slack_challenge'
        event_data = {'token': self.token, 'challenge': challenge, 'type': 'url_verification'}
        data = json.dumps(event_data)

        response = self.client.post(
            self.url,
            data=data,
            content_type='application/json',
            **get_signature_headers(data=data)
        )
        assert response.status_code == 200

        data = response.json()
        assert data['challenge'] == challenge

    def test_keyword_event(self) -> None:
        channel = 'some_channel_id'
        thread = 'some_thread_id'
        text = KEYWORDS[0]
        event_data = {
            'token': self.token,
            'event': {
                'type': 'message',
                'text': text,
                'user': self.slack_user1.slack_id,
                'ts': thread,
                'channel': channel,
                'channel_type': 'group'
            },
            'type': 'event_callback',
        }
        data = json.dumps(event_data)
        text = get_text_from_file(filename='about')

        response = self.client.post(
            self.url,
            data=data,
            content_type='application/json',
            **get_signature_headers(data=data)
        )
        assert response.status_code == 200

        assert self.slack_client_mock.chat_postMessage.call_count == 2
        call_args = self.slack_client_mock.chat_postMessage.call_args_list

        args = call_args[0][1]
        assert args['channel'] == channel
        assert args['thread_ts'] == thread

        args = call_args[1][1]
        assert args['channel'] == self.slack_user1.slack_id
        content = [c.get('text', {}).get('text') for c in args['blocks']]
        assert text in content

    def test_invalid_data(self) -> None:
        data = 'This is not a json.'

        response = self.client.post(
            self.url,
            data=data,
            content_type='application/json',
            **get_signature_headers(data=data)
        )
        assert response.status_code == 400

    def test_invalid_token(self):
        event_data = {
            'token': 'definitely_not_a_valid_token',
            'event': {},
        }
        data = json.dumps(event_data)

        response = self.client.post(
            self.url,
            data=data,
            content_type='application/json',
            **get_signature_headers(data=data)
        )
        assert response.status_code == 400

    def test_invalid_event(self):
        event_data = {
            'token': self.token,
            'not_an_event': True,
        }
        data = json.dumps(event_data)

        response = self.client.post(
            self.url,
            data=data,
            content_type='application/json',
            **get_signature_headers(data=data)
        )
        assert response.status_code == 400
