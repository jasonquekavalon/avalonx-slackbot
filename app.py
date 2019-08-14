import uuid
from uuid import UUID
from threading import Thread
import time
import os

from flask import Flask, request, make_response, Response, jsonify, copy_current_request_context
import requests
from slack import WebClient
from google.cloud import pubsub_v1, storage

from ps_callback import pubsub
import config as cfg
from log import log
import datastore_client
from auth import get_token
from integration import setup_mocks

log.setup_logger()
logger = log.get_logger()

PROJECT_ID = os.getenv("PROJECT_ID")

if PROJECT_ID == "alfred-dev-emulator":
    setup_mocks.set_up_mocks()
    slack_client = WebClient(cfg.SLACK_BOT_TOKEN, base_url=os.getenv('SLACK_API_URL'))
    ds_client = datastore_client.create_client(PROJECT_ID, http=requests.Session)  # Avoid bug in Datastore emulator
else:
    ds_client = datastore_client.create_client(PROJECT_ID)
    slack_client = WebClient(cfg.SLACK_BOT_TOKEN)


SLACK_VERIFICATION_TOKEN = cfg.SLACK_VERIFICATION_TOKEN

SF_CASE_URL = cfg.SF_API_URL or "https://avalonsolutions--PreProd.cs109.my.salesforce.com/services/data/v39.0/sobjects/Case"

app = Flask(__name__)

DEFAULT_BACKEND_CHANNEL = "alfred-dev-internal"
bucket_name = "alfred-uploaded-images"

thread = Thread(target=pubsub, kwargs={"slack_client": slack_client,
                                       "default_backend_channel": DEFAULT_BACKEND_CHANNEL})
thread.start()

# TODO: Add checks for all responses from slack api calls

def verify_slack_token(func):
    """This should be used for ALL requests in the future"""
    def wrapper():
        req = request.form.to_dict()
        print(req)
        request_token = req['token']
        # print(f"req token: {request_token}")
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
            if not PROJECT_ID == "alfred-dev-emulator":  # Explicitly check for now. TODO: Fix this
                create_sf_case(req['text'], req['team_domain'], friendly_id)

            internal_message = f"*{req['user_name']}* from workspace *{req['team_domain']}* has a question in {req['channel_name']}: *{req['text']}*. To respond, type `/avalonx-respond {friendly_id} <response>`."
            slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=internal_message)
        else:
            friendly_id = req['text'].split()[1] 
            following_message_split = req["text"].split(maxsplit=2)[2:]
            following_message = following_message_split[0]

            message = f"*{req['user_name']}* from workspace *{req['team_domain']}* says: *{following_message}*. "

            stored_messages = datastore_client.get_item(ds_client, "message", friendly_id, "text")
            if isinstance(stored_messages, str):
                stored_messages = [stored_messages]
            stored_messages.append(following_message)

            datastore_client.update_item(ds_client, "message", stored_messages, friendly_id, "text")

            internal_message = f"*{req['user_name']}* from workspace *{req['team_domain']}* has a question in {req['channel_name']}: *{following_message}*. To respond, type `/avalonx-respond {friendly_id} <response>`."
            slack_client.chat_postMessage(channel=DEFAULT_BACKEND_CHANNEL, text=internal_message)

    if msg_validation(req):
        query = ds_client.query(kind='message')
        query.add_filter('team_domain', "=", req['team_domain'])
        count = len(list(query.fetch())) + 1
        friendly_id = f"{req['team_domain']}-{count}"
        req['friendly_id'] = friendly_id
        req["status"] = "Pending"
        # Start background thread to process
        thread = Thread(target=process, kwargs={'req': req, 'friendly_id': friendly_id})
        thread.start()

        # website = f"https://alfred-dev-1.appspot.com/?friendly_id={friendly_id}&team_id={req['team_domain']}"

        msg = {
            "text": f"Your message has been received. Your Message ID is *{friendly_id}*.",
            "attachments": [
                {
                    "fallback": "You are unable to choose a game",
                    "callback_id": "status",
                    "color": "#3AA3E3",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "name": "command",
                            "text": "Message status",
                            "type": "button",
                            "value": f"{friendly_id}"
                        },
                        {
                            "name": "command",
                            "text": "Upload a screenshot",
                            "type": "button",
                            "url": f"https://alfred-dev-1.appspot.com/?friendly_id={friendly_id}&team_id={req['team_domain']}"
                        },
                    ]
                }
            ]
        }

        response = make_response(jsonify(msg), 200)
        response.headers['Content-Type'] = "application/json"
        return response
        # return make_response(jsonify(msg), 200)
    else:
        return make_response("You're missing the required properties", 400)


