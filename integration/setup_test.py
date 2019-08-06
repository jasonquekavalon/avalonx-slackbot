import os
import time


def setup_test():
    os.environ['PROJECT_ID'] = 'alfred-dev-emulator'

    if os.environ.get("RUNNING_IN_CLOUDBUILDER"):
        os.environ["DATASTORE_EMULATOR_HOST"] = "datastore:8432"
        os.environ['PUBSUB_EMULATOR_HOST'] = "pubsub:8433"
        os.environ['SLACK_API_URL'] = "http://slack-api:1080"
        os.environ['SF_API_URL'] = "http://sf-api:1081"
    else:
        os.environ["DATASTORE_EMULATOR_HOST"] = "0.0.0.0:8432"
        os.environ['PUBSUB_EMULATOR_HOST'] = "0.0.0.0:8433"
        os.environ['SLACK_API_URL'] = "http://0.0.0.0:1080"
        os.environ['SF_API_URL'] = "http://0.0.0.0:1081"

    time.sleep(10)  # Wait for datastore emulator to initialise
