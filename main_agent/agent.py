import logging
from google.adk.agents import LlmAgent
from google.adk.tools import load_artifacts

import os
import requests
import time
import json

# --- Configuração ---
WORKSPACE_URL: str = os.getenv("DATABRICKS_WORKSPACE_URL")
CLIENT_ID: str = os.getenv("DATABRICKS_CLIENT_ID")
CLIENT_SECRET: str = os.getenv("DATABRICKS_CLIENT_SECRET")
WAREHOUSE_ID: str = os.getenv("DATABRICKS_WAREHOUSE_ID")

def get_oauth_token(workspace_url, client_id, client_secret):
    """Obtém um token de acesso OAuth usando Client ID e Secret."""
    auth_url = f"{workspace_url}/oidc/v1/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'all-apis'
    }
    
    response = requests.post(auth_url, headers=headers, data=data)
    response.raise_for_status() # Lança exceção para erros HTTP
    print("Token OAuth obtido com sucesso!")
    return response.json()['access_token']

def executar_query(access_token, warehouse_id, status=None, vara=None, tipo_acao=None, parte=None):
    """
    Executa uma query no Databricks, aguarda o resultado e o retorna.

    Args:
        access_token (str): O token de acesso OAuth.
        warehouse_id (str): O ID do SQL Warehouse.
        status (str, optional): Filtra pela coluna 'status'.
        vara (str, optional): Filtra pela coluna 'vara'.
        tipo_acao (str, optional): Filtra pela coluna 'tipo_acao'.
        parte (str, optional): Filtra pela coluna 'parte'.

    Returns:
        list: Uma lista de listas contendo os dados do resultado, ou None se falhar.
    """
    # 1. Monta a query dinamicamente com os filtros
    base_query = "SELECT * FROM workspace.default.processos_juridicos"
    conditions = []
    
    # Adiciona as condições de filtro de forma segura
    if status:
        # Escapa aspas simples para prevenir SQL Injection
        safe_status = status.replace("'", "''")
        conditions.append(f"status = '{safe_status}'")    
    if vara:
        # Escapa aspas simples para prevenir SQL Injection
        safe_vara = vara.replace("'", "''")
        conditions.append(f"vara = '{safe_vara}'")
    if tipo_acao:
        safe_tipo_acao = tipo_acao.replace("'", "''")
        conditions.append(f"tipo_acao = '{safe_tipo_acao}'")
    if parte:
        safe_parte = parte.replace("'", "''")
        conditions.append(f"parte LIKE '%{safe_parte}%'") # Usando LIKE para busca parcial

    if conditions:
        sql_query = f"{base_query} WHERE {' AND '.join(conditions)}"
    else:
        sql_query = base_query

    print(f"Executando a query: {sql_query}")

    # 2. Submete a query para execução
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    submit_response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/sql/statements",
        headers=headers,
        json={"statement": sql_query, "warehouse_id": warehouse_id}
    )
    submit_response.raise_for_status()
    statement_id = submit_response.json()["statement_id"]
    print(f"Query submetida com sucesso! Statement ID: {statement_id}")

    # 3. Aguarda o resultado
    while True:
        status_response = requests.get(
            f"{WORKSPACE_URL}/api/2.0/sql/statements/{statement_id}",
            headers=headers
        )
        status_response.raise_for_status()
        status_data = status_response.json()
        
        current_state = status_data["status"]["state"]
        print(f"Status atual: {current_state}")

        if current_state == "SUCCEEDED":
            print("\nQuery executada com sucesso!")
            result = status_data.get("result", {})
            return result.get("data_array", [])
        elif current_state in ["FAILED", "CANCELED", "CLOSED"]:
            print(f"A query falhou com o status: {current_state}")
            print(status_data)
            return None
        
        time.sleep(2)

# Flight Agent: Specializes in flight booking and information
advogado_agent = LlmAgent(
    model='gemini-2.5-pro',
    name="AdvogadoAgent",
    description="Agente de advogados",
    instruction=f"""
    **Persona:** Você é um advogado especialista em [Área do Direito, ex: Direito Tributário].

    **Tarefa:** Analise o caso a seguir sob a perspectiva de um especialista e gere um parecer conciso, destacando os pontos de maior relevância, os riscos e as possíveis linhas de argumentação para o nosso cliente, que é o [Autor/Réu].

    **Dados do Processo:**
    * **Tipo de Ação:** [Ex: Ação de Cobrança]
    * **Resumo dos Fatos:** [Descreva objetivamente os acontecimentos que levaram ao processo. Inclua datas, valores e partes envolvidas.]
    * **Argumento Central do Cliente:** [Qual é a principal tese de defesa/acusação do seu cliente?]
    * **Argumento Central da Parte Contrária:** [Qual é a principal tese da outra parte?]
    * **Fase Atual:** [Ex: Fase de instrução, aguardando sentença, etc.]

    **Formato do Parecer:**
    Elabore um texto corrido, mas bem estruturado, abordando:
    1.  Impressão geral sobre o caso.
    2.  Análise de pontos fortes e fracos da nossa posição.
    3.  Recomendações iniciais.
    """)


def get_info_processos_juridicos(status:str) -> str:
    """Retorna informaÇões sobre processos juridicos com base


    Args:
        str: status=None [Em andamento, Julgado, Em recurso, Arquivado, Suspenso], 

    Returns:
        str: resultado da consulta de processos
    """

    token = get_oauth_token(WORKSPACE_URL, CLIENT_ID, CLIENT_SECRET)
    
    # Etapa 2: Executar a query com os filtros desejados
    # Deixe um filtro como None para não usá-lo
    print("\n--- Exemplo de Consulta com Filtros ---")
    resultados = executar_query(
        access_token=token,
        warehouse_id=WAREHOUSE_ID,
        status=status,
    )
    return resultados

root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="Você é Antonio, um agente muito gentil sempre disposto a ajudar com dúvidas.",
    tools=[load_artifacts,get_info_processos_juridicos],
    sub_agents=[advogado_agent]
)

logging.basicConfig(level=logging.INFO)