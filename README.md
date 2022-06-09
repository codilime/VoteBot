A [Slack](https://slack.com) vote bot.


## Usage

### Generate the slack api token

First you need to get the slack api token for your bot. You have two options:

1. If you use a [bot user integration](https://api.slack.com/bot-users) of slack, you can get the api token on the integration page.
2. If you use a real slack user, you can generate an api token on [slack web api page](https://api.slack.com/web). You can find the token in the Basic Information tab.

![alt text](https://github.com/codilime/VoteBot/blob/r_buczynski/slack%202.png)

### Configure the bot
First create a `.env` file in your own instance of slackbot.

#### Complete the file as below:


Then you need to configure the `TOKENS` in a `.env` file, which must be located in a main directory. This will be automatically used by the bot.

.env:
```
SECRET_KEY=<django-secret-key>
SLACK_BOT_TOKEN=<your-slack-token>
SIGNING_SECRET=<your-key>
SLACK_VERIFICATION_TOKEN=<your-slack-verification-token>
```


### Setup - type in terminal

```commandline
git clone https://github.com/codilime/VoteBot.git
py manage.py -m venv venv  
cd .\venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
```

### Run django app
```commandline
python manage.py runserver
```

### Configure base URL
You need login to [spack api panel](https://api.slack.com/apps) and change base url for endpoints. 
Change base url in categories. You can use Ngrok to generate url for tests. 
![alt text](https://github.com/codilime/VoteBot/blob/r_buczynski/slack%201.png)


### Endpoints for Slash Commands
```commandline
    /vote - Type '/vote' to receive a form where you can vote in the award program.
    /about - Type '/about' to receive information about the awards program.
    /check-votes - Type '/check-votes' to check how you voted. 
    /check-points - Type '/check-points' to know how many points you have received.
    /check-winner-month - Type '/check-winner-month' to know who win award program in current month.
```
You can manage slash method in the Slash Commands tab.
![alt text](https://github.com/codilime/VoteBot/blob/r_buczynski/slack%203.png)


### Endpoints for Event Subscriptions
```commandline
    /event/hook/ - is a url using for handle events on slack chanels. 
    It is possible to change the scope of permissions in the slack api panel. 
    All events is handle by one url. 
    Your app can subscribe to be notified of events in Slack (for example, 
    when a user adds a reaction or creates a file) at a URL you choose.
```
Remember to enable events on slack api page.
![alt text](https://github.com/codilime/VoteBot/blob/r_buczynski/slack%204.png)


### Endpoints for Interactivity & Shortcuts
```commandline
    /interactive - Interactivity - Any interactions with shortcuts, 
    modals, or interactive components (such as buttons, select menus, and datepickers) 
    will be sent to a URL you specify.
```


### Sending reminders
The application automatically sends voting reminders in the middle and on the last day of the month.
send_reminder

On the first day of each month, information about the voting results in the previous month is sent.

```commandline

```

### Testing area
You can use our chanel for [testing bot](https://join.slack.com/t/programwyrniebot/shared_invite/zt-1ac7mt2iu-1VCqoLW6sHnave~Jur8AeQ).
