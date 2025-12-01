from pathlib import Path

def notes_command(args):
    notes_file = Path("notes.txt")

    if not args:
        return "Usage: notes add <text> | notes list"
    
    sub = args[0].lower()
    rest = " ".join(args[1:]).strip()

    if sub == "add":
        if not rest:
            return "Cannot add empty note."
        
        # append note to file
        with notes_file.open("a", encoding="utf-8") as f:
            f.write(rest + "\n")

            return "✓ Note added."
        
    if sub in ("list", "ls"):
        if not notes_file.exists():
            return "No notes yet."
        
        lines = notes_file.read_text(encoding="utf-8").splitlines()
        if not lines:
            return "No notes yet."
        
        out_lines = ["Notes:"]
        for i, line in enumerate(lines, start=1):
            out_lines.append(f"{i}. {line}")

        return "\n".join(out_lines)
    return "Unknown notes command. Usage: notes add <text> | notes list"