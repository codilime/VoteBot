from django.test import TestCase

from bot_app.texts import TextsSources, TextsBuilder


class TestTexts(TestCase):
    def setUp(self) -> None:
        sources = TextsSources()
        self.builder = TextsBuilder(sources=sources)

    def test_user_comments(self) -> None:
        # Given
        user = 'Jan Kowalski'
        comments = {
            'Anna Nowak': "Comment about user",
            'Paweł Kowalski': "Another comment about a user",
        }

        expected_header = f"Comments given to user {user} in current half of year:\n"
        expected_lines = '\n'.join([f'• {user}: {comment}' for user, comment in comments.items()])
        expected = expected_header + expected_lines

        # When
        text = self.builder.user_comments(user=user, comments=comments)

        # Then
        assert text == expected

    def test_top5(self) -> None:
        # Given
        category = 'Category 1'
        users_points = [('Jan Kowalski', 7), ('Anna Nowak', 4), ('Paweł Kowalski', 1)]

        expected_header = f"Top 5 Limes in category {category} in a current half of year:\n"
        expected_lines = '\n'.join([f'• {user} with {points} points' for user, points in users_points])
        expected = expected_header + expected_lines

        # When
        text = self.builder.top5(category=category, users_points=users_points)

        # Then
        assert text == expected
