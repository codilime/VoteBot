import calendar
import time
from datetime import datetime
from unittest import mock

from django.test import TestCase, override_settings

from bot_app.models import SlackUser, VotingResults
from bot_app.scheduler.jobs import remind_about_program, announce_winners, send_periodic_messages, \
    notify_about_new_points
from bot_app.scheduler.scheduler import Scheduler
from bot_app.texts import texts
from tests.base import BaseTestCase


class TestScheduler(TestCase):
    def test_scheduler(self) -> None:
        scheduler = Scheduler(check_rate=1)

        func = mock.MagicMock()
        scheduler.every().second.do(func)
        assert func.call_count == 0

        scheduler.run()
        assert scheduler._thread.is_alive() is True

        time.sleep(3)  # Wait for scheduler to call the func.
        scheduler.stop()
        time.sleep(3)  # Wait for scheduler to stop.

        assert scheduler._thread.is_alive() is False
        assert func.call_count > 0


class TestSchedulerJobs(BaseTestCase):
    def setUp(self) -> None:
        self._mock_slack_client()
        self._add_simple_test_data()

    def test_reminder(self) -> None:
        remind_about_program()
        assert self.slack_client_mock.chat_postMessage.call_count == SlackUser.objects.count()

        text = texts.remind_about_program()
        calls = [c[1] for c in self.slack_client_mock.chat_postMessage.call_args_list]
        users_reminded = [c['channel'] for c in calls]
        assert users_reminded == [u.slack_id for u in SlackUser.objects.all()]
        assert all([text in c['text'] for c in calls])

    @override_settings(HR_USERS=['test.user.1', 'other.user'])
    def test_announce_winners(self) -> None:
        winners_text = f"""Wyniki głosowania w programie wyróżnień:
W kategorii Team up to win mając {self.voting_result.points_team_up_to_win} głosów wygrywa {self.slack_user1.profile.real_name}.
W kategorii Act to deliver mając {self.voting_result.points_act_to_deliver} głosów wygrywa {self.slack_user2.profile.real_name}.
W kategorii Disrupt to grow mając {self.voting_result.points_disrupt_to_grow} głosów wygrywa {self.slack_user2.profile.real_name}."""

        announce_winners()
        assert self.slack_client_mock.chat_postMessage.call_count == 1

        call = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call['channel'] == self.slack_user1.slack_id
        assert call['text'] == winners_text

    @mock.patch('bot_app.scheduler.jobs.announce_winners')
    @mock.patch('bot_app.scheduler.jobs.remind_about_program')
    def test_send_periodic_messages(self, reminder: mock.MagicMock, announcer: mock.MagicMock) -> None:
        today = datetime.now()
        last_day_of_month = calendar.monthrange(today.year, today.month)[1]

        with mock.patch('bot_app.scheduler.jobs.datetime') as dt:
            dt.now.return_value = today.replace(day=last_day_of_month)
            send_periodic_messages()

        assert reminder.call_count == 0
        assert announcer.call_count == 1

        with mock.patch('bot_app.scheduler.jobs.datetime') as dt:
            dt.now.return_value = today.replace(day=last_day_of_month - 1)
            send_periodic_messages()

        assert reminder.call_count == 1
        assert announcer.call_count == 1

    def test_new_points_notification(self) -> None:
        got_voted_text = f"""{VotingResults.objects.count()} osób zagłosowało dzisiaj na Ciebie! Sumarycznie przyznali Ci:
{self.voting_result.points_team_up_to_win} punktów w kategorii Team up to win.
{self.voting_result.points_act_to_deliver} punktów w kategorii Act to deliver.
{self.voting_result.points_disrupt_to_grow} punktów w kategorii Disrupt to grow."""

        notify_about_new_points()
        assert self.slack_client_mock.chat_postMessage.call_count == VotingResults.objects.count()

        call = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call['channel'] == self.slack_user2.slack_id
        assert call['text'] == got_voted_text
