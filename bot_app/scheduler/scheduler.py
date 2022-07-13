import threading
import time

import schedule

from bot_app.scheduler.jobs import send_periodic_messages, notify_about_new_points, create_users_from_slack


class Scheduler:
    """ This class handles scheduling events, like sending periodic texts. It runs scheduler in the background
    as a separate thread, not blocking the main app. It will run scheduled jobs, but only if main app is running.
    Will not rerun any missed jobs if app was down.

    If app was to run in multiple containers there might be a need to move Scheduler elsewhere,
    to run completely independently form the main app, so jobs aren't run multiple times. """
    _thread: threading.Thread
    _stop_thread_event: threading.Event

    def __init__(self, check_rate: int = 60) -> None:
        """ @param check_rate: interval in seconds, how often scheduler checks if any job should be run. """
        self._scheduler = schedule.Scheduler()

        self._stop_thread_event = threading.Event()
        self._thread = self.SchedulerThread(
            scheduler=self._scheduler, check_rate=check_rate, stop_event=self._stop_thread_event
        )
        self._thread.daemon = True  # Die if main app exits.

    class SchedulerThread(threading.Thread):
        def __init__(
                self, scheduler: schedule.Scheduler, check_rate: int, stop_event: threading.Event, *args, **kwargs
        ):
            super().__init__(*args, **kwargs)

            self._scheduler = scheduler
            self._check_rate = check_rate
            self._stop_event = stop_event

        def run(self):
            while not self._stop_event.is_set():
                self._scheduler.run_pending()
                time.sleep(self._check_rate)

    def run(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_thread_event.set()

    def every(self, interval: int = 1) -> schedule.Job:
        """ This method exists to ensure original schedule's interface for settings jobs. """
        return self._scheduler.every(interval=interval)


def schedule_jobs(scheduler: Scheduler) -> None:
    """ This func schedules any jobs that app should be doing in the background.
    How to schedule a new job: https://schedule.readthedocs.io/en/stable/examples.html"""
    scheduler.every().day.at("10:00").do(create_users_from_slack)
    scheduler.every().day.at("10:00").do(send_periodic_messages)
    scheduler.every().day.at("16:00").do(notify_about_new_points)
