from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Cyber Incident Tracker API"
    database_url: str = "postgresql+psycopg://incident_user:incident_pass@localhost:5432/incident_tracker"
    redis_url: str = "redis://localhost:6379/0"
    api_v1_prefix: str = "/api/v1"
    databreaches_feed_url: str = "https://www.databreaches.net/feed/"
    hhs_ocr_frontpage_url: str = "https://ocrportal.hhs.gov/ocr/breach/breach_frontpage.jsf"
    hhs_ocr_report_url: str = "https://ocrportal.hhs.gov/ocr/breach/breach_report_hip.jsf"
    sec_8k_feed_url: str = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-k&company=&dateb=&owner=include&start=0&count=100&output=atom"
    sec_user_agent: str = "IncidentFinder/0.1 (security-research@example.com)"
    connector_max_records: int = 50
    auto_create_org_sources: str = "sec_edgar_8k,hhs_ocr"
    require_api_key: bool = False
    api_keys: str = ""
    default_tenant_id: str = "default"
    default_user_role: str = "manager"
    manager_roles: str = "manager,admin"
    enable_email_alerts: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_use_tls: bool = False
    smtp_username: str = ""
    smtp_password: str = ""
    alerts_from_email: str = "alerts@incidentfinder.local"
    alert_retry_max_attempts: int = 3
    alert_retry_backoff_seconds: int = 60
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    trusted_hosts: str = "localhost,127.0.0.1,testserver"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
