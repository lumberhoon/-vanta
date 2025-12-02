import tkinter as tk
from tkinter import scrolledtext
import threading
from core.paths import CHAT_HISTORY_FILE

from core.brain import process_input
from core.audio_io import start_recording, stop_and_transcribe, speak_text, play_ptt_ping
from core.hotkeys import GlobalPTTListener




class VantaGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("VANTA 0.1")
        self.thinking_after_id = None

        #track whether we're currently recording audio
        self.is_recording = False

        #Configure main window grid
        self.root.rowconfigure(0, weight = 1)
        self.root.rowconfigure(1, weight = 0)
        self.root.columnconfigure(0, weight = 1)

        #Text area for history
        self.output = scrolledtext.ScrolledText(
            self.root,
            wrap = tk.WORD,
            state = "disabled",
            height = 20,
        )
        self.output.grid(row = 0, column = 0, sticky = "nsew", padx = 8, pady = 8)

        self.history_file = CHAT_HISTORY_FILE
        self.history_loading = False
        self._load_chat_history(max_lines = 200)


        # Frame for input + button
        input_frame = tk.Frame(self.root)
        input_frame.grid(row =1, column = 0, sticky = "ew", padx = 8, pady = (0, 8))
        input_frame.columnconfigure(0, weight = 1)
        input_frame.columnconfigure(1, weight = 0)

        # Entry where the user types commands
        self.entry = tk.Entry(input_frame)
        self.entry.grid(row = 0, column = 0, sticky = "ew", padx = (0, 4))
        self.entry.bind("<Return>", self.on_enter)

        #Bind push-to-talk to F4 key
        self.root.bind("<KeyPress-F4>", self.on_ptt_press)
        self.root.bind("<KeyRelease-F4>", self.on_ptt_release)

        # Send button
        send_button = tk.Button(input_frame, text = "Send", command = self.on_send)
        send_button.grid(row = 0, column = 1)

        #Print initial banner


        self._append_text(
            "> VANTA 0.1 online\n"
            "Type commands (help, chat, sys, assistant, config ...)\n"
            "Hold F4 to talk (push-to-talk).\n\n"
        )
        
        #Global PTT
        self.ptt_listener = GlobalPTTListener(self, key = "f4")
        self.ptt_listener.start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self.entry.focus_set()

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