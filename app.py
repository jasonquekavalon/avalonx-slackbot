from flask import Flask, request, make_response, Response
import config as cfg
from slack import WebClient
import datastore_client
import uuid

slack_client = WebClient(cfg.SLACK_BOT_TOKEN)
SLACK_VERIFICATION_TOKEN = cfg.SLACK_VERIFICATION_TOKEN
app = Flask(__name__)

# Create the datastore client
ds_client = datastore_client.create_client("alfred-dev-1")

# TODO: Add checks for all responses from slack api calls


def verify_slack_token(request_token):
    """This should be used for ALL requests in the future"""
    if SLACK_VERIFICATION_TOKEN != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
        return make_response("Request contains invalid Slack verification token", 403)


@app.route("/slack/validation", methods=["POST"])
def msg_validation(req):
    return (req.get("message") and req.get("channel_name"))


@app.route("/slack/gcp_support", methods=["POST"])
def slack_gcp():

    # Save the message to the database using the datastore client
    # request status field (pending)

    req = request.form.to_dict()
    req["status"] = "Pending"
    message_id = datastore_client.add_item(ds_client, "message", req)

    # send channel a response
    if (msg_validation(req)):
        slack_client.chat_postMessage(channel=req["channel_name"], text=req['message'])
        slack_client.chat_postMessage(channel=req["backend_channel"], text=req['message'])
        return make_response("Your message id is " + str(message_id) + ". To check the status of your message, type '/status'.", 200)  # response is giving me the wrong message_id
    else:
        return make_response("You're missing the required properties", 400)


@app.route("/response", methods=["PUT"])
def slack_response():
    req = request.json
    response_to_message = req["response"]
    updated_status = "Completed!"
    message_id = request.args.get("message_id")
    datastore_client.update_response(ds_client, "message", response_to_message, message_id)
    datastore_client.update_status(ds_client, "message", updated_status, message_id)
    slack_client.chat_postMessage(channel=req["channel_name"], text=req["response"])
    return make_response("", 200)


@app.route("/get/message", methods=["GET"])
def slack_get():
    message_query = request.args.get("message_id")
    # Get the message from the database using the datastore client
    queries = datastore_client.get_message(ds_client, "message", message_query)
    return make_response(str(queries), 200)


@app.route("/get/status", methods=["GET"])
def slack_status():

    status_query = request.args.get("message_id")
    status = datastore_client.get_status(ds_client, "message", status_query)
    return make_response(str(status), 200)


@app.route("/hello", methods=["POST"])
def slash_hello():
    slack_client.chat_postMessage(channel="alfred-dev-internal", text="test test test")

    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
