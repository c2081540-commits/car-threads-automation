from dataclasses import dataclass
import os


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    threads_user_id: str = os.getenv("THREADS_USER_ID", "")
    threads_access_token: str = os.getenv("THREADS_ACCESS_TOKEN", "")
    threads_api_version: str = os.getenv("THREADS_API_VERSION", "v1.0")
    timezone: str = os.getenv("TIMEZONE", "Asia/Tokyo")
    auto_publish: bool = _bool("AUTO_PUBLISH")
    image_base_url: str = os.getenv("IMAGE_BASE_URL", "")
    content_queue_path: str = os.getenv("CONTENT_QUEUE_PATH", "data/content_queue.json")
    published_log_path: str = os.getenv("PUBLISHED_LOG_PATH", "data/published.json")


settings = Settings()

