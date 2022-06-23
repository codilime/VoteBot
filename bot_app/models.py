from django.db import models

CATEGORIES = {
    'points_team_up_to_win': "Team up to win",
    "points_act_to_deliver": "Act to deliver",
    "points_disrupt_to_grow": "Disrupt to grow",
}


class SlackUser(models.Model):
    slack_id = models.CharField(unique=True, max_length=64)
    name = models.CharField(max_length=128)
    real_name = models.CharField(max_length=128)
    is_hr = models.BooleanField(default=False, help_text="Can see winners of each month.")
    is_bot = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.SmallIntegerField(default=0)

    def __str__(self):
        return f"{self.slack_id} {self.name}"


class Vote(models.Model):
    voting_user = models.ForeignKey(SlackUser, on_delete=models.RESTRICT, related_name="voting_user")
    voted_user = models.ForeignKey(SlackUser, on_delete=models.RESTRICT, related_name="voted_user")
    points_team_up_to_win = models.IntegerField(default=0)
    points_act_to_deliver = models.IntegerField(default=0)
    points_disrupt_to_grow = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Class: {self.__class__.__name__}, user: {self.voting_user}."
