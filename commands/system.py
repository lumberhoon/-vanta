# commands/system.py
import platform
import subprocess
from pathlib import Path
from tkinter import filedialog
import json
from core import config
from core.paths import ALIAS_FILE

APP_ALIASES = {
    "chrome": "chrome",
    "edge": "msedge",
    "explorer": "explorer",
    "file-explorer": "explorer",
    "notepad": "notepad",
    "chatgpt": "chatgpt"
}

def _load_user_aliases() -> dict[str, str]:
    try:
        if not ALIAS_FILE.exists():
            return {}
        with ALIAS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        # ensure keys/values are strings
        return {str(k).lower(): str(v) for k, v in data.items()}
    except Exception:
        return {}


def _save_user_aliases(user_aliases: dict[str, str]) -> None:
    try:
        with ALIAS_FILE.open("w", encoding="utf-8") as f:
            json.dump(user_aliases, f, indent=2)
    except Exception:
        # don't crash if disk write fails
        pass


def _get_app_aliases() -> dict:
    """
    Merge built-in aliases with user-defined ones from config
    user-defined overrieds built-ins
    """
    user_aliases = _load_user_aliases()
    merged = {**APP_ALIASES, **user_aliases}
    return merged



def _system_actions_allowed() -> bool:
    cfg = config.get_config()
    return cfg.get("system_actions_enabled", False)

def _open_app(target: str) -> str:
    """
    Try to open a desktop application by name.
    Currently implemented for Windows Only
    """

    system = platform.system().lower()
    target_key = target.lower().strip()

    app_aliases = _get_app_aliases()
    app_cmd = app_aliases.get(target_key, target)

    if system != "windows":
        return "System actions: only Windows is supported right now. "
    
    if not _system_actions_allowed():
        return (
            "System actions are disabled in config. "
            "Enabled them with: config set system_actions_enabled true"
        )

    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "", app_cmd],
            shell = False,
        )
        return f"Launching {target_key}..."
    except Exception as e:
        return f"Failed to launch {target_key} {e}"
    

def _system_info() -> str:
    # Return a simple multi-line system info summary
    system = platform.system()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    proc = platform.processor() or "Unknown CPU"

    lines = [
        "System information:",
        f" OS: {system} {release}",
        f" Version: {version}",
        f" Machine: {machine}",
        f" CPU: {proc}",
    ]
    return "\n".join(lines)

def system_command(args):
    """System-related commands"""

    if not args or args[0] in {"help", "-h", "--help"}:
        return (
            "[sys] System command usage:\n"
            "  sys                 - show this help\n"
            "  sys info            - show basic system info\n"
            "  sys listapps        - list all known app aliases\n"
            "  sys addapp          - add or override an app alias (interactive file picker)\n"
            "  sys removeapp <name>- remove a user-defined app alias\n"
            "\n"
            "You can also use natural language:\n"
            "  open chrome\n"
            "  launch discord\n"
            "  start vscode\n"
        )
    
    sub = args[0].lower()

    if sub == "info":
        return _system_info()
    
    if sub == "open":
        if len(args) < 2:
            return "Usage: sys open <app>"
        target = " ".join(args[1:])
        return _open_app(target)
    
    
    if sub == "addapp":
        if len(args) < 2:
            return "Usage: sys addapp <simple_name>\nExample: sys addapp photoshop"
        name = args[1]
        return _add_app_interactive(name)
    
    if sub == "listapps":
        return _list_apps()
    
    if sub == "removeapp":
        if len(args) < 2:
            return "Usage: sys removeapp <name>"
        name = args[1]
        return _remove_app(name)
    
    
    return "Unknown sys sub command. Try: sys help"

def _add_app_interactive(name: str) -> str:

    #User picks an exe for a given alias name
    path = filedialog.askopenfilename(
        title = f"Select program for {name}",
        filetypes = [
            ("Executables", "*.exe *.bat *.cmd *.lnk"),
            ("All files", "*.*"),
        ],
    )
    if not path:
        return "[sys] App mapping cancelled."
    
    user_aliases = _load_user_aliases()
    user_aliases[name.lower()] = path
    _save_user_aliases(user_aliases)

    return (
        f"[sys] Added alias '{name}' -> {path}\n"
        f"You can now say: open {name}"
    )

def _list_apps() -> str:
    
    app_aliases = _get_app_aliases()

    if not app_aliases:
        return "[sys] No app aliases configured yet."
    
    lines = ["[sys] Known app aliases:"]

    for name in sorted(app_aliases.keys()):
        cmd = app_aliases[name]
        lines.append(f"  {name:12} -> {cmd}")

    return "\n".join(lines)


def _remove_app(name: str) -> str:

    key = name.lower().strip()

    user_aliases = _load_user_aliases()

    if key in user_aliases:

        removed_cmd = user_aliases.pop(key)
        _save_user_aliases(user_aliases)
        return (
            f"[sys] Removed user alias '{key}'\n"
            f"   (Previously mapped to: {removed_cmd})"
        )
    
    app_aliases = _get_app_aliases()
    if key in app_aliases:
        return (
            f"[sys] '{key}' is a built-in alias.\n"
            f"You can't remove it, but you can override it by using:\n"
            f"  sys addapp {key}"
        )
    
    return f"[sys] No alias named '{key}' found."