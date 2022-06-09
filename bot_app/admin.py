from django.contrib import admin
from .models import SlackProfile, SlackUser, VotingResults


admin.site.register(SlackProfile)
admin.site.register(SlackUser)
admin.site.register(VotingResults)
