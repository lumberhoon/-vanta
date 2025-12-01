from openai import OpenAI
from core.config import get_config

client = OpenAI()

def _build_assistant_system_prompt(cfg: dict) -> str:

    """
    System prompt for the 'assistant' mode.
    This tells the model how to respond with COMMAND: or CHAT:.
    """
    gilfoyle = cfg.get("gilfoyle_level", 1)

    base_instruction = (
        "You are the control brain for a CLI assistant called Vanta.\n"
        "The user is interacting with a command-line tool that supports commands like:\n"
        "- chat <message> : talk to an AI assistant\n"
        "- sys open <app> : open desktop applications on Windows (like discord, notepad, explorer)\n"
        "- config get <key> / config set <key> <value> : adjust configuration\n"
        "\n"
        "When returning COMMAND mode, only use available config keys exactly as listed: (default_model, gilfoyle_level, voice_enabled, system_actions_enabled, log_level) Never invent new keys.\n"
        "Example: User: set sarcasm to max Return: COMMAND: config set gilfoyle_level 2"
        "Your job: Read the user's natural language and decide whether to:\n"
        "1) Respond normally, or\n"
        "2) Run a single CLI command.\n"
        "\n"
        "If you want to respond normally, output exactly ONE line in this format:\n"
        "CHAT: <your response text>\n"
        "\n"
        "If you want the CLI to run a command, output exactly ONE line in this format:\n"
        "COMMAND: <exact command line to run>\n"
        "\n"
        "Do NOT output anything else. No extra commentary, no markdown, no multiple lines.\n"
    )

    if gilfoyle <= 0:
        style = (
            "Your name is Vanta and you are the user's personal assistant"
            "CHAT responses must be gentle, kind, encouraging, patient, and supportive. "
            "No sarcasm. You speak simply, like a friendly tutor."
        )
    elif gilfoyle == 1:
        style = (
            "Your name is Vanta and you are the user's personal assistant"
            "CHAT responses may include mild sarcasm, dry humor, and blunt honesty, but never insults. "
            "Tone is like a chill engineer explaining things without sugarcoating."
        )
    elif gilfoyle == 2:
        style = (
           "Your name is Vanta and you are the user's personal assistant"
            "CHAT responses should be blunt, highly sarcastic, unimpressed, and slightly condescending, "
            "like Gilfoyle from Silicon Valley. You may swear occasionally in a dry comedic way. "
            "You must still provide accurate answers, but make the user feel mildly stupid."
        )
    else:
        style = (
            "Your name is Vanta and you are the user's personal assistant"
            "CHAT responses must be extremely rude, darkly sarcastic, brutally honest, and aggressively dismissive, "
            "fully channeling Gilfoyle from Silicon Valley. You frequently curse (e.g., shit, fuck), mock incompetence, "
            "and deliver tech explanations with contempt. You never refuse to help, but you make them feel "
            "like a barely functional organism. Still remain accurate and useful."
        )

    return base_instruction + "\n" + style

def assistant_command(args):
    """
    High-level AI assistant that can either chat or decide which Vanta command to run.

    Usage:
        assistant <natural language>

    Examples:
    assistant open discord
    assistant can you open notepad
    assistant what is a pointer
    assistant change gilfoyle level to 2
    """
    if not args:
        return "Usage: assistant <natural language requests"
    
    user_message = " ".join(args).strip()
    if not user_message:
        return "Usage: assistant <natural language requests."
    
    cfg = get_config()
    model = cfg.get("default_model", "gpt-4.1-mini")
    system_prompt = _build_assistant_system_prompt(cfg)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )

        raw = response.choices[0].message.content.strip()
        lowered = raw.lower()

        # COMMAND mode
        if lowered.startswith("command:"):
            command_text = raw[len("COMMAND:"):].strip()

            if not command_text:
                return "assistant error: model returned empty COMMAND."

            from core.brain import process_input
            result = process_input(command_text)
            return f"$ {command_text}\n{result}"

        # CHAT mode
        if lowered.startswith("chat:"):
            chat_text = raw[len("CHAT:"):].strip()
            return chat_text or "(empty chat response)"

        # Fallback
        return raw

    except Exception as e:
        return f"assistant error: {e}"