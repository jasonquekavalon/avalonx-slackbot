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

def verify_slack_token(func):
    """This should be used for ALL requests in the future"""
    # print("verify")
    logger.info("verify")
    def wrapper():
        request_token = func()
        if SLACK_VERIFICATION_TOKEN != request_token:
            print("Error: invalid verification token!")
            # print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
            return make_response("Request contains invalid Slack verification token", 403)
    return wrapper

@app.route("/slack/validation", methods=["POST"])
def msg_validation(req):
    return req.get("text")


@verify_slack_token
@app.route("/slack/gcp_support", methods=["POST"])
def slack_gcp():

    # Save the message to the database using the datastore client

    req = request.form.to_dict()

    query = ds_client.query(kind = 'message')
    query.add_filter('team_domain', "=", req['team_domain'])
    count = len(list(query.fetch())) + 1

    req["status"] = "Pending"
    friendly_id = f"{req['team_domain']}-{count}"    
    req["status"] = "Pending"
    req['friendly_id'] = friendly_id
    # send channel a response
    if (msg_validation(req)):
        
        if "message_id" not in req['text']:
            
            message = f"*{req['user_name']}* from workspace *{req['team_domain']}* says: *{req['text']}*. "
            friendly_id = datastore_client.add_item(ds_client, "message", req, friendly_id)
            
            internal_message = f"*{req['user_name']}* from workspace *{req['team_domain']}* has a question in {req['channel_name']}: *{req['text']}*. To respond, type `/avalonx-respond {friendly_id} <response>`."
            slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=internal_message)
        else:
            friendly_id = req['text'].split()[1] #/avalonx message_id 1283219837857402 <message>
            following_message_split = req["text"].split(maxsplit=2)[2:]
            following_message = following_message_split[0]
            
            message = f"*{req['user_name']}* from workspace *{req['team_domain']}* says: *{following_message}*. "
            
            stored_messages = datastore_client.get_saved_messages(ds_client, "message", friendly_id)
            if isinstance(stored_messages, str):
                stored_messages = [stored_messages]
            stored_messages.append(following_message)           
            
            datastore_client.update_message(ds_client, "message", stored_messages, friendly_id)
                
            internal_message = f"*{req['user_name']}* from workspace *{req['team_domain']}* has a question in {req['channel_name']}: *{following_message}*. To respond, type `/avalonx-respond {friendly_id} <response>`."
            slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=internal_message)
        # slack_client.chat_postMessage(channel=req["channel_name"], text=req['message'])
        
        make_response(message + f"Your Message ID is {friendly_id}. To check the status of your message, type `/avalonx-message-status {friendly_id}`.", 200)   

    else:
        make_response("You're missing the required properties", 400)

    return req['token']

@verify_slack_token
@app.route("/response", methods=["POST"])
def slack_response():
    req = request.form.to_dict()

    
    friendly_id = req['text'].split()[0]  # Should be a uuid if it was sent in as the first word
    # Ensure that message_id is a real uuid.

    # try:
    #     _ = UUID(str(message_id), version=4)
    # except ValueError:
    #     # If it's a value error, then the string 
    #     # is not a valid hex code for a UUID.
    #     return make_response("You're missing the required properties. Response should be in this format `/avalonx-respond <message id> <response>`. ", 400)

    response_to_message_split = req["text"].split(maxsplit=1)[1:]
    response_to_message = response_to_message_split[0]
    channel_name = datastore_client.get_channelname(ds_client, "message", friendly_id)
    response = f"*{req['user_name']}* from workspace *{req['team_domain']}* has responded to Message ID *{friendly_id}* in {req['channel_name']}: *{response_to_message}*. To respond, type `/avalonx message_id {friendly_id} <INPUT RESPONSE HERE>`. To resolve this conversation, type `/avalonx-resolve {friendly_id}`."
    stored_responses = datastore_client.get_saved_responses(ds_client, "message", friendly_id)
    if stored_responses == None:
        stored_responses = []
        
    elif isinstance(stored_responses,str):
        stored_responses = [stored_responses]
    stored_responses.append(response_to_message)
    datastore_client.update_response(ds_client, "message", stored_responses, friendly_id)

    slack_client.chat_postMessage(channel=channel_name, text=response)
    make_response("Response has been sent!", 200)
    return req['token']

@app.route("/get/message", methods=["GET"])
def slack_get():
    message_query = request.args.get("message_id")
    # Get the message from the database using the datastore client
    queries = datastore_client.get_message(ds_client, "message", message_query)
    return make_response(str(queries), 200)

@verify_slack_token
@app.route("/status", methods=["POST"])
def slack_status():
    req = request.form.to_dict()
    friendly_id = req['text']
    status = datastore_client.get_status(ds_client, "message", friendly_id)

    make_response(f"Your status for ticket with ID = {friendly_id} is *{status}*", 200)
    return req['token']

@verify_slack_token
@app.route("/resolve_message", methods=["POST"])
def slack_resolve_message():
    req = request.form.to_dict()
    friendly_id = req['text'].split()[0]
    updated_status = "Completed"
    datastore_client.update_status(ds_client, "message", updated_status, friendly_id)
  
    slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=f"*{req['user_name']}* from workspace *{req['team_domain']}* has resolved their ticket with Message ID *{friendly_id}*")
    make_response("Your issue has been resolved. Thank you for using the Alfred slack bot. We hope you have a nice day!", 200)
    return req['token']

@app.route("/hello", methods=["POST"])
def slash_hello():
    slack_client.chat_postMessage(channel="alfred-dev-internal", text="test test")

    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
