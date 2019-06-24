# avalonx-slackbot


# Installation
Create your virtual environment and install dependencies:
- `virtualenv venv --python=python3.7`
- `source venv/bin/activate`
- `pip install -r requirements.txt`

Copy the `Bot User OAuth Access Token` from the Slack workspace into `config.py` under `SLACK_BOT_TOKEN`


Copy the `Signing Secret` from the App Credentials page on the Slack workspace into `config.py` under `SLACK_VERIFICATION_TOKEN`

# Running
Run `app.py`. This will start the Flask web framework.

# Testing
Download and install Postman (https://www.getpostman.com/). Create a new collection. Add a new `POST` request with the following details:
- Address: `127.0.0.1:5000/some-endpoint`. Example `127.0.0.1:5000/slack/test`: This will reach the /slack/test endpoint defined in server.py.
In the Headers field, add:
- Authorization | Bearer `the client secret from app credentials page in slack workspace`
- Content-Type | application/json

Change the body field to be `raw` and make sure the type is set to application/json and send the following body:
```
{
	"channel_name": "alfred-dev",
	"message": "test message!"
}
```

Press send. Postman will now send a request to your local server running Flask, which in turn will use the Slack API for communicating to our workspace!

