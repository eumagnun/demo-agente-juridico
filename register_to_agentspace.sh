
export PROJECT_ID="XXXXXXX" #"Seu PROJECT_ID do GOOGLE CLOUD"
export PROJECT_NUMBER=000000  #"Seu PROJECT_NUMBER do GOOGLE CLOUD"
export AGENT_ID=0000000 #"O AGENT_ID é o ID gerado pelo deploy"
export AGENT_DISPLAY_NAME_RES="Assistente Jurídico" #"Nome do seu agent"
export AGENT_DESCRIPTION="Análise de processos jurídicos" #"Descrição do seu agent"
export AS_APP="XXXXXXX-XXXXXXX" #"ID da sua instância do AGENTSPACE"
export AGENT_LOG_URL="https://storage.googleapis.com/my-demo-public-bucket/logo.png" #"URL IMAGEM LOGO" 
export AS_APP_LOCATION="global" #"LOCALIDADE_SUA_INSTANCIA_AGENTSPACE"

# The API endpoint is different depending on the location of the Agentspace app
if [ "$AS_APP_LOCATION" = "us" ] || [ "$AS_APP_LOCATION" = "eu" ]; then
   API_ENDPOINT="https://${AS_APP_LOCATION}-discoveryengine.googleapis.com"
else
   API_ENDPOINT="https://discoveryengine.googleapis.com"
fi

export AGENT_ENGINE_RES="projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${AGENT_ID}"

# 2. Execute o comando cURL para registrar o agente
curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "x-goog-user-project: ${PROJECT_ID}" \
${API_ENDPOINT}/v1alpha/projects/${PROJECT_NUMBER}/locations/${AS_APP_LOCATION}/collections/default_collection/engines/${AS_APP}/assistants/default_assistant/agents -d '{
  "displayName": "'"${AGENT_DISPLAY_NAME_RES}"'",
  "description": "'"${AGENT_DESCRIPTION}"'",
  "icon": {
    "uri":  "'"${AGENT_LOG_URL}"'"
  },
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "'"${AGENT_DESCRIPTION}"'"
    },
    "provisioned_reasoning_engine": {
      "reasoning_engine": "'"${AGENT_ENGINE_RES}"'"
    }
  }
}'
