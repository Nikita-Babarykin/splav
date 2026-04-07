from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str
    allowed_user_ids: set[int]
    style_examples_path: Path
    max_input_chars: int


def _parse_user_ids(raw_value: str) -> set[int]:
    user_ids: set[int] = set()

    for chunk in raw_value.split(","):
        cleaned = chunk.strip()
        if not cleaned:
            continue
        user_ids.add(int(cleaned))

    return user_ids


def _resolve_examples_path(raw_path: str, base_dir: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return base_dir / path


def load_settings() -> Settings:
    load_dotenv()

    project_root = Path(__file__).resolve().parent.parent

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    allowed_user_ids_raw = os.getenv("ALLOWED_USER_IDS", "")
    style_examples_path = _resolve_examples_path(
        os.getenv("STYLE_EXAMPLES_PATH", "data/style_examples.txt"),
        project_root,
    )
    max_input_chars = int(os.getenv("MAX_INPUT_CHARS", "12000"))

    if not telegram_bot_token:
        raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env")

    if not openai_api_key:
        raise ValueError("Не найден OPENAI_API_KEY в .env")

    return Settings(
        telegram_bot_token=telegram_bot_token,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        allowed_user_ids=_parse_user_ids(allowed_user_ids_raw),
        style_examples_path=style_examples_path,
        max_input_chars=max_input_chars,
    )
