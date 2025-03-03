#!/bin/bash

set -e

if [ -f .env ]; then
  echo "Loading environment variables from .env file"
  export $(cat .env | xargs)
fi

export DOCKER_FILE="Dockerfile.api"

bash deploy.sh
