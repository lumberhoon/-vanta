from core.config import get_config, save_config

BOOL_KEYS = {"voice_enabled", "system_actions_enabled"}
INT_KEYS = {"gilfoyle_level"}


def _parse_value_for_key(key: str, raw_value: str):
    # Convert string from the CLI into the right Python type."
    if key in INT_KEYS:
        try:
            return int(raw_value), None
        except ValueError:
            return None, f"Invalid value for {key}. Expected an integer, got '{raw_value}'."
        
    if key in BOOL_KEYS:
        val = raw_value.lower()
        if val in {"true", "on", "1", "yes"}:
            return True, None
        if val in {"false", "off", "0", "no"}:
            return False, None
        return None, f"Invalid value for {key}. Use true/false, on/off, yes/no, 1/0."
    
    #default: leave as string
    return raw_value, None


def config_command(args):
    """
    Manage Vanta's configuration.
    Usage:
        config show
        config get <key>
        config set <key> <value>
    """
    cfg = get_config()

    if not args or args[0] in {"help", "-h", "--help"}:
        return (
            "Config commands:\n"
            "   config show         -show all config values\n"
            "   config get <key>    -show a single config value\n"
            "   config set <key> <value>    -update a config value\n"
            "\n"
            f"Available keys: {', '.join(cfg.keys())}"
        )
    sub = args[0]

    if sub == "show":
        lines = ["Current configuration:"]
        for key, value in cfg.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)
    
    if sub == "get":
        if len(args) < 2:
            return "Usage: config get <key>"
        
        key = args[1]
        if key not in cfg:
            return f"Unknown config key: {key}"
        
        return f"{key} = {cfg[key]}"
    
    if sub == "set":
        if len(args) < 3:
            return "Usage: config set <key> <value>"
        
        key = args[1]
        raw_value = " ".join(args[2:])

        if key not in cfg:
            return f"Unknown config key: {key}"
        
        parsed_value, error = _parse_value_for_key(key, raw_value)
        if error:
            return error
        
        cfg[key] = parsed_value
        save_config(cfg)

        return f"Updated {key} = {parsed_value}"
    
    return "Unknown config subcommand. Try: config help"