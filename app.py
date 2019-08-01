import uuid
from uuid import UUID
from threading import Thread
import time

from flask import Flask, request, make_response, Response
import requests
from slack import WebClient
from google.cloud import pubsub_v1, storage

from ps_callback import pubsub
import config as cfg
from log import log
import datastore_client
from auth import get_token

log.setup_logger()
logger = log.get_logger()
slack_client = WebClient(cfg.SLACK_BOT_TOKEN)
SLACK_VERIFICATION_TOKEN = cfg.SLACK_VERIFICATION_TOKEN

SF_CASE_URL = "https://avalonsolutions--PreProd.cs109.my.salesforce.com/services/data/v39.0/sobjects/Case"

app = Flask(__name__)

DEFAULT_BACKEND_CHANNEL = "alfred-dev-internal"
bucket_name = "alfred-uploaded-images"

thread = Thread(target=pubsub, kwargs={"slack_client": slack_client, "default_backend_channel": DEFAULT_BACKEND_CHANNEL})
thread.start()

# Create the datastore client
ds_client = datastore_client.create_client("alfred-dev-1")

# TODO: Add checks for all responses from slack api calls


def verify_slack_token(func):
    """This should be used for ALL requests in the future"""
    def wrapper():
        req = request.form.to_dict()
        print(req)
        request_token = req['token']
        print(f"req token: {request_token}")
        if SLACK_VERIFICATION_TOKEN != request_token:
            # print("Error: invalid verification token!")
            return make_response("Request contains invalid Slack verification token", 403)
        else:
            return func()
    return wrapper


@app.route("/slack/validation", methods=["POST"])
def msg_validation(req):
    return req.get("text")


@app.route("/slack/gcp_support", methods=["POST"])
# @verify_slack_token
def slack_gcp():
    logger.info("Request received for gcp support...")
    req = request.form.to_dict()

    def process(req, friendly_id=None):
        if "message_id" not in req['text']:
            message = f"*{req['user_name']}* from workspace *{req['team_domain']}* says: *{req['text']}*. "
            friendly_id = datastore_client.add_item(ds_client, "message", req, friendly_id)
            # Add to salesforce
            create_sf_case(req['text'], req['team_domain'], friendly_id)

            internal_message = f"*{req['user_name']}* from workspace *{req['team_domain']}* has a question in {req['channel_name']}: *{req['text']}*. To respond, type `/avalonx-respond {friendly_id} <response>`."
            slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=internal_message)
        else:
            friendly_id = req['text'].split()[1]  # /avalonx message_id 1283219837857402 <message>
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

    if msg_validation(req):
        query = ds_client.query(kind='message')
        query.add_filter('team_domain', "=", req['team_domain'])
        count = len(list(query.fetch())) + 1
        friendly_id = f"{req['team_domain']}-{count}"
        req['friendly_id'] = friendly_id
        req["status"] = "Pending"
        thread = Thread(target=process, kwargs={'req': req, 'friendly_id': friendly_id})  # Start background thread to process
        thread.start()

        return make_response(f"Your Message ID is *{friendly_id}*. To check the status of your message, type `/avalonx-message-status {friendly_id}`. To upload a screenshot, type `/avalonx-screenshot {friendly_id}`.", 200)
    else:
        return make_response("You're missing the required properties", 400)


@app.route("/response", methods=["POST"])
# @verify_slack_token
def slack_response():
    logger.info("Request received for response...")
    req = request.form.to_dict()

    def process(req):
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

        elif isinstance(stored_responses, str):
            stored_responses = [stored_responses]
        stored_responses.append(response_to_message)
        datastore_client.update_response(ds_client, "message", stored_responses, friendly_id)

        slack_client.chat_postMessage(channel=channel_name, text=response)
    
    thread = Thread(target=process, kwargs={'req': req})  # Create background thread
    thread.start()
    return make_response("Response has been sent!", 200)


