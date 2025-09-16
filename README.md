# Software criado apenas para fins de testes, sem qualquer tipo de garantia
## Agente Jurídico com Vertex AI e Databricks

Este projeto demonstra a criação de um assistente de IA (agente) de ponta a ponta, capaz de consultar uma base de dados de processos jurídicos hospedada no Databricks. O agente utiliza o Agent Development Kit (ADK) do Google e é implantado no Vertex AI Agent Engine, tornando-se acessível através do Agentspace.

## Visão Geral da Arquitetura

A solução é composta pelos seguintes componentes:

  * **Fonte de Dados (Databricks):** Uma tabela Delta no Databricks armazena os dados dos processos jurídicos. Para este exemplo, os dados são gerados de forma fictícia.
  * **Agente de IA (Google ADK):** O "cérebro" da operação, construído em Python com o ADK. Ele é composto por:
      * `root_agent`: O agente principal que interage com o usuário.
      * `advogado_agent`: Um sub-agente especialista com a persona de um advogado para análises mais detalhadas.
      * `get_info_processos_juridicos`: Uma ferramenta (tool) que se conecta à API do Databricks para executar consultas SQL de forma segura.
  * **Hospedagem (Vertex AI Agent Engine):** O agente é empacotado e implantado como um serviço escalável e gerenciável no Google Cloud.
  * **Interface de Uso (Agentspace):** O agente implantado é registrado no Agentspace, tornando-se detectável e pronto para uso.

## Pré-requisitos

Antes de começar, garanta que você tenha:

**Google Cloud:**

  * Um projeto no Google Cloud com a API do Vertex AI ativada.
  * `gcloud` CLI instalado e autenticado (`gcloud auth login`).
  * Um bucket no Cloud Storage para staging.

**Databricks:**

  * Um workspace no Databricks.
  * Um SQL Warehouse em execução e seu respectivo ID.
  * Um Service Principal (Principal de Serviço) com permissão para acessar o SQL Warehouse.
  * As credenciais do Service Principal (Client ID e Client Secret).

**Python:**

  * Python 3.9 ou superior.
  * `pip` para gerenciamento de pacotes.

-----

## 🚀 Guia de Instalação e Deploy

Siga estes passos para configurar e implantar o agente.

### 1\. Preparação do Ambiente Local

Clone o repositório e configure o ambiente Python.

```bash
# Clone o repositório
git clone https://github.com/eumagnun/demo-agente-juridico
cd demo-agente-juridico

# Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 2\. Configuração das Variáveis de Ambiente

As credenciais e configurações são gerenciadas através de variáveis de ambiente.

Copie o arquivo de exemplo:

```bash
cp main_agent/.env-example main_agent/.env
```

Edite o arquivo `main_agent/.env` e preencha com suas credenciais do Google Cloud e Databricks:

```ini
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=[SEU_PROJECT_ID]
GOOGLE_CLOUD_LOCATION=us-central1

DATABRICKS_WORKSPACE_URL=[SUA_DATABRICKS_WORKSPACE_URL]
DATABRICKS_CLIENT_ID=[SEU_DATABRICKS_CLIENT_ID]
DATABRICKS_CLIENT_SECRET=[SEU_DATABRICKS_CLIENT_SECRET]
DATABRICKS_WAREHOUSE_ID=[SEU_DATABRICKS_WAREHOUSE_ID]
```

### 3\. Geração dos Dados no Databricks

Antes de o agente poder consultar os dados, você precisa criá-los no Databricks. Utilize o script de geração de dados fornecido e execute-o em um notebook no seu workspace Databricks. Ele criará a tabela `processos_juridicos` necessária para o agente.
```Python
# Importando as bibliotecas necessárias para a sessão Spark, tipos de dados e geração de dados

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DateType, DoubleType
from faker import Faker
import random
from datetime import datetime, timedelta

# Inicializa o Faker para gerar dados em português do Brasil
fake = Faker('pt_BR')

# --- Parâmetros de Geração ---
num_processos = 1000 # Altere este número para gerar mais ou menos dados

# --- Listas de Dados para Simulação (garante consistência e realismo) ---
varas = ["1ª Vara Cível", "2ª Vara de Família", "Vara do Juizado Especial Cível", "1ª Vara Criminal", "2ª Vara da Fazenda Pública"]
comarcas = ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Porto Alegre", "Salvador"]
status_processo = ["Em andamento", "Arquivado", "Julgado", "Suspenso", "Em recurso"]
tipos_acao = ["Ação de Cobrança", "Divórcio Litigioso", "Reclamação Trabalhista", "Busca e Apreensão", "Inventário"]

