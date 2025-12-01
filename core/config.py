import json
from pathlib import Path

CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
        "default_model": "gpt-4.1-mini",
        "gilfoyle_level": 1,
        "voice_enabled": False,
        "system_actions_enabled": False,
        "log_level": "info",
}



def load_config():
    #creates new file using defaults if it doesn't exist
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    #If file exists, try loading it
    try:
        with CONFIG_FILE.open("r", encoding= "utf-8") as f:
            cfg = json.load(f)
    except Exception:
        # if corrupting, rewrite it to default
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    #Merge missing keys from defaults without deleting user changes
    for key, value in DEFAULT_CONFIG.items():
        if key not in cfg:
            cfg[key] = value

    return cfg

def save_config(config_dict: dict):
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent = 4)

#Load config once when importing this module
CONFIG = load_config()

def get_config():
    return CONFIG