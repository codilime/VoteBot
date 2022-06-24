# CodiLime's vote bot for [Slack](https://slack.com)

This bot allows to grant points to other users. Points can be granted in 3 categories,
accordingly to CodiLime's Manifesto:
- Team up to win
- Act to deliver
- Disrupt to grow

## TODO:
- Greeting in every message is irritating...
- Draws are not handled in any way (print all of them in message)
- Templates work only with DEBUG=True (is this some django quirk?)
- Split dependencies to prod and dev, preferably use [poetry](https://github.com/python-poetry/poetry)
- CI/CD
- Deploy to test environment

## Running tests
You need virtual env set, and requirements installed, and everything should just run. 
Without the `.env` file, Slack API configuration, or rest of this readme:
```
python manage.py test
```
To check tests coverage run:
```
coverage run --source='./bot_app' manage.py test --verbosity=3 && coverage report -m
```

## Running app
### Before the first run:
- You'll need a Slack workspace to work on with your instance of bot. You can create a new one or invite yourself to our [test workspace](https://join.slack.com/t/programwyrniebot/shared_invite/zt-1ac7mt2iu-1VCqoLW6sHnave~Jur8AeQ).
- Create account on [Slack API](https://api.slack.com/), create a new app from scratch, pick a workspace on which you want to install your app.
- Go to ***OAuth & Permissions*** and set bellow scopes in ***Bot Token Scopes***:
```
channels:history
chat:write
commands
users:read
```
- Scroll up and click ***Install to Workspace***, after installation you should receive ***Bot User OAuth Token*** in `xoxb-...` format
- After that you can either run app locally or from Docker container.

### Local run
- Create new, empty PostgreSQL database
- In project's root create `.env` file:
```
SECRET_KEY=[django secret key, unique and unpredictable value, whatever you come up with]
DB_URL=your database url in postgres://USER:PASSWORD@127.0.0.1:5432/DATABASE format

SIGNING_SECRET=[Signing Secret from Slack API -> Basic Information -> App Credentials section]
SLACK_BOT_TOKEN=[xoxb Bot User OAuth Token from Slack API -> Install App section]

ENABLE_SCHEDULER=0    # Enable for production.
DEBUG=1    # Disable for production.
```
- With all that completed you should be able to run migrations and start the app:
```shell
python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
```
- App should start, but for full functionality you'll have to [set up endpoints in Slack API](#endpoints).

### Docker run
- In project's root create `.env` file:
```
SECRET_KEY=[django secret key, unique and unpredictable value, whatever you come up with]
DB_URL=postgres://postgres:postgres@db:5432/DATABASE  # URL to db container.

SIGNING_SECRET=[Signing Secret from Slack API -> Basic Information -> App Credentials section]
SLACK_BOT_TOKEN=[xoxb Bot User OAuth Token from Slack API -> Install App section]

ENABLE_SCHEDULER=0    # Enable for production.
```
- If it's the first run, or you removed `database` volume you have to migrate DB and create superuser first:
```
docker-compose run --entrypoint python vote-bot manage.py migrate
docker-compose run --entrypoint python vote-bot manage.py createsuperuser
```
- After that use `docker-compose up` command to run the containers
- App should start, but for full functionality you'll have to [set up endpoints in Slack API](#endpoints).

## Endpoints
Endpoints to handle user's slash commands:
``` 
/about - information about the awards program
/vote - show voting form
/check-votes - check your previous votes from this month 
/check-points - check points you received this month
/check-winners - check this month's winner, if you have permissions
```
Other endpoints, required for app's functionality:
```
/interactive - handle interactions with modals, buttons, etc., in our case receive subbmited voting modal
/event/hook/ - handle miscellaneous events, like somebody mentioning our awards program in a message
```
### Local proxy
For all of this to work our app has to be visible to the world (and Slack API). To achieve that Slack documentation recommends 
[to use Ngrok as a local proxy](https://api.slack.com/start/building/bolt-python#ngrok).
Only change being to run it on the same port that our app is running now (probably `8000`).   
Having forwarded ngrok URL from `https://abcd-01-23-45-678.eu.ngrok.io` to our machine we can set up endpoints in the Slack API.

### Slash commands
For slash commands to work you have to create each command in the ***Slash Commands*** tab. 
Any commands that were not added will not work. To add `/about` command you'd have to set it up like this:
```
Command: /about
Request URL: https://abcd-01-23-45-678.eu.ngrok.io/about
Short description: Description of awards program.
```
![Setting slash commands](readme/slash_commands.png)

### Interactive (receiving votes)
To enable voting you have to set up `/vote` slash command and enable interactivity for your app.
To enable interactivity you have to go to ***Interactivity & Shortcuts*** tab, toggle the switch
and add your local proxy endpoint: `https://abcd-01-23-45-678.eu.ngrok.io/interactive`
![Adding interactivity](readme/interactive.png)

### Events (reacting for messages)
To enable events you have to go to ***Events Subscriptions*** tab, toggle the switch
and add your local proxy endpoint: `https://abcd-01-23-45-678.eu.ngrok.io/event/hook/`. 
App has to be running to allow Slack to check the endpoint, and **trailing slash is important!**  
After that you'll have to add new event `message.channels` in ***Subscribe to bot events*** and save changes.
![Enabling events](readme/events.png)

## Scheduler
App has a scheduler that is responsible for running periodic jobs. It can send reminders, announce winners, sync users
from slack, and so on. It's running in separate thread to not block the main application.    
Scheduler's jobs can be edited in the `bot_app/scheduler/scheduler.py` file, in the `schedule_jobs` function.   
Scheduler is disabled for development by default, but it should be enabled on production environment. 
Set `ENABLE_SCHEDULER=1` environmental variable to enable the scheduler.

## Checking this month's winner
To check winners for current month use `/check-winners` slash command. Additionally, there is a job scheduled
that will automatically post message about winners on the last day of the month.  
Although to be possible for user to receive that message the checkbox `is hr` in the `/admin` has to be selected 
for that user. Otherwise, the user will receive message about lacking the permissions to check winners.   
![is_hr checkbox](readme/is_hr.png)
