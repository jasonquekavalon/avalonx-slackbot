from flask import Flask, request, make_response, Response
import config as cfg
from slack import WebClient
import datastore_client
import uuid
import logging
from uuid import UUID

logger = logging.getLogger()
slack_client = WebClient(cfg.SLACK_BOT_TOKEN)
SLACK_VERIFICATION_TOKEN = cfg.SLACK_VERIFICATION_TOKEN
app = Flask(__name__)

DEFAULT_BACKEND_CHANNEL = "alfred-dev-internal"


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
    return req.get("text")


@app.route("/slack/gcp_support", methods=["POST"])
def slack_gcp():

    # Save the message to the database using the datastore client

    req = request.form.to_dict()
    print(req)
    
    req["status"] = "Pending"

    # send channel a response
    if (msg_validation(req)):
        # saved_messages = []
        if "message_id" not in req['text']:
            # message_from_customer = req["text"]
            message = f"*{req['user_name']}* from workspace *{req['team_domain']}* says: *{req['text']}*. "
            message_id = datastore_client.add_item(ds_client, "message", req)
            # saved_messages.append(message_stored)
            internal_message = f"*{req['user_name']}* from workspace *{req['team_domain']}* has a question in {req['channel_name']}: *{req['text']}*. To respond, type `/avalonx-respond {message_id} <response>`."
            slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=internal_message)
        else:
            message_id = req['text'].split()[1] #/avalonx message_id 1283219837857402 <message>
            following_message_split = req["text"].split(maxsplit=2)[2:]
            following_message = following_message_split[0]
            # mesage_from_customer = following_messages
            message = f"*{req['user_name']}* from workspace *{req['team_domain']}* says: *{following_message}*. "
            # saved_messages.append(message_stored)
            stored_messages = datastore_client.get_saved_messages(ds_client, "message", message_id)
            new_stored_messages = stored_messages.append(following_message)
            datastore_client.update_message(ds_client, "message", new_stored_messages, message_id)
                
            internal_message = f"*{req['user_name']}* from workspace *{req['team_domain']}* has a question in {req['channel_name']}: *{following_message}*. To respond, type `/avalonx-respond {message_id} <response>`."
            slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=internal_message)
        # slack_client.chat_postMessage(channel=req["channel_name"], text=req['message'])
        
        return make_response(message + f"Your Message ID is {message_id}. To check the status of your message, type `/avalonx-message-status {message_id}`.", 200)   
    else:
        return make_response("You're missing the required properties", 400)

@app.route("/response", methods=["POST"])
def slack_response():
    req = request.form.to_dict()
    
    message_id = req['text'].split()[0]  # Should be a uuid if it was sent in as the first word
    # Ensure that message_id is a real uuid.
    try:
        _ = UUID(str(message_id), version=4)
    except ValueError:
        # If it's a value error, then the string 
        # is not a valid hex code for a UUID.
        return make_response("You're missing the required properties. Response should be in this format `/avalonx-respond <message id> <response>`. ", 400)
    response_to_message_split = req["text"].split(maxsplit=1)[1:]
    response_to_message = response_to_message_split[0]
    channel_name = datastore_client.get_channelname(ds_client, "message", message_id)
    response = f"*{req['user_name']}* from workspace *{req['team_domain']}* has responded to Message ID *{message_id}* in {req['channel_name']}: *{response_to_message}*. To respond, type `/avalonx message_id {message_id} <INPUT RESPONSE HERE>`. To resolve this conversation, type `/avalonx-resolve {message_id}`."

    datastore_client.update_response(ds_client, "message", response_to_message, message_id)
    slack_client.chat_postMessage(channel=channel_name, text=response)
    return make_response("Response has been sent!", 200)


@app.route("/get/message", methods=["GET"])
def slack_get():
    message_query = request.args.get("message_id")
    # Get the message from the database using the datastore client
    queries = datastore_client.get_message(ds_client, "message", message_query)
    return make_response(str(queries), 200)


@app.route("/status", methods=["POST"])
def slack_status():
    req = request.form.to_dict()
    ticket_id = req['text']
    status = datastore_client.get_status(ds_client, "message", ticket_id)
    return make_response(f"Your status for ticket with ID = {ticket_id} is *{status}*", 200)

@app.route("/resolve_message", methods=["POST"])
def slack_resolve_message():
    req = request.form.to_dict()
    message_id = req['text'].split()[0]
    updated_status = "Completed"
    datastore_client.update_status(ds_client, "message", updated_status, message_id)
  
    slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=f"*{req['user_name']}* from workspace *{req['team_domain']}* has resolved their ticket with Message ID *{message_id}*")
    return make_response("Your issue has been resolved. Thank you for using the Alfred slack bot. We hope you have a nice day!", 200)

@app.route("/hello", methods=["POST"])
def slash_hello():
    slack_client.chat_postMessage(channel="alfred-dev-internal", text="test test")

    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
