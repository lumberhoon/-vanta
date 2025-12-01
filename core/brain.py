# core/brain.py

from commands.system import system_command
from commands.code import code_command
from commands.notes import notes_command
from commands.chat import chat_command
from core.logger import log
from commands.config import config_command
from commands.assistant import assistant_command
import string

def process_input(text: str) -> str:
    """
    Core Brain entrypoint for Vanta 0.1.
    Takes raw user text and decides what to do with it.
    """
    text = text.strip()
    if not text:
        return "Say something useful."

    parts = text.split()
    if not parts:
        return "Say something useful."

    # Clean ONLY the command token (first word)
    cmd_token = parts[0]
    cmd = cmd_token.lower().strip(string.punctuation)

    args = [a.strip(string.punctuation) for a in parts[1:]]


    if cmd in ("open", "launch", "start") and args:
        log(f"[BRAIN] Natural system command: {text}")
        return system_command(["open", *args])
        


    # routing table
    commands = {
        "help": lambda _: "Commands: ping, hi, hello, chat, sys, code, notes, help, exit",
        "ping": lambda _: "pong",
        "hi": lambda _: "Don't get attached",
        "hello": lambda _: "Don't get attached",
        "chat": chat_command,
        "notes": notes_command,
        "sys": system_command,
        "addapp": lambda args: system_command(["addapp", *args]),
        "removeapp": lambda args: system_command(["removeapp", *args]),
        "code": code_command,
        "config": config_command,
        "assistant": assistant_command,
    }

    handler = commands.get(cmd)

    if handler is None:
        log(f"[BRAIN] Natural language assistant: {text}")
        return assistant_command([text])

    # call the handler with args
    result = handler(args)
    log(f"Result: {result}")
    return result