@app.route("/get/message", methods=["GET"])
def slack_get():
    message_query = request.args.get("message_id")
    # Get the message from the database using the datastore client
    queries = datastore_client.get_message(ds_client, "message", message_query)
    return make_response(str(queries), 200)


@app.route("/status", methods=["POST"])
# @verify_slack_token
def slack_status():
    logger.info("Request received for status endpoint...")
    req = request.form.to_dict()
    friendly_id = req['text']
    status = datastore_client.get_status(ds_client, "message", friendly_id)

    return make_response(f"Your status for ticket with ID *{friendly_id}* is *{status}*", 200)
#     return req['token']


@app.route("/resolve_message", methods=["POST"])
# @verify_slack_token
def slack_resolve_message():
    logger.info("Request received for resolve_message...")

    def process(req):
        req = request.form.to_dict()
        friendly_id = req['text'].split()[0]
        updated_status = "Completed"
        datastore_client.update_status(ds_client, "message", updated_status, friendly_id)

        slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=f"*{req['user_name']}* from workspace *{req['team_domain']}* has resolved their ticket with Message ID *{friendly_id}*")
    
    thread = Thread(target=process, kwargs={'req': req})
    thread.start()
    return make_response("Your issue has been resolved. Thank you for using the Alfred slack bot. We hope you have a nice day!", 200)


@app.route("/screenshot", methods=["POST"])
# @verify_slack_token
def slack_screenshot():
    logger.info("Request received for screenshot...")
    req = request.form.to_dict()
    friendly_id = req['text']
    team_id = req["team_domain"]
    website = f"https://alfred-dev-1.appspot.com/?friendly_id={friendly_id}&team_id={team_id}"
    slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=f"*{req['user_name']}* from workspace *{req['team_domain']}* is submitting screenshots under Message ID: *{friendly_id}*")
    return make_response(f"Please upload your screenshots at: {website}. Thank you!", 200)


@app.route("/getscreenshot", methods=["POST"])
def slack_getscreenshot():
    req = request.form.to_dict()

    def process(req):
        friendly_id = req['text'].split()[0]
        team_domain = req['team_domain']

        storage_client = storage.Client()
        count = 1
        prefix = team_domain + "/" + friendly_id

        for index, blob in list_blobs_with_prefix(bucket_name, prefix=prefix):
            file = blob.download_to_filename("hello.png")  # (name)

            with open("hello.png", "rb") as image:
                f = image.read()
                b = bytearray(f)
                slack_client.files_upload(token=cfg.SLACK_BOT_TOKEN, channels=DEFAULT_BACKEND_CHANNEL, file=b, filename=f"{friendly_id}_{index}.png")
    
    thread = Thread(target=process, kwargs={'req': req})
    thread.start()
    return make_response("", 200)


def list_blobs_with_prefix(bucket_name, prefix):
    """Lists all the blobs in the bucket that begin with the prefix.

    This can be used to list all blobs in a "folder", e.g. "public/".
    """
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
    for index, blob in enumerate(blobs):
        yield index, blob


@app.route("/hello", methods=["POST"])
# @verify_slack_token
def slash_hello():
    # slack_client.chat_postMessage(channel="alfred-dev-internal", text="test test")
    print("hello")
    return make_response("", 200)


def create_sf_case(message, team_id, friendly_id):
    # You should unpack the fields we want to save into Salesforce here (maybe all fields for now) into their appropriate SF equivalents
    token = get_token()

    # See https://developer.salesforce.com/docs/api-explorer/sobject/Case for documentation
    body = {
        "Type": "Question",
        "Origin": "Web",
        "Reason": friendly_id,
        "SuppliedCompany": team_id,
        "Subject": message,
        "SuppliedName": "Alfred GCP Support"
    }
# comment
    header = {
        "Authorization": "Bearer {}".format(token)
    }

    req = requests.post(SF_CASE_URL, json=body, headers=header)

    print(req.status_code)


# Start the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
