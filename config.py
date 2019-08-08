import os

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SLACK_VERIFICATION_TOKEN = os.getenv("SLACK_VERIFICATION_TOKEN")
SF_API_URL = os.getenv("SF_API_URL")

IS_SANDBOX = True

KEY_FILE = "/root/salesforce.key"
ISSUER = os.getenv("SF_ISSUER")
SUBJECT = os.getenv("SF_SUBJECT")

PROJECT_ID = os.getenv("PROJECT_ID") or "alfred-dev-1"  # Safeguard
CLOUD_STORAGE_BUCKET = "alfred-uploaded-images"
