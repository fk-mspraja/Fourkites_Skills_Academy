"""
Configuration management for RCA backend
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings"""

    # API Settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

    # ClickHouse (SigNoz)
    SIGNOZ_CLICKHOUSE_HOST = os.getenv("SIGNOZ_CLICKHOUSE_HOST")
    SIGNOZ_CLICKHOUSE_PORT = int(os.getenv("SIGNOZ_CLICKHOUSE_PORT", 9000))
    SIGNOZ_CLICKHOUSE_USER = os.getenv("SIGNOZ_CLICKHOUSE_USER")
    SIGNOZ_CLICKHOUSE_PASSWORD = os.getenv("SIGNOZ_CLICKHOUSE_PASSWORD")
    SIGNOZ_CLICKHOUSE_DATABASE = os.getenv("SIGNOZ_CLICKHOUSE_DATABASE", "signoz_logs")

    # ClickHouse (Rewind)
    REWIND_CLICKHOUSE_HOST = os.getenv("REWIND_CLICKHOUSE_HOST")
    REWIND_CLICKHOUSE_PORT = int(os.getenv("REWIND_CLICKHOUSE_PORT", 9440))
    REWIND_CLICKHOUSE_USER = os.getenv("REWIND_CLICKHOUSE_USER")
    REWIND_CLICKHOUSE_PASSWORD = os.getenv("REWIND_CLICKHOUSE_PASSWORD")
    REWIND_CLICKHOUSE_DATABASE = os.getenv("REWIND_CLICKHOUSE_DATABASE", "rewind_db")
    REWIND_CLICKHOUSE_SECURE = os.getenv("REWIND_CLICKHOUSE_SECURE", "true").lower() == "true"

    # Redshift
    REDSHIFT_HOST = os.getenv("REDSHIFT_HOST")
    REDSHIFT_PORT = int(os.getenv("REDSHIFT_PORT", 5439))
    REDSHIFT_USER = os.getenv("REDSHIFT_USER")
    REDSHIFT_PASSWORD = os.getenv("REDSHIFT_PASSWORD")
    REDSHIFT_DATABASE = os.getenv("REDSHIFT_DATABASE", "productiondwh")

    # FourKites API
    FK_API_AUTH_METHOD = os.getenv("FK_API_AUTH_METHOD", "basic")
    FK_API_USER = os.getenv("FK_API_USER")
    FK_API_PASSWORD = os.getenv("FK_API_PASSWORD")
    FK_API_APP_ID = os.getenv("FK_API_APP_ID")
    FK_API_SECRET = os.getenv("FK_API_SECRET")

    # API Base URLs
    TRACKING_API_BASE_URL = os.getenv("TRACKING_API_BASE_URL", "https://tracking-api-rr.fourkites.com")
    COMPANY_API_BASE_URL = os.getenv("COMPANY_API_BASE_URL", "https://company-api.fourkites.com")
    DATAHUB_API_BASE_URL = os.getenv("DATAHUB_API_BASE_URL")
    JT_API_BASE_URL = os.getenv("JT_API_BASE_URL", "https://just-transform.fourkites.com")

    # Athena
    USE_ATHENA = os.getenv("USE_ATHENA", "true").lower() == "true"
    ATHENA_REGION = os.getenv("ATHENA_REGION", "us-east-1")
    ATHENA_OUTPUT_LOCATION = os.getenv("ATHENA_OUTPUT_LOCATION")
    ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "raw_data_db")
    ATHENA_AWS_ACCESS_KEY_ID = os.getenv("ATHENA_AWS_ACCESS_KEY_ID")
    ATHENA_AWS_SECRET_ACCESS_KEY = os.getenv("ATHENA_AWS_SECRET_ACCESS_KEY")
    ATHENA_AWS_SESSION_TOKEN = os.getenv("ATHENA_AWS_SESSION_TOKEN")  # Optional for temporary credentials

    # LLM Provider
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure_openai")

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

    # Azure OpenAI
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

    # Confluence
    CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
    CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
    CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
    CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY", "EI")

    # Slack
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_WORKSPACE = os.getenv("SLACK_WORKSPACE", "fourkites.slack.com")

    # JIRA
    JIRA_SERVER = os.getenv("JIRA_SERVER")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")


# Global config instance
config = Config()
