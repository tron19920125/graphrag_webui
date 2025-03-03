#!/bin/bash

set -e

if [ -f .env ]; then
  source .env
fi

APP_NAME=$1

if [ -z "$APP_NAME" ]; then
  echo "Please provide a App name by running: ./deploy_api.sh <app_name>"
  exit 1
fi

export DOCKER_FILE="Dockerfile.api"

bash deploy.sh "${APP_NAME}-api"
