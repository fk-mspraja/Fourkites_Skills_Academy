"""
Configuration for Rewind API
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for Rewind API"""

    # =============================================================================
    # API Settings
    # =============================================================================
    API_TITLE = "Rewind API"
    API_VERSION = "1.0.0"
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8080"))

    # =============================================================================
    # Data Sources
    # =============================================================================

    # ClickHouse - SigNoz (logs from integrations-worker)
    SIGNOZ_CLICKHOUSE_HOST = os.getenv("SIGNOZ_CLICKHOUSE_HOST", "localhost")
    SIGNOZ_CLICKHOUSE_PORT = int(os.getenv("SIGNOZ_CLICKHOUSE_PORT", "9000"))
    SIGNOZ_CLICKHOUSE_USER = os.getenv("SIGNOZ_CLICKHOUSE_USER", "default")
    SIGNOZ_CLICKHOUSE_PASSWORD = os.getenv("SIGNOZ_CLICKHOUSE_PASSWORD", "")

    # ClickHouse - Rewind DB (fact_load_file_* tables)
    REWIND_CLICKHOUSE_HOST = os.getenv("REWIND_CLICKHOUSE_HOST", "localhost")
    REWIND_CLICKHOUSE_PORT = int(os.getenv("REWIND_CLICKHOUSE_PORT", "9000"))
    REWIND_CLICKHOUSE_USER = os.getenv("REWIND_CLICKHOUSE_USER", "default")
    REWIND_CLICKHOUSE_PASSWORD = os.getenv("REWIND_CLICKHOUSE_PASSWORD", "")
    REWIND_CLICKHOUSE_DATABASE = os.getenv("REWIND_CLICKHOUSE_DATABASE", "rewind_db")
    REWIND_CLICKHOUSE_SECURE = os.getenv("REWIND_CLICKHOUSE_SECURE", "false").lower() == "true"
    REWIND_CLICKHOUSE_VERIFY = os.getenv("REWIND_CLICKHOUSE_VERIFY", "true").lower() == "true"

    # Redshift (data warehouse)
    REDSHIFT_HOST = os.getenv("REDSHIFT_HOST", "")
    REDSHIFT_PORT = int(os.getenv("REDSHIFT_PORT", "5439"))
    REDSHIFT_USER = os.getenv("REDSHIFT_USER", "readonly")
    REDSHIFT_PASSWORD = os.getenv("REDSHIFT_PASSWORD", "")
    REDSHIFT_DATABASE = os.getenv("REDSHIFT_DATABASE", "productiondwh")

    # Trino (historical data > 30 days)
    TRINO_HOST = os.getenv("TRINO_HOST", "")
    TRINO_USER = os.getenv("TRINO_USER", "")
    TRINO_PASSWORD = os.getenv("TRINO_PASSWORD", "")

    # Athena (AWS Athena for ts_api and historical data)
    ATHENA_REGION = os.getenv("ATHENA_REGION", "us-east-1")
    ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "raw_data_db")
    ATHENA_OUTPUT_LOCATION = os.getenv("ATHENA_OUTPUT_LOCATION", "s3://aws-athena-query-results-fourkites/")
    ATHENA_AWS_ACCESS_KEY_ID = os.getenv("ATHENA_AWS_ACCESS_KEY_ID", "")
    ATHENA_AWS_SECRET_ACCESS_KEY = os.getenv("ATHENA_AWS_SECRET_ACCESS_KEY", "")
    ATHENA_AWS_SESSION_TOKEN = os.getenv("ATHENA_AWS_SESSION_TOKEN", "")

    # =============================================================================
    # FourKites APIs
    # =============================================================================

    # Authentication method: "hmac" or "basic"
    FK_API_AUTH_METHOD = os.getenv("FK_API_AUTH_METHOD", "hmac")

    # HMAC Authentication (recommended)
    FK_API_APP_ID = os.getenv("FK_API_APP_ID", "airflow-worker")
    FK_API_SECRET = os.getenv("FK_API_SECRET", "")  # HMAC-SHA1 secret

    # Basic Authentication (fallback)
    FK_API_USER = os.getenv("FK_API_USER", "")
    FK_API_PASSWORD = os.getenv("FK_API_PASSWORD", "")

    # Tracking API
    TRACKING_API_BASE_URL = os.getenv(
        "TRACKING_API_BASE_URL",
        "https://tracking-api-rr.fourkites.com"
    )

    # Company API
    COMPANY_API_BASE_URL = os.getenv(
        "COMPANY_API_BASE_URL",
        "https://company-api.fourkites.com"
    )

    # =============================================================================
    # Auto RCA Settings
    # =============================================================================

    # JIRA Configuration
    JIRA_SERVER = os.getenv("JIRA_SERVER", "https://fourkites.atlassian.net")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

    # LLM Provider Configuration
    # Choose your LLM provider: "anthropic" or "azure_openai"
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")

    # Anthropic Claude API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")  # Updated to Sonnet 4.5

    # Azure OpenAI Configuration (use when Anthropic limit reached)
    # Note: GPT-5 support will be added when available in Azure OpenAI
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")  # Latest available
    AZURE_OPENAI_REALTIME_DEPLOYMENT = os.getenv("AZURE_OPENAI_REALTIME_DEPLOYMENT", "gpt-4o-realtime-preview")

    # RCA Feature Flags
    ENABLE_AUTO_RCA = os.getenv("ENABLE_AUTO_RCA", "true").lower() == "true"

    # Frontend Feature Flag: Show Auto RCA button in UI
    # Set to "false" in production to hide the Auto RCA view mode switcher
    # Allows phased rollout: enable Timeline first, then Auto RCA after testing
    ENABLE_AUTO_RCA_FRONTEND = os.getenv("ENABLE_AUTO_RCA_FRONTEND", "true").lower() == "true"

    # Frontend Feature Flag: Show Manual Log Search button in UI
    # Set to "false" to hide the Manual Log Search view mode switcher
    # Useful for limiting access to advanced log search features
    ENABLE_MANUAL_LOG_SEARCH = os.getenv("ENABLE_MANUAL_LOG_SEARCH", "true").lower() == "true"

    # =============================================================================
    # Feature Flags
    # =============================================================================

    # Enable/disable specific data sources
    ENABLE_SIGNOZ_CLICKHOUSE = os.getenv("ENABLE_SIGNOZ_CLICKHOUSE", "true").lower() == "true"
    ENABLE_REWIND_CLICKHOUSE = os.getenv("ENABLE_REWIND_CLICKHOUSE", "true").lower() == "true"
    ENABLE_REDSHIFT = os.getenv("ENABLE_REDSHIFT", "true").lower() == "true"
    ENABLE_TRINO = os.getenv("ENABLE_TRINO", "false").lower() == "true"
    ENABLE_ATHENA = os.getenv("ENABLE_ATHENA", "true").lower() == "true"

    # DEPRECATED: Legacy ENABLE_CLICKHOUSE for backward compatibility
    # Now maps to ENABLE_SIGNOZ_CLICKHOUSE
    if os.getenv("ENABLE_CLICKHOUSE"):
        ENABLE_SIGNOZ_CLICKHOUSE = os.getenv("ENABLE_CLICKHOUSE", "true").lower() == "true"

    # =============================================================================
    # Query Chunking Feature Flags
    # =============================================================================
    # Enable 7-day chunking for Athena queries (performance optimization)
    # When disabled, queries run in a single shot for the entire date range

    # Chunk ts_api queries (API calls history)
    ENABLE_TS_API_CHUNKING = os.getenv("ENABLE_TS_API_CHUNKING", "true").lower() == "true"

    # Chunk callbacks_v2 queries (callback delivery history)
    ENABLE_CALLBACKS_CHUNKING = os.getenv("ENABLE_CALLBACKS_CHUNKING", "true").lower() == "true"

    # Chunk location_processing_flow queries (carrier file processing)
    ENABLE_CARRIER_FILES_CHUNKING = os.getenv("ENABLE_CARRIER_FILES_CHUNKING", "true").lower() == "true"

    # =============================================================================
    # Logging & Monitoring
    # =============================================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

    # =============================================================================
    # CORS Settings
    # =============================================================================
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    ).split(",")

    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present"""
        errors = []

        # Check Redshift connection
        if cls.ENABLE_REDSHIFT and not cls.REDSHIFT_HOST:
            errors.append("REDSHIFT_HOST is required when Redshift is enabled")

        # Check SigNoz ClickHouse connection
        if cls.ENABLE_SIGNOZ_CLICKHOUSE and not cls.SIGNOZ_CLICKHOUSE_HOST:
            errors.append("SIGNOZ_CLICKHOUSE_HOST is required when SigNoz ClickHouse is enabled")

        # Check Rewind ClickHouse connection
        if cls.ENABLE_REWIND_CLICKHOUSE and not cls.REWIND_CLICKHOUSE_HOST:
            errors.append("REWIND_CLICKHOUSE_HOST is required when Rewind ClickHouse is enabled")

        # Check API authentication
        if cls.FK_API_AUTH_METHOD == "hmac" and not cls.FK_API_SECRET:
            errors.append("FK_API_SECRET is required for HMAC authentication")
        elif cls.FK_API_AUTH_METHOD == "basic" and (not cls.FK_API_USER or not cls.FK_API_PASSWORD):
            errors.append("FK_API_USER and FK_API_PASSWORD are required for basic authentication")

        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    # Client configuration properties
    @property
    def salesforce(self):
        """Get Salesforce configuration"""
        if not hasattr(self, '_salesforce'):
            self._salesforce = SalesforceConfig()
        return self._salesforce

    @property
    def justtransform(self):
        """Get JustTransform configuration"""
        if not hasattr(self, '_justtransform'):
            self._justtransform = JustTransformConfig()
        return self._justtransform

    @property
    def super_api(self):
        """Get Super API configuration"""
        if not hasattr(self, '_super_api'):
            self._super_api = SuperApiConfig()
        return self._super_api

    @property
    def redshift(self):
        """Get Redshift configuration"""
        if not hasattr(self, '_redshift'):
            self._redshift = RedshiftConfig()
        return self._redshift

    @property
    def clickhouse(self):
        """Get ClickHouse configuration"""
        if not hasattr(self, '_clickhouse'):
            self._clickhouse = ClickHouseConfig()
        return self._clickhouse

    @property
    def tracking_api(self):
        """Get Tracking API configuration"""
        if not hasattr(self, '_tracking_api'):
            self._tracking_api = TrackingAPIConfig()
        return self._tracking_api

    @property
    def llm(self):
        """Get LLM configuration"""
        if not hasattr(self, '_llm'):
            self._llm = LLMConfig()
        return self._llm

    @property
    def max_parallel_tasks(self):
        """Get max parallel tasks"""
        return int(os.getenv("MAX_PARALLEL_TASKS", "5"))

    @property
    def default_timeout(self):
        """Get default timeout"""
        return float(os.getenv("DEFAULT_TIMEOUT", "60.0"))


# =============================================================================
# Client-specific config classes
# =============================================================================

class SalesforceConfig:
    """Salesforce API configuration"""

    def __init__(self):
        self.username = os.getenv("SALESFORCE_USERNAME", "")
        self.password = os.getenv("SALESFORCE_PASSWORD", "")
        self.security_token = os.getenv("SALESFORCE_SECURITY_TOKEN", "")
        self.domain = os.getenv("SALESFORCE_DOMAIN", "login")

    def is_configured(self) -> bool:
        """Check if Salesforce is properly configured"""
        return bool(self.username and self.password and self.security_token)

    @classmethod
    def from_env(cls):
        return cls()


class JustTransformConfig:
    """JustTransform API configuration"""

    def __init__(self):
        self.base_url = os.getenv("JT_BASE_URL", "https://api.justtransform.com")
        self.username = os.getenv("JT_USERNAME", "")
        self.password = os.getenv("JT_PASSWORD", "")

    def is_configured(self) -> bool:
        """Check if JustTransform is properly configured"""
        return bool(self.username and self.password)

    @classmethod
    def from_env(cls):
        return cls()


class SuperApiConfig:
    """FourKites Super API configuration (DataHub API)"""

    def __init__(self):
        self.base_url = os.getenv("SUPER_API_BASE_URL", "")
        self.timeout = int(os.getenv("SUPER_API_TIMEOUT", "30"))

        # Super API uses FK_API Basic Auth credentials (no separate API key)
        self.user = os.getenv("FK_API_USER", "")
        self.password = os.getenv("FK_API_PASSWORD", "")

    def is_configured(self) -> bool:
        """Check if Super API is properly configured"""
        return bool(self.base_url and self.user and self.password)

    @classmethod
    def from_env(cls):
        return cls()


class RedshiftConfig:
    """Redshift configuration"""

    def __init__(self):
        self.host = os.getenv("REDSHIFT_HOST", "")
        self.port = int(os.getenv("REDSHIFT_PORT", "5439"))
        self.database = os.getenv("REDSHIFT_DATABASE", "productiondwh")
        self.user = os.getenv("REDSHIFT_USER", "readonly")
        self.password = os.getenv("REDSHIFT_PASSWORD", "")

    def is_configured(self) -> bool:
        """Check if Redshift is properly configured"""
        return bool(self.host and self.user and self.password)

    @classmethod
    def from_env(cls):
        return cls()


class ClickHouseConfig:
    """ClickHouse configuration"""

    def __init__(self):
        self.host = os.getenv("SIGNOZ_CLICKHOUSE_HOST", "localhost")
        self.port = int(os.getenv("SIGNOZ_CLICKHOUSE_PORT", "9000"))
        self.database = os.getenv("SIGNOZ_CLICKHOUSE_DATABASE", "signoz_logs")
        self.user = os.getenv("SIGNOZ_CLICKHOUSE_USER", "default")
        self.password = os.getenv("SIGNOZ_CLICKHOUSE_PASSWORD", "")

    def is_configured(self) -> bool:
        """Check if ClickHouse is properly configured"""
        return bool(self.host)

    @classmethod
    def from_env(cls):
        return cls()


class TrackingAPIConfig:
    """Tracking API configuration"""

    def __init__(self):
        self.base_url = os.getenv("TRACKING_API_BASE_URL", "https://tracking-api-rr.fourkites.com")
        self.auth_method = os.getenv("FK_API_AUTH_METHOD", "basic")
        self.user = os.getenv("FK_API_USER", "")
        self.password = os.getenv("FK_API_PASSWORD", "")
        self.app_id = os.getenv("FK_API_APP_ID", "")
        self.secret = os.getenv("FK_API_SECRET", "")

    def is_configured(self) -> bool:
        """Check if Tracking API is properly configured"""
        if self.auth_method == "basic":
            return bool(self.user and self.password)
        else:  # hmac
            return bool(self.app_id and self.secret)

    @classmethod
    def from_env(cls):
        return cls()


class LLMConfig:
    """LLM configuration"""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "azure_openai")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

    @classmethod
    def from_env(cls):
        return cls()


# Create singleton instance
config = Config()
