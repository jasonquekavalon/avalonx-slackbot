import os

from google.cloud import pubsub_v1
from google.api_core import exceptions

from log import log

logger = log.get_logger()


def pubsub(slack_client, default_backend_channel):
    project_id = os.getenv("PROJECT_ID") or "alfred-dev-1"
    subscription_name = "file-upload"

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_name)
    topic_path = subscriber.topic_path(project_id, 'file-upload')

    try:
        subscriber.create_subscription(subscription_path, topic_path)
    except exceptions.AlreadyExists as e:
        logger.info("Pub/Sub subscription already exists in project {}.".format(project_id))

    def callback(message):
        if message.attributes.get('eventType') == "OBJECT_FINALIZE":
            print(message)
            team = message.attributes.get('objectId').split('/')[0]
            friendly_id = message.attributes.get('objectId').split('/')[1]
            slack_client.chat_postMessage(channel=default_backend_channel, text=f"*{team}* has submitted a screenshot with Message ID: *{friendly_id}*")

        message.ack()
    future = subscriber.subscribe(subscription_path, callback=callback)
    try:
        future.result()
    except Exception as e:
        logger.error('Listening for messages on {} threw an Exception: {}.'.format(subscription_name, e))
