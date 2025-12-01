import keyboard
from core.logger import log

class GlobalPTTListener:
    def __init__(self, gui, key= 'f4'):
        self.gui = gui
        self.key = key
        self._listening = False
        self._press_hook = None
        self._release_hook = None
        self._ptt_active = False

    def start(self):
        if self._listening:
            return
        
        log(f"[HOTKEY] Started global PTT listener (key = {self.key})")
        self._listening = True

        self._press_hook = keyboard.on_press_key(self.key, self._on_key_down)
        self._release_hook = keyboard.on_release_key(self.key, self._on_key_up)

    def stop(self):
        if not self._listening:
            return
        
        log("[HOTKEY] Stopped global PTT listener")
        self._listening = False

        if self._press_hook:
            keyboard.unhook(self._press_hook)
            self._press_hook = None

        if self._release_hook:
            keyboard.unhook(self._release_hook)
            self._release_hook = None

    def _on_key_down(self, event):
        if not self._listening or self._ptt_active:
            return
        
        self._ptt_active = True
        log(f"[HOTKEY] Key down ({event.name})")
        self.gui.handle_global_ptt_down()

    def _on_key_up(self, event):
        if not self._listening or not self._ptt_active:
            return
        
        self._ptt_active = False
        log(f"[HOTKEY] Key up ({event.name})")
        self.gui.handle_global_ptt_up()
