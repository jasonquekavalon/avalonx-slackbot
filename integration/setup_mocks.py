import os

def set_up_mocks():
    """
    Set up local GCS and Pub/Sub emulator mocks
    """
    from integration import gcs
    from google.cloud import storage, pubsub_v1
    # logger.info("Emulator environment: Setting up mocks for GCS and Pub/Sub")
    # Point google.cloud.storage.Client to a custom Mock class
    storage.Client = gcs.storage_client_mock
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(os.environ.get("PROJECT_ID"), 'file-upload')
    try:
        topic = publisher.create_topic(topic_path)
    except exceptions.AlreadyExists:
        logger.info("Pub/Sub topic already exists in project {}.".format(os.environ.get("PROJECT_ID")))
