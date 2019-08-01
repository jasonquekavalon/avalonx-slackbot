import time
from google.cloud import pubsub_v1

project_id = "alfred-dev-1"
subscription_name = "file-upload"

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_name)

def callback(message):
    print("Message recieved: {}".format(message))
    
    message.ack()

future = subscriber.subscribe(subscription_path, callback=callback)

print("Listening for messages on {}".format(subscription_path))
# while True:
#     time.sleep(60)
future.result()