@app.route("/response", methods=["POST"])
# @verify_slack_token
def slack_response():
    logger.info("Request received for response...")
    
    @copy_current_request_context
    def process():
        req = request.form.to_dict()
        friendly_id = req['text'].split()[0]  

        response_to_message_split = req["text"].split(maxsplit=1)[1:]
        response_to_message = response_to_message_split[0]
        channel_name = datastore_client.get_item(ds_client, "message", friendly_id, "channel_name")
        response = f"*{req['user_name']}* from workspace *{req['team_domain']}* has responded to Message ID *{friendly_id}* in {req['channel_name']}: *{response_to_message}*. To respond, type `/avalonx message_id {friendly_id} <INPUT RESPONSE HERE>`. To resolve this conversation, type `/avalonx-resolve {friendly_id}`."
        stored_responses = datastore_client.get_item(ds_client, "message", friendly_id, "response")
        if stored_responses == None:
            stored_responses = []

        elif isinstance(stored_responses, str):
            stored_responses = [stored_responses]
        stored_responses.append(response_to_message)
        datastore_client.update_item(ds_client, "message", stored_responses, friendly_id, "response")

        msg = f"*{req['user_name']}* from workspace *{req['team_domain']}* has responded to Message ID *{friendly_id}* in {req['channel_name']}: *{response_to_message}*. To respond, type `/avalonx message_id {friendly_id} <INPUT RESPONSE HERE>`."

        attach = [
                {
                    "text": "Else:",
                    "fallback": "You are unable to choose a game",
                    "callback_id": "response",
                    "color": "#3AA3E3",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "name": "resolve",
                            "text": "Resolve message",
                            "type": "button",
                            "value": f"{friendly_id}"
                        },
                        {
                            "name": "command",
                            "text": "Upload a screenshot",
                            "type": "button",
                            "url": f"https://alfred-dev-1.appspot.com/?friendly_id={friendly_id}&team_id={req['team_domain']}"
                        }
                    ]
                }
        ]

        slack_client.chat_postMessage(channel=channel_name, text=msg, attachments=attach)
    
    thread = Thread(target=process)  # Create background thread
    thread.start()

    return make_response("Response has been sent!", 200)

@app.route("/status", methods=["POST"])
# @verify_slack_token
def slack_status():
    req = request.form.to_dict()
    friendly_id = req['payload'].split("value")[1].split('"')[2]
    team_domain = req['payload'].split("domain")[1].split('"')[2]
    callback_id = req['payload'].split("callback_id")[1].split('"')[2]
    name = req['payload'].split("name")[1].split('"')[2]

    if callback_id == "status" and name == "command":
        status = datastore_client.get_item(ds_client, "message", friendly_id, 'status')
        msg = {
            "text": f"Your status for ticket with ID *{friendly_id}* is *{status}*. To respond, type `/avalonx message_id {friendly_id} <INPUT RESPONSE HERE>`.",
            "attachments": [
                {
                    "text": "Else:",
                    "fallback": "You are unable to choose a game",
                    "callback_id": "status",
                    "color": "#3AA3E3",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "name": "command",
                            "text": "Message status",
                            "type": "button",
                            "value": f"{friendly_id}"
                        },
                        {
                            "name": "command",
                            "text": "Upload a screenshot",
                            "type": "button",
                            "url": f"https://alfred-dev-1.appspot.com/?friendly_id={friendly_id}&team_id={team_domain}"
                        },
                        {
                            "name": "resolve",
                            "text": "Resolve message",
                            "type": "button",
                            "value": f"{friendly_id}"
                        }
                    ]
                }
            ]
        }
        return make_response(jsonify(msg), 200)
    elif name == "resolve":
        return slack_resolve_message(friendly_id)
    else:
        return slack_getscreenshot(friendly_id, team_domain)

@app.route("/resolve_message", methods=["POST"])
# @verify_slack_token
def slack_resolve_message(friendly_id):
    logger.info("Request received for resolve_message...")
    req = request.form.to_dict()

    def process(req):
        updated_status = "Completed"
        datastore_client.update_item(ds_client, "message", updated_status, friendly_id, "status")

        slack_client.chat_postMessage(
            channel=DEFAULT_BACKEND_CHANNEL, text=f"*{req['user_name']}* from workspace *{req['team_domain']}* has resolved their ticket with Message ID *{friendly_id}*")

    thread = Thread(target=process, kwargs={'req': req})
    thread.start()
    return make_response("Your issue has been resolved. Thank you for using the Alfred slack bot. We hope you have a nice day!", 200)

@app.route("/getscreenshot", methods=["POST"])
def slack_getscreenshot(friendly_id, team_domain):
    req = request.form.to_dict()

    def process(req):
        storage_client = storage.Client()
        count = 1
        prefix = team_domain + "/" + friendly_id

        for index, blob in list_blobs_with_prefix(bucket_name, prefix=prefix):
            file = blob.download_to_filename("hello.png")  # (name)

            with open("hello.png", "rb") as image:
                f = image.read()
                b = bytearray(f)
                slack_client.files_upload(token=cfg.SLACK_BOT_TOKEN, channels=DEFAULT_BACKEND_CHANNEL,
                                          file=b, filename=f"{friendly_id}_{index}.png")

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
    header = {
        "Authorization": "Bearer {}".format(token)
    }

    req = requests.post(SF_CASE_URL, json=body, headers=header)

    print(req.status_code)


# Start the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
