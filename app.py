from flask import Flask, request, make_response, Response
import config as cfg
from slack import WebClient
import datastore_client
import uuid

slack_client = WebClient(cfg.SLACK_BOT_TOKEN)
SLACK_VERIFICATION_TOKEN = cfg.SLACK_VERIFICATION_TOKEN
app = Flask(__name__)

# Create the datastore client
ds_client=datastore_client.create_client("alfred-dev-1")

# TODO: Add checks for all responses from slack api calls
def verify_slack_token(request_token):
    """This should be used for ALL requests in the future"""
    if SLACK_VERIFICATION_TOKEN != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
        return make_response("Request contains invalid Slack verification token", 403)

message_id = str(uuid.uuid4())
@app.route("/slack/test", methods=["POST"])
def slack_test():
    req = request.json

    # Save the message to the database using the datastore client
    #request status field (pending)
    req["status"] = "Pending" 
    datastore_client.add_item(ds_client, "message", req)

    # send channel a response
    slack_client.chat_postMessage(channel=req["channel_name"], text=req['message'])

    return make_response("", 200)

@app.route("/get/message", methods=["GET"])
def slack_get():
    message_query = request.args.get("message_id")
    # Get the message from the database using the datastore client
    queries = datastore_client.get_message(ds_client, "message", message_query)
    return make_response(str(queries), 200)
    

@app.route("/hello", methods=["POST"])
def slash_hello():
    slack_client.chat_postMessage(channel="alfred-dev", text="HELLO WORLD")

    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    app.run()
