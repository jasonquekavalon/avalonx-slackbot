import time
from google.cloud import pubsub_v1

project_id = "afred-dev-1"
subscription_name = "projects/alfred-dev-1/subscriptions/file-upload"

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_name)

def callback(message):
    print("Message recieved: {}".format(message))
    message.ack()

subscriber.subscribe(subscription_path, callback=callback)

print("Listening for messages on {}".format(subscription_path))

