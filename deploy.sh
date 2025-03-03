#!/bin/bash

set -e

sudo chmod 666 /var/run/docker.sock

if [ -z "$APP_NAME" ]; then
  echo "APP_NAME is not set"
  exit 1
fi
echo "app name: $APP_NAME"

# if APP_CPU is not set, use default 4.0
if [ -z "$APP_CPU" ]; then
  APP_CPU="4.0"
fi
echo "cpu: $APP_CPU"

# if APP_MEMORY is not set, use default 8.0
if [ -z "$APP_MEMORY" ]; then
  APP_MEMORY="8.0Gi"
fi
echo "memory: $APP_MEMORY"

# if min-replicas is not set, use default 1
if [ -z "$MIN_REPLICAS" ]; then
  MIN_REPLICAS="0"
fi
echo "min-replicas: $MIN_REPLICAS"

# if max-replicas is not set, use default 3
if [ -z "$MAX_REPLICAS" ]; then
  MAX_REPLICAS="4"
fi
echo "max-replicas: $MAX_REPLICAS"

# if ACR_NAME is not set, use default "daidemo"
if [ -z "$ACR_NAME" ]; then
  ACR_NAME="daidemo"
fi
echo "acr name: $ACR_NAME"

# if RESOURCE_GROUP is not set, use default "daidemo"
if [ -z "$RESOURCE_GROUP" ]; then
  RESOURCE_GROUP="daidemo"
fi
echo "resource group: $RESOURCE_GROUP"

# if ENV_NAME is not set, use default "daidemo"
if [ -z "$ENV_NAME" ]; then
  ENV_NAME="daidemo"
fi
echo "environment: $ENV_NAME"

# if LOCATION is not set, use default "japaneast"
if [ -z "$LOCATION" ]; then
  LOCATION="japaneast"
fi
echo "location: $LOCATION"

echo "Creating Resource Group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

echo "Creating Container Registry..."
az acr create \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Basic

echo "Creating Container App Environment..."
az containerapp env create \
  --name $ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

VERSION=$(date +"%Y%m%d%H%M")
UPDATE_TIME=$(date +"%Y-%m-%d %H:%M:%S")
IMAGE=$ACR_NAME.azurecr.io/$APP_NAME:$VERSION
IMAGE=$(echo "$IMAGE" | tr '[:upper:]' '[:lower:]')
echo "image: $IMAGE"

az acr login --name $ACR_NAME

docker build --build-arg APP_VERSION=$VERSION \
  --build-arg UPDATE_TIME="$UPDATE_TIME" \
  -f $DOCKER_FILE \
  -t $IMAGE .

docker images | grep $APP_NAME | grep $VERSION

docker push $IMAGE

docker images | grep $APP_NAME | grep $VERSION

# enable admin user
az acr update -n $ACR_NAME --admin-enabled true

# get registry credentials
ACR_SERVER=$(az acr show --name $ACR_NAME --query "loginServer" -o tsv)
if [ -z "$ACR_SERVER" ]; then
  echo "ACR_SERVER is empty"
  exit 1
fi

REGISTRY_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

if [ -z "$REGISTRY_USERNAME" ]; then
  echo "REGISTRY_USERNAME is not set"
  exit 1
fi

if [ -z "$REGISTRY_PASSWORD" ]; then
  echo "REGISTRY_PASSWORD is not set"
  exit 1
fi

echo "Creating Container App..."
RES=$(az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENV_NAME \
  --image $IMAGE \
  --target-port 80 \
  --ingress 'external' \
  --min-replicas $MIN_REPLICAS \
  --max-replicas $MAX_REPLICAS \
  --registry-server $ACR_SERVER \
  --registry-username $REGISTRY_USERNAME \
  --registry-password $REGISTRY_PASSWORD \
  --cpu $APP_CPU \
  --memory $APP_MEMORY)

# docker images | grep $APP_NAME | grep $VERSION

url=$(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "Container App created successfully."
echo ""
echo "APP URL:"
echo "https://$url"
