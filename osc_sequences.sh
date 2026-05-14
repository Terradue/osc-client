#!/bin/bash
set -euo pipefail

read -p "Open Science Catalog location: " OSC_LOCATION

PROJECT_NAME=Geohazards
PROJECT_ID=geohazards-tep
WORKFLOW=oci://ghcr.io/eoap/app-ml4floods/app-ml4floods:latest
WF_ID=ml4floods-v0-4-2
JOB=${WF_ID}-9r4pt

# [ -d "./open-science-catalog-metadata/.git" ] && git -C ./open-science-catalog-metadata pull --ff-only || git clone git@github.com:Terradue/open-science-catalog-metadata-staging.git open-science-catalog-metadata

echo "Creating the Workflow..."

osc-client \
--id ${WF_ID} \
--project-id ${PROJECT_ID} \
--project-name ${PROJECT_NAME} \
--ogc-api-processes-endpoint https://processing.geohazards-tep.eu/7465727261647565 \
--output $OSC_LOCATION \
$WORKFLOW \
workflow \

echo "Workflow created!"

echo "Requesting the Authentication Token..."

# read username and password from prompt
read -p "Username: " USERNAME
read -s -p "Password: " PASSWORD

TOKEN=$(curl -X POST https://iam.terradue.com/realms/master/protocol/openid-connect/token  -d "grant_type=password"  -d "client_id=processing-gep"   -d "username=$USERNAME" -d "password=$PASSWORD"  -d "scope=offline_access" | jq -r '.access_token')

echo "Authentication Token obtained!"

echo "Creating the Experiment..."

osc-client \
--id $JOB \
--project-id ${PROJECT_ID} \
--project-name ${PROJECT_NAME} \
--ogc-api-processes-endpoint https://processing.geohazards-tep.eu/7465727261647565 \
--output $OSC_LOCATION \
$WORKFLOW \
experiment \
--workflow-id ${WF_ID} \
--authorization-token $TOKEN

echo "Experiment created!"

echo "Creating the Product..."

osc-client \
--id $JOB \
--project-id ${PROJECT_ID} \
--project-name ${PROJECT_NAME} \
--ogc-api-processes-endpoint https://processing.geohazards-tep.eu/7465727261647565 \
--output $OSC_LOCATION \
$WORKFLOW \
products \
--experiment-id ${JOB} \
--authorization-token $TOKEN

echo "Product created!"

# git -C e-catalog-metadata commit -m "${PROJECT_ID} Update"
# git -C ./open-science-catalog-metadata push
