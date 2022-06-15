from django.test import TestCase
from parameterized import parameterized


class TestInvalidMethod(TestCase):
    @parameterized.expand((
            '/about',
            '/vote',
            '/interactive',
            '/check-votes',
            '/check-points',
            '/check-winner-month',
            '/event/hook/',
    ))
    def test_method(self, url: str) -> None:
        response = self.client.get(url)
        assert response.status_code == 405
