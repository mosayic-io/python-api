import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        extra='allow',
        env_file_encoding='utf-8'
    )

    # Core settings
    debug_mode: bool = False
    environment: str = "development"
    gcp_project_id: str = ""

    # These are loaded from .env.local or environment variables
    supabase_service_role_key: str = ""
    supabase_url: str = ""
    api_key: str = ""
    openai_api_key: str = ""
    teamup_api_token: str = ""
    tinyurl_api_key: str = ""

    # Charm credentials loaded from .env.local or environment variables
    charm_client_id: str = ""
    charm_client_secret: str = ""
    charm_refresh_token: str = ""
    charm_api_key: str = ""
    charm_auth_base_url: str = "https://accounts.charmtracker.com"

    # Charm Tracker Facility Configuration
    charm_facility_id: int = 2639654000000021081

    # Provider IDs
    charm_provider_ids: dict = {
        "zoe_schroeder": 2639654000000065005,
        "deidre_schodroski": 2639654000000038005,
        "matthew_weiner": 2639654000000050015,
    }

    # Visit Type IDs
    charm_visit_type_ids: dict = {
        "bariatric_surgery": 2639654000000067009,
        "egd": 2639654000000067015,
        "follow-up_visit_in_person_15": 2639654000000067019,
        "follow-up_visit_in_person_20": 2639654000000067125,
        "follow-up_visit_telemed_15": 2639654000000427675,
        "follow-up_visit_telemed_20": 2639654000000067129,
        "general_surgery": 2639654000000067027,
        "general_surgery_consult_in_person_20": 2639654000000067033,
        "general_surgery_consult_telemed_20": 2639654000000067037,
        "platinum_consult_in_person_20": 2639654000000427731,
        "platinum_consult_telemed_20": 2639654000000067053,
        "platinum_follow_up_in_person_10": 2639654000000427733,
        "platinum_follow_up_telemed_10": 2639654000000067049,
        "post-op_visit_in_person_15": 2639654000000067045,
        "post-op_visit_telemed_15": 2639654000000427577,
        "pre-op_visit_in_person_15": 2639654000000067057,
        "pre-op_visit_telemed_15": 2639654000000067061,
        "registered_dietitian_telemed_20": 2639654000000427711,
        "weight_loss_consult_in_person_30": 2639654000000067065,
        "weight_loss_consult_telemed_30": 2639654000000067069,
    }

    # Appointment Status IDs
    charm_appointment_status_ids: dict = {
        "appointment_created": "2639654000000035061",
        "awaiting_new_patient_forms": "2639654000000035063",
        "cancelled_by_patient": "2639654000000021101",
        "cancelled_by_physician": "2639654000000021099",
        "checked_in": "2639654000000021093",
        "completed": "2639654000000046971",
        "confirmed": "2639654000000021089",
        "consulted": "2639654000000021095",
        "new_patient_forms_complete": "2639654000000046973",
        "no_show": "2639654000000021097",
        "not_arrived": "2639654000000021091",
        "ready_for_provider": "2639654000000046975",
        "rescheduled": "2639654000000021103",
        "roomed": "2639654000000046977",
        "visit_checkin_forms_complete": "2639654000000046979",
        "will_complete_forms_in_office": "2639654000000046981",
    }


@lru_cache()
def get_settings():
    """
    Get application settings instance.

    Uses lru_cache to ensure only one Settings instance is created
    and reused across the application lifecycle.
    """
    return Settings()
