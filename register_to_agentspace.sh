export PROJECT_ID=[SEU_PROJECT_ID]
export PROJECT_NUMBER=[SEU_PROJECT_NUMBER]
export REASONING_ENGINE_RES=[URL_GERADA_PELO_REASONING_ENGINE]
export AGENT_DISPLAY_NAME_RES="demo databricks"
export AS_APP="[ID_APP_AGENTSPACE]"


curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "x-goog-user-project: ${PROJECT_ID}" \
https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${AS_APP}/assistants/default_assistant/agents -d '{
    "displayName": "'"${AGENT_DISPLAY_NAME_RES}"'",
    "description": "'"You are an Assistant with multiple tools"'",
    "icon": {
        "uri": "https://images.icon-icons.com/2699/PNG/512/databricks_logo_icon_170295.png"
    },
    "adk_agent_definition": {
        "tool_settings": {
            "tool_description": "Sua missão é responder dúvidas sobre processos juridicos. Se necessário voce pode usar sua Tool para obter informações ou acionar o subagent advogado"
        },
        "provisioned_reasoning_engine": {
            "reasoning_engine": "'"${REASONING_ENGINE_RES}"'"
        }
    }
}'