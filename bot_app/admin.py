from django.contrib import admin

from bot_app.models import SlackUser, Vote

admin.site.register(SlackUser)
admin.site.register(Vote)
