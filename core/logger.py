from datetime import datetime
from pathlib import Path
from core.paths import LOG_FILE

LOG_FILE_PATH: Path = LOG_FILE
                

def log(text: str):
    """
    Append a single log line to vanta.log with a timestamp.
    Example:
    [2025-11-26 16:40:12] command: ping
    """

    #Get current time as a readable string
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #Build one full long line
    line = f"[{timestamp}] {text}\n"

    #open the log file in append mode and write the line
    try:
        with LOG_FILE_PATH.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass