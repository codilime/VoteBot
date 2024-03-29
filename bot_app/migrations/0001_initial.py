# Generated by Django 4.0.4 on 2022-06-23 11:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SlackUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slack_id', models.CharField(max_length=64, unique=True)),
                ('name', models.CharField(max_length=128)),
                ('real_name', models.CharField(max_length=128)),
                ('is_hr', models.BooleanField(default=False, help_text='Can see winners of each month.')),
                ('is_bot', models.BooleanField(default=False)),
                ('deleted', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points_team_up_to_win', models.IntegerField(default=0)),
                ('points_act_to_deliver', models.IntegerField(default=0)),
                ('points_disrupt_to_grow', models.IntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('voted_user', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='voted_user', to='bot_app.slackuser')),
                ('voting_user', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='voting_user', to='bot_app.slackuser')),
            ],
        ),
    ]
