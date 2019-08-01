import os

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_VERIFICATION_TOKEN = os.getenv("SLACK_VERIFICATION_TOKEN")

IS_SANDBOX = True

KEY_FILE = "/root/salesforce.key"
ISSUER = os.getenv("SF_ISSUER")
SUBJECT = os.getenv("SF_SUBJECT")

PROJECT_ID = "alfred-dev-1"
CLOUD_STORAGE_BUCKET = "alfred-uploaded-images"
