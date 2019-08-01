from google.cloud import pubsub_v1
from log import log

logger = log.get_logger()


def pubsub(slack_client, default_backend_channel):
    project_id = "alfred-dev-1"
    subscription_name = "file-upload"

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_name)

    def callback(message):
        if message.attributes.get('eventType') == "OBJECT_FINALIZE":
            team = message.attributes.get('objectId').split('/')[1]
            friendly_id = message.attributes.get('objectId').split('/')[2]
            slack_client.chat_postMessage(channel=default_backend_channel, text=f"*{team}* has submitted a screenshot with Message ID: *{friendly_id}*")

        message.ack()
    future = subscriber.subscribe(subscription_path, callback=callback)
    try:
        future.result()
    except Exception as e:
        logger.error('Listening for messages on {} threw an Exception: {}.'.format(subscription_name, e))
