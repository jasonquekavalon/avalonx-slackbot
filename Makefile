.PHONY: lint docker-builder docker-build it

BUILD_COMMIT=$(shell [[ -z "$(SHA_DOCKERFILE)" ]] && git log --pretty=format:'%h' -n 1 || echo "$(SHA_DOCKERFILE)")
BUILD_DATE=$(shell TZ=Utc date +%Y-%m-%d)
BUILD_TIME=$(shell TZ=Utc date +%H:%M:%S)
BUILD_RELEASE=$(shell [[ -z "$(TAG_DOCKERFILE)" ]] && git describe --tags || echo "$(TAG_DOCKERFILE)")

PYTHON_NAME=$(shell basename "$(PWD)")

lint:
	@echo "Using flake8 to check for common Python mistakes..."
	flake8

# Run integration tests in docker compose without rebuilding the image to test against
it-fast:
	@echo "Running all integration tests..."
	docker network create cloudbuild || true
	docker-compose up -d
	python3 -m pytest -v
	docker-compose down

# Run integration tests in docker compose after having rebuilt the image to test against
it-fresh: docker-build it
	@echo "Running all integration tests..."
	docker network create cloudbuild || true
	docker-compose up -d --force-recreate --renew-anon-volumes
	python3 -m pytest -v
	docker-compose down

# Build and deploy in the real Google cloud
cb:
	gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=$(BUILD_COMMIT),TAG_NAME=$(BUILD_RELEASE) .

# Build and deploy using your local environment
cbl:
	cloud-build-local --config cloudbuild.yaml --dryrun=false --substitutions=SHORT_SHA=$(BUILD_COMMIT),TAG_NAME=$(BUILD_RELEASE) .
