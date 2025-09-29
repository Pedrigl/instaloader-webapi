from pydantic import Field

try:
    from pydantic import BaseSettings
    _HAS_BASESETTINGS = True
except Exception:
    BaseSettings = None
    _HAS_BASESETTINGS = False
from pathlib import Path
from typing import Optional
import json
import os


# Determine .env path. Allow DOTENV_PATH env var to override location.
_dotenv_override = os.getenv('DOTENV_PATH')
if _dotenv_override:
    DOTENV_PATH = Path(_dotenv_override)
else:
    DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"

if DOTENV_PATH.exists():
    try:
        try:
            from dotenv import load_dotenv

            load_dotenv(dotenv_path=str(DOTENV_PATH), override=False)
        except Exception:
            with open(DOTENV_PATH, 'r', encoding='utf8') as _f:
                for _line in _f:
                    _line = _line.strip()
                    if not _line or _line.startswith('#') or '=' not in _line:
                        continue
                    _k, _v = _line.split('=', 1)
                    _k = _k.strip()
                    _v = _v.strip().strip('"').strip("'")
                    os.environ.setdefault(_k, _v)
    except Exception:
        pass

if _HAS_BASESETTINGS:
    class Settings(BaseSettings):

        DATABASE_URL: Optional[str] = Field(None, env="DATABASE_URL")
        LOG_LEVEL: str = "INFO"

        OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
        OPENAI_MODEL: str = Field("gpt-4o-mini", env="OPENAI_MODEL")

        WORKER_INTERVAL_SECONDS: int = 3600
        WORKER_TARGETS: str = ""          # e.g. "acct1,acct2,post:ABC"
        SUPERMARKET_TARGETS: str = ""     # e.g. "store_account1,store_account2"

        class Config:
            env_file = None
            env_file_encoding = "utf-8"
else:
    class Settings:
        def __init__(self):
            self.DATABASE_URL = os.getenv('DATABASE_URL')
            self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
            self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
            self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            self.WORKER_INTERVAL_SECONDS = int(os.getenv('WORKER_INTERVAL_SECONDS', '3600'))
            self.WORKER_TARGETS = os.getenv('WORKER_TARGETS', '')
            self.SUPERMARKET_TARGETS = os.getenv('SUPERMARKET_TARGETS', '')

def load_settings_from_optional_file(path_env: str = "CONFIG_FILE") -> Settings:
    cfg_file = os.getenv(path_env, "")
    if cfg_file and os.path.exists(cfg_file):
        with open(cfg_file, "r", encoding="utf8") as f:
            data = json.load(f) 
        return Settings(**data)

_settings: Optional[Settings] = None
def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings_from_optional_file()
    return _settings

def get_settings_dep() -> Settings:
    return get_settings()