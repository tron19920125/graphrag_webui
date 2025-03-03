# GraphRAG WebUI

A web interface for [GraphRAG](https://github.com/microsoft/graphrag).

## Cloud Resources

To deploy and run this solution, the following resources need to be activated:

- [Azure Virtual Machines](https://portal.azure.com/#browse/Microsoft.Compute%2FVirtualMachines)
- [AI Search](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/CognitiveSearch)
- [Azure OpenAI](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/OpenAI)
- [Document intelligence](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/FormRecognizer)

## Requirements

- Ubuntu 24
  - [Azure Virtual Machines](https://portal.azure.com/#browse/Microsoft.Compute%2FVirtualMachines)
- Docker & Docker Compose
  - [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)

## Install Docker & Docker Compose

```bash
sudo apt update -y
sudo snap install docker
sudo apt install docker-compose -y
```

## Set Authentication (Optional)

If you want to set authentication, copy and set your config.yaml:

```bash
cp config.yaml.example config.yaml
```

## Start App

```bash
bash start.sh
```

When the applications are started, you will have access to 2 URLs:

- Management App: <http://localhost:9000/>
  - OR <http://{your-vm-ip}:9000/>
- API Documentation: <http://localhost:9000/docs>
  - OR <http://{your-vm-ip}:9000/docs>

## Update GraphRAG WebUI

```bash
bash update.sh
```

## Make App as system Service

If you want to make the app as your service, run:

```bash
bash service.sh
```

## Deploy to production environment

Before deploying the applications, run:

```bash
az login
```

### Deploy API

You need copy env file and update first.

```bash
cp .env.example .env
```

Deploy API:

```bash
bash deploy_api.sh
```