# --- Função para gerar um processo aleatório ---
def gerar_processo(processo_id):
    data_abertura = fake.date_time_between(start_date='-5y', end_date='now').date()
    # Garante que a última movimentação seja sempre após a data de abertura
    data_movimentacao = fake.date_time_between(start_date=data_abertura, end_date='now').date()
    # Cria um número de processo em um formato comum no Brasil (simplificado)
    numero_processo = f"{random.randint(1000000, 9999999)}-{random.randint(10, 99)}.{datetime.now().year}.{random.randint(1, 9)}.{random.randint(10, 99)}.{random.randint(1000, 9999)}"

    return {
        "id_processo": processo_id,
        "numero_processo": numero_processo,
        "vara": random.choice(varas),
        "comarca": random.choice(comarcas),
        "status": random.choice(status_processo),
        "data_abertura": data_abertura,
        "data_ultima_movimentacao": data_movimentacao,
        "tipo_acao": random.choice(tipos_acao),
        "parte_autora": fake.name(),
        "advogado_autor": f"{fake.name()} (OAB/{fake.state_abbr()}{random.randint(10000, 99999)})",
        "parte_re": fake.company(),
        "advogado_reu": f"{fake.name()} (OAB/{fake.state_abbr()}{random.randint(10000, 99999)})",
        "valor_causa": round(random.uniform(1000.0, 500000.0), 2)
    }

# Gerando a lista de dados usando a função acima
dados_processos = [gerar_processo(i) for i in range(1, num_processos + 1)]

# Definindo o schema (a "planta" da nossa tabela)
# Por que definir um schema? Isso garante que os dados sejam carregados com os tipos corretos (data, texto, número), evitando erros de interpretação.
schema = StructType([
    StructField("id_processo", IntegerType(), False),
    StructField("numero_processo", StringType(), True),
    StructField("vara", StringType(), True),
    StructField("comarca", StringType(), True),
    StructField("status", StringType(), True),
    StructField("data_abertura", DateType(), True),
    StructField("data_ultima_movimentacao", DateType(), True),
    StructField("tipo_acao", StringType(), True),
    StructField("parte_autora", StringType(), True),
    StructField("advogado_autor", StringType(), True),
    StructField("parte_re", StringType(), True),
    StructField("advogado_reu", StringType(), True),
    StructField("valor_causa", DoubleType(), True)
])

# Criando o DataFrame do Spark a partir dos dados e do schema
df_processos = spark.createDataFrame(dados_processos, schema)

# --- Salvando os dados como uma tabela Delta ---
nome_tabela = "processos_juridicos"
# O modo "overwrite" substituirá a tabela se ela já existir, útil para testes.
df_processos.write.format("delta").mode("overwrite").saveAsTable(nome_tabela)

print(f"Tabela '{nome_tabela}' criada com sucesso com {num_processos} registros.")
display(df_processos) # Exibe uma amostra interativa dos dados
```

### 4\. Deploy do Agente no Vertex AI

O script **`agent_engine_deploy.py`** empacota e implanta seu agente no Vertex AI Reasoning Engines.

Edite o arquivo `agent_engine_deploy.py` e substitua os placeholders:

```python
vertexai.init(project="[SEU_PROJECT_ID]", staging_bucket="gs://[SEU_BUCKET_PARA_STAGING]")
```

Execute o script de deploy:

```bash
python agent_engine_deploy.py
```

Ao final da execução, o terminal exibirá os detalhes do agente implantado. Copie o **`resource_name`** completo do agente, pois você precisará dele no próximo passo. Ele terá o formato: `projects/SEU_PROJECT_NUMBER/locations/us-central1/reasoningEngines/ID_DO_AGENTE`.

### 5\. Registro no Agentspace

O último passo é tornar seu agente visível no Agentspace.

Edite o script **`register_to_agentspace.sh`** e preencha as variáveis com seus dados:

```bash
export PROJECT_ID=[SEU_PROJECT_ID]
export PROJECT_NUMBER=[SEU_PROJECT_NUMBER]
export REASONING_ENGINE_RES=[COLE_O_RESOURCE_NAME_DO_PASSO_ANTERIOR_AQUI]
export AS_APP="[ID_DA_SUA_APLICACAO_NO_AGENTSPACE]"
```

Execute o script:

```bash
bash register_to_agentspace.sh
```

Pronto\! Seu agente jurídico agora está implantado e disponível no seu Agentspace para responder a perguntas como: *"Quantos processos estão com o status 'Em andamento'?"*.

-----

## Estrutura do Projeto

```
.
├── agent_engine_deploy.py      # Script para deploy no Vertex AI Reasoning Engines.
├── main_agent/
│   ├── .env                    # (Local) Credenciais e configurações.
│   ├── .env-example            # Template para o arquivo .env.
│   ├── __init__.py             # Inicializador do módulo.
│   └── agent.py                # Lógica principal do agente, ferramentas e sub-agentes.
├── register_to_agentspace.sh   # Script para registrar o agente no Agentspace.
├── requirements.txt            # Dependências Python do projeto.
└── .gitignore                  # Arquivos e pastas a serem ignorados pelo Git.
```
