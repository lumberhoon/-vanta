import tkinter as tk
from tkinter import scrolledtext
import threading
from core.paths import CHAT_HISTORY_FILE

from core.brain import process_input
from core.audio_io import start_recording, stop_and_transcribe, speak_text, play_ptt_ping
from core.hotkeys import GlobalPTTListener

# Retro IBM-style color palette
CHASSIS_BG = "#d9d7ca"   # off-white / beige plastic
TERM_BG    = "#000000"   # black terminal screen
TERM_FG    = "#00ff66"   # phosphor green text


class VantaGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("VANTA 0.2")
        self.thinking_after_id = None
        self.root.overrideredirect(True)
        self.is_recording = False
        self.is_fullscreen = False
        self._prev_geometry = NotImplemented
        
        #Build GUI layout
        self._build_gui()
        
        #Bind Fullscreen + Esc
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._on_escape)

        #Bind push-to-talk to F4 key
        self.root.bind("<KeyPress-F4>", self.on_ptt_press)
        self.root.bind("<KeyRelease-F4>", self.on_ptt_release)

        #Bind window drag movement

        #Print initial banner

        self._append_text(
            "> VANTA 0.2 online\n"
            "[Hotkeys]\n"
            " • F11 = Fullscreen\n"
            " • ESC = Exit Fullscreen\n"
            " • F4 = Push-to-talk\n"
            " • Enter = Submit text\n"
        )
        
        #Global PTT
        self.ptt_listener = GlobalPTTListener(self, key = "f4")
        self.ptt_listener.start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self.entry.focus_set()

    
    def _build_gui(self):

        self.root.columnconfigure(0, weight=1)
        self.root.configure(bg = CHASSIS_BG)
        self.root.rowconfigure(0, weight=0)  # drag bar
        self.root.rowconfigure(1, weight=1)
        

        self.drag_bar = tk.Frame(self.root, bg = CHASSIS_BG, height = 20)
        self.drag_bar.grid(row = 0, column = 0, sticky ="ew")

        title_label = tk.Label(
            self.drag_bar,
            text = "VANTA 0.2",
            bg = CHASSIS_BG,
            fg = "#000000",
            font = ("Courier New", 10)
        )
        title_label.pack(side = "left", padx = 8)

        self.drag_bar.bind("<Button-1>", self._start_move)
        self.drag_bar.bind("<B1-Motion>", self._do_move)

        crt_frame = tk.Frame(self.root, bg = CHASSIS_BG, padx = 20, pady = 20)
        crt_frame.grid(row = 1, column = 0, sticky = "nsew")
       
        crt_frame.columnconfigure(0, weight = 1)
        crt_frame.rowconfigure(0, weight = 1)
        crt_frame.rowconfigure(1, weight = 0)
    
        
        self.output = tk.Text(
            crt_frame,
            wrap = tk.WORD,
            state = "disabled",
            font = ("Courier New", 11),
            bg = TERM_BG,
            fg = TERM_FG,
            insertbackground = TERM_FG,
            borderwidth = 0,
            highlightthickness = 0
        )
        self.output.grid(row = 0, column = 0, sticky = "nsew")

        input_frame = tk.Frame(crt_frame, bg = TERM_BG)
        input_frame.grid(row = 1, column = 0, sticky = "ew")
        input_frame.columnconfigure(0, weight = 1)

        self.entry = tk.Entry(
            input_frame,
            font = ("Courier New", 11),
            bg = TERM_BG,
            fg = TERM_FG,
            insertbackground = TERM_FG,
            relief = "flat"
        )
        self.entry.grid(row = 0, column = 0, sticky = "ew", padx = (0, 6))
        
        self.entry.bind("<Return>", self.on_enter)

        self.send_button = tk.Button(
            input_frame,
            text = "Send",
            width = 8,
            command = self.on_send,
            bg = CHASSIS_BG,
            fg = "#000000",
            activebackground = "#c8c5b4",
            activeforeground = "#000000",
            relief = "raised"
        )
        self.send_button.grid(row = 0, column = 1, sticky = "e")

    
    def _start_move(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _do_move(self, event):
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")

    def _on_close(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _toggle_fullscreen(self, event = None):

        if not self.is_fullscreen:
            self._prev_geometry = self.root.geometry()
            self.root.overrideredirect(False)
            self.root.attributes("-fullscreen", True)
            self.is_fullscreen = True
        else:
            self.root.attributes("-fullscreen", False)
            self.is_fullscreen = False

        if self._prev_geometry:
            self.root.geometry(self._prev_geometry)
            
        self.root.overrideredirect(True)

    def _on_escape(self, event = None):
        
        if getattr(self, "is_fullscreen", False):
            self._toggle_fullscreen()
        else:
            self._on_close()
    
    
    def _process_text_async(self, user_text: str) -> None:
        """
        Run process_input in a background thread, thenupdate the GUI when it done
        No freezing
        """
        def worker():
            try:
                response = process_input(user_text)
            except Exception as e:
                response = f"[error] {e}"

            def update_gui():
                if response:
                    self._append_text(f"{response}\n\n")
            
            self.root.after(0, update_gui)
        threading.Thread(target = worker, daemon = True).start()

    
    def _process_voice_async(self) -> None:
        """
        Run stop_and_transcribe + process_input + speak_text in a background thread
        GUI updates scheduled via root.after
        """
        def worker():
            
            try:
                text = stop_and_transcribe()
            except Exception as e:
                error_msg = f"[voice error] {e}\n\n"

                def show_error():
                    self._append_text(error_msg)

                self.root.after(0, show_error)
                return
            
            if not text:
                def no_speech():
                    self._append_text("[voice] No speech detected.\n\n")
                self.root.after(0, no_speech)
                return
            
            def show_user_voice():
                self._append_text(f">>> [mic] {text}\n")
                #self._append_text("[Thinking]...\n")
            self.root.after(0, show_user_voice)

            def show_thinking():
                self.thinking_after_id = None
                self._append_text("[Thinking]...\n")
            
            
            self.thinking_after_id = self.root.after(2000, show_thinking)

            try: 
                response = process_input(text)
            except Exception as e:
                response = f"[error] {e}"

            def show_response():

                if self.thinking_after_id is not None:
                    self.root.after_cancel(self.thinking_after_id)
                    self.thinking_after_id = None

                if response:
                    self._append_text(f"{response}\n\n")
            self.root.after(0, show_response)

            try:
                if response:
                    speak_text(response)
            except Exception as e:
                def show_tts_error():
                    self._append_text(f"[tts error] {e}\n\n")
                self.root.after(0, show_tts_error)

        threading.Thread(target = worker, daemon = True).start()


    def _load_chat_history(self, max_lines: int = 200) -> None:
        
        try:
            if not self.history_file.exists():
                return

            with self.history_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()

            if max_lines is not None and max_lines > 0:
                lines = lines[-max_lines:]

            self._history_loading = True
            for line in lines:
                self._append_text(line)
        except Exception:
            pass
    
        finally:
            self._history_loading = False


    def _append_text(self, text: str) -> None:
        """Append text to the output area."""
        self.output.configure(state = "normal")
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.configure(state = "disabled")

        if getattr(self, "_history_loading", False):
            return
        
        try:
            if hasattr(self, "history_file") and self.history_file is not None:
                with self.history_file.open("a", encoding="utf-8") as f:
                    f.write(text)
        except Exception:
            pass

    def on_enter(self, event) -> None:
        """Handle pressing Enter in the entry box."""
        self.on_send()

    def on_send(self) -> None:
        """Read input, send it to Vanta, display the result."""
        user_text = self.entry.get().strip()
        if not user_text:
            return
        
        self._append_text(f">>> {user_text}\n")

        self.entry.delete(0, tk.END)

        self._process_text_async(user_text)

    def on_ptt_press(self, event=None):
        """
        Start recording when F4 is pressed.
        Ignore if we are already recording.
        """
        if self.is_recording:
            return

        self.is_recording = True
        self._append_text("[voice] Listening... (hold F4)\n")
        
        try:
            play_ptt_ping()
        except Exception:
            pass
        
        try:
            start_recording()
        except Exception as e:
            self._append_text(f"[voice error] failed to start recording {e}\n")
            self.is_recording = False
    

    def on_ptt_release(self, event = None):

        if not self.is_recording:
            return
    
        self.is_recording = False

        try:
            play_ptt_ping()
        except Exception:
            pass
       
        self._append_text("[voice] Processing audio...\n")

        self._process_voice_async()       

    
    def handle_global_ptt_down(self):
        self.root.after(0, self.on_ptt_press)

    def handle_global_ptt_up(self):
        self.root.after(0, self.on_ptt_release)

    def _on_close(self):
        try:
            if self.ptt_listener:
                self.ptt_listener.stop()
        except:
            pass

        self.root.destroy()


def main():
    root = tk.Tk()
    app = VantaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()