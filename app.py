from flask import Flask, request, make_response, Response
import config as cfg
from slack import WebClient

slack_client = WebClient(cfg.SLACK_BOT_TOKEN)
SLACK_VERIFICATION_TOKEN = cfg.SLACK_VERIFICATION_TOKEN
app = Flask(__name__)


# TODO: Add checks for all responses from slack api calls
def verify_slack_token(request_token):
    """This should be used for ALL requests in the future"""
    if SLACK_VERIFICATION_TOKEN != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
        return make_response("Request contains invalid Slack verification token", 403)


@app.route("/slack/test", methods=["POST"])
def slack_test():
    req = request.json

    # send channel a response
    slack_client.chat_postMessage(channel=req["channel_name"], text=req['message'])

    return make_response("", 200)


@app.route("/hello", methods=["POST"])
def slash_hello():
    slack_client.chat_postMessage(channel="alfred-dev-internal", text="//testing rolling update//")

    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
