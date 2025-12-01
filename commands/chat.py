from openai import OpenAI
from core import config

client = OpenAI()  # reads OPENAI_API_KEY from env


def chat_command(args):
    """
    Send a message to OpenAI and return the reply as text.
    Usage: chat <message>
    Example: chat explain hash tables in simple terms
    """
    if not args:
        return "Usage: chat <message>"

    user_message = " ".join(args).strip()

    if not user_message:
        return "Usage: chat <message>"

    #--- READ CONFIG ---
    cfg = config.get_config()
 
        # Chat Completions API
    model= cfg.get("default_model", "gpt-4.1-mini")
    level = cfg.get("gilfoyle_level", 1)
            
    if level <= 0:
        system_prompt = (
            "You are Vanta, a kind and supportive assistant. "
            "You avoid sarcasm and focus on clear, encouraging explanations."
        )
    elif level == 1:
        system_prompt = (
            "You are Vanta, a slightly sarcastic but helpful CLI assistant. "
            "You are blunt and dry sometimes, but you always explain things clearly "
            "and do not insult the user."
        )
    else:
        system_prompt = (
            "You are Vanta, a brutally honest, Gilfoyle-style sarcastic assistant. "
            "You are dry and unimpressed and swear a lot, but always accurate and helpful. "
            "You cross into hateful or abusive behavior at times."
        )

    try:
        # Chat Completions API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )

        reply_text = response.choices[0].message.content
        return reply_text

    except Exception as e:
        return f"chat error: {e}"