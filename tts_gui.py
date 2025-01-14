import tkinter as tk
from tkinter import ttk, messagebox
from models import build_model
import torch
import soundfile as sf
from kokoro import generate
from datetime import datetime
import os
import threading  

SAMPLE_RATE = 24000
OUTPUT_FOLDER = "output"

class ModernTTSApp:
    def __init__(self):
        self.VOICES = {
             "Emma": "bf_emma",
             "Bella": "af_bella",
             "Nicole": "af_nicole",
             "Sarah": "af_sarah",
             "Sky": "af_sky",
             "Adam": "am_adam",
             "Michael": "am_michael",
             "Isabella": "bf_isabella",
             "George": "bm_george",
             "Lewis": "bm_lewis",
        }
        self.is_generating = False
        
        self.setup_window()
        self.style = ttk.Style()
        self.create_styles()
        self.create_widgets()
        self.setup_bindings()

    def setup_window(self):
        self.root = tk.Tk()
        self.root.title("Kokoro TTS")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        self.root.configure(bg="#f5f5f5")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

    def create_styles(self):
        self.style.configure("Title.TLabel",
                      font=("Helvetica", 24, "bold"),
                      padding=10)
        
        self.style.configure("Header.TLabel",
                      font=("Helvetica", 12, "bold"))
        
        self.style.configure("Custom.TButton",
                      padding=10,
                      relief="flat",
                      borderwidth=0)
        
        self.style.configure("Custom.Horizontal.TProgressbar",
                      troughcolor="#E0E0E0",
                      background="#4CAF50",
                      borderwidth=0,
                      thickness=10)
        
        self.style.configure("Rounded.TLabelframe",
                      borderwidth=2,
                      relief="solid",
                      padding=15)
        
        self.style.configure("Rounded.TLabelframe.Label",
                      font=("Helvetica", 11, "bold"))

    def create_widgets(self):
        # Title
        title = ttk.Label(self.main_frame,
                         text="Kokoro Text-to-Speech",
                         style="Title.TLabel")
        title.grid(row=0, column=0, pady=(0, 20))

        # Create content frame
        content_frame = ttk.Frame(self.main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)

        # Voice selection frame
        voice_frame = ttk.LabelFrame(content_frame,
                                   text="Voice Selection",
                                   padding="15",
                                   style="Rounded.TLabelframe")
        voice_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.voice_var = tk.StringVar(value=list(self.VOICES.keys())[0])
        voice_dropdown = ttk.Combobox(voice_frame,
                                    textvariable=self.voice_var,
                                    values=list(self.VOICES.keys()),
                                    state="readonly",
                                    width=30)
        voice_dropdown.grid(row=0, column=0, padx=5)

        # Text input frame
        text_frame = ttk.LabelFrame(content_frame,
                                  text="Input Text",
                                  padding="15",
                                  style="Rounded.TLabelframe")
        text_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        # Text input with scrollbar
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.grid(row=0, column=1, sticky="ns")
        
        self.text_input = tk.Text(text_frame,
                                height=10,
                                yscrollcommand=text_scroll.set,
                                wrap=tk.WORD,
                                font=("Helvetica", 11),
                                padx=10,
                                pady=10,
                                relief="flat",
                                bg="#ffffff",
                                insertbackground="#333333")
        self.text_input.grid(row=0, column=0, sticky="nsew")
        text_scroll.config(command=self.text_input.yview)

        # Bottom frame
        bottom_frame = ttk.Frame(content_frame)
        bottom_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        bottom_frame.columnconfigure(0, weight=1)

        # Status frame
        status_frame = ttk.Frame(bottom_frame)
        status_frame.grid(row=0, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        self.progress_label = ttk.Label(status_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Progress bar (always visible but with opacity)
        self.progress_bar = ttk.Progressbar(
            status_frame,
            style="Custom.Horizontal.TProgressbar",
            mode="determinate"
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew")
        
        # Set initial state to "hidden" (transparent)
        self.progress_bar["value"] = 0
        self.style.configure("Custom.Horizontal.TProgressbar",
                           background="#4CAF50",
                           troughcolor="#E0E0E0",
                           opacity=0)

        # Control frame
        control_frame = ttk.Frame(bottom_frame)
        control_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        control_frame.columnconfigure(1, weight=1)

        # Character count label
        self.char_count_label = ttk.Label(control_frame,
                                        text="Characters: 0",
                                        style="Header.TLabel")
        self.char_count_label.grid(row=0, column=0, sticky="w")

        # Generate button
        self.generate_button = ttk.Button(
            control_frame,
            text="Generate Audio",
            style="Custom.TButton",
            command=self.generate_audio
        )
        self.generate_button.grid(row=0, column=2, sticky="e")

    def setup_bindings(self):
        self.text_input.bind('<KeyRelease>', self.update_char_count)

    def update_char_count(self, event=None):
        count = len(self.text_input.get("1.0", tk.END).strip())
        self.char_count_label.config(text=f"Characters: {count}")

    def toggle_ui_state(self, generating):
        if generating:
            self.text_input.config(state=tk.DISABLED)
            self.generate_button.config(text="Cancel")
            self.style.configure("Custom.Horizontal.TProgressbar",
                               background="#4CAF50",
                               troughcolor="#E0E0E0",
                               opacity=1)
        else:
            self.text_input.config(state=tk.NORMAL)
            self.generate_button.config(text="Generate Audio")
            self.style.configure("Custom.Horizontal.TProgressbar",
                               background="#4CAF50",
                               troughcolor="#E0E0E0",
                               opacity=0)
            self.progress_label.config(text="Ready")

    def generate_audio(self):
        if self.is_generating:
            self.is_generating = False
            self.toggle_ui_state(False)
            self.progress_label.config(text="Generation canceled.")
            return

        self.is_generating = True
        self.toggle_ui_state(True)

        text = self.text_input.get("1.0", tk.END).strip()
        display_name = self.voice_var.get()
        voice_key = self.VOICES[display_name]

        if not text:
            messagebox.showerror("Error", "Please enter text.")
            self.toggle_ui_state(False)
            return

        # Define the audio generation task as a separate function
        def audio_generation_task():
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                MODEL = build_model("kokoro-v0_19.pth", device)
                VOICEPACK = torch.load(f"voices/{voice_key}.pt",
                                     weights_only=True).to(device)

                chunks = [chunk for chunk in text.split(".") if len(chunk) >= 2]
                total_chunks = len(chunks)

                # Update the progress bar's maximum value
                self.progress_bar["maximum"] = total_chunks

                audio = []
                for i, chunk in enumerate(chunks):
                    if not self.is_generating:
                        break

                    # Update the progress bar and label
                    self.progress_bar["value"] = i + 1
                    self.progress_label.config(
                        text=f"Processing chunk {i + 1} of {total_chunks}...")
                    self.root.update_idletasks()  # Force UI update

                    # Generate audio for the current chunk
                    snippet, _ = generate(MODEL, chunk, VOICEPACK,
                                       lang=voice_key[0])
                    audio.extend(snippet)

                if self.is_generating:
                    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    OUTPUT_FILE = f"{OUTPUT_FOLDER}/{voice_key}_output_{timestamp}.wav"
                    sf.write(OUTPUT_FILE, audio, SAMPLE_RATE)
                    
                    # Update the UI after successful generation
                    self.progress_label.config(text="Audio generated successfully!")
                    messagebox.showinfo("Success",
                                      f"Audio saved to {OUTPUT_FILE}")
                    # Reset the progress bar to 0 after the user clicks "OK"
                    self.progress_bar["value"] = 0

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
            finally:
                self.is_generating = False
                self.toggle_ui_state(False)

        # Start the audio generation task in a separate thread
        threading.Thread(target=audio_generation_task, daemon=True).start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ModernTTSApp()
    app.run()