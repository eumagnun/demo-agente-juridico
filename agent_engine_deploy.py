
import vertexai
from main_agent.agent import root_agent
from vertexai import agent_engines
from vertexai.preview import reasoning_engines

vertexai.init(project="[SEU_PROJECT_ID]", staging_bucket="[gs://BUCKET_PARA_STAGING]")

app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

remote_app = agent_engines.create(
    display_name="agent_juridico_databricks2",
    agent_engine=app,
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]",
    ],
    extra_packages=["main_agent"]
)