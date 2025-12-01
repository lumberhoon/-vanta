import os
from pathlib import Path

def get_app_dir() -> Path:

    appdata = os.getenv("APPDATA")
    if appdata:
        base = Path(appdata)
    else:
        base = Path.home()

    app_dir = base / "Vanta"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

APP_DIR = get_app_dir()

LOG_FILE = APP_DIR / "vanta.log"
ALIAS_FILE = APP_DIR / "app_aliases.json"
CHAT_HISTORY_FILE = APP_DIR / "chat_history.log"