app:
	SLACK_BOT_TOKEN= SLACK_VERIFICATION_TOKEN= python -m app 

# Build and deploy in the real Google cloud
cb:
	gcloud builds submit --config cloudbuild.yaml .

# Build and deploy using your local environment
cbl:
	cloud-build-local --config cloudbuild.yaml --dryrun=false .
