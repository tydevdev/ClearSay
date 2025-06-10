import customtkinter as ctk
import os
import queue
from datetime import datetime
import wave
from tkinter import filedialog

from model import run_model
import numpy as np
import sounddevice as sd

# Configure appearance for dark mode

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Directory where recordings and transcripts are stored
RECORDING_DIR = "recorded_audio"
TRANSCRIPT_DIR = "transcripts"
os.makedirs(RECORDING_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

recording = False
audio_queue: queue.Queue[np.ndarray] = queue.Queue()
stream: sd.InputStream | None = None


def audio_callback(indata, frames, time, status):
    """Collect audio chunks from the ``InputStream`` callback."""
    if status:
        print(status)
    audio_queue.put(indata.copy())


def toggle_recording():
    """Start or stop audio recording depending on the current state."""
    global recording, stream

    if not recording:
        audio_queue.queue.clear()
        stream = sd.InputStream(samplerate=44100, channels=1, callback=audio_callback)
        stream.start()
        start_button.configure(text="Stop Recording")
        recording = True
    else:
        start_button.configure(text="Processing Transcript", state="disabled")
        start_button.update_idletasks()
        if stream is not None:
            stream.stop()
            stream.close()
        frames = []
        while not audio_queue.empty():
            frames.append(audio_queue.get())

        if frames:
            start_button.configure(text="Processing Transcript", state="disabled")
            audio = np.concatenate(frames, axis=0)
            audio = np.int16(audio * 32767)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(RECORDING_DIR, f"recording_{timestamp}.wav")
            with wave.open(file_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(audio.tobytes())

            app.after(100, lambda: process_transcription(file_path))


def process_transcription(file_path: str) -> None:
    """Run the transcription model and update the UI."""
    global recording
    transcription = run_model(file_path)
    text_box.configure(state="normal")
    text_box.delete("1.0", "end")
    text_box.insert("end", transcription)
    text_box.configure(state="disabled")

    # Save the transcript so it can be viewed later
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"transcript_{timestamp}.txt")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcription)

    start_button.configure(text="Start Recording", state="normal")
    recording = False


def copy_to_clipboard() -> None:
    """Copy the current transcript to the system clipboard."""
    text = text_box.get("1.0", "end").strip()
    if text:
        app.clipboard_clear()
        app.clipboard_append(text)


def view_transcripts() -> None:
    """Display a list of saved transcripts for viewing and copying."""
    files = [f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".txt")]
    if not files:
        return

    window = ctk.CTkToplevel(app)
    window.title("Transcripts")
    window.geometry("400x300")

    selected = ctk.StringVar(value=files[0])

    def load_file(name: str) -> None:
        path = os.path.join(TRANSCRIPT_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            content = ""
        transcript_box.configure(state="normal")
        transcript_box.delete("1.0", "end")
        transcript_box.insert("end", content)
        transcript_box.configure(state="disabled")

    option_menu = ctk.CTkOptionMenu(
        window, values=files, variable=selected, command=load_file, takefocus=True
    )
    option_menu.pack(pady=5)

    transcript_box = ctk.CTkTextbox(window, width=350, height=150, state="disabled", takefocus=True)
    transcript_box.pack(pady=10)

    copy_btn = ctk.CTkButton(
        window, text="Copy", command=lambda: app.clipboard_append(transcript_box.get("1.0", "end").strip()), takefocus=True
    )
    copy_btn.pack(pady=5)

    window.after(100, lambda: load_file(files[0]))
    option_menu.focus_set()


# Create main application window
app = ctk.CTk()
app.title("ClearSay")
app.geometry("400x300")

# Transcribed text display
text_box = ctk.CTkTextbox(app, width=350, height=150, state="disabled", takefocus=True)
text_box.pack(pady=20)

# Recording control button
start_button = ctk.CTkButton(app, text="Start Recording", command=toggle_recording, takefocus=True)
start_button.pack(pady=10)
# Set initial focus so keyboard navigation begins on the first button
start_button.focus_set()

# Copy to clipboard button
copy_button = ctk.CTkButton(app, text="Copy Transcript", command=copy_to_clipboard, takefocus=True)
copy_button.pack(pady=5)

# View transcripts button
view_button = ctk.CTkButton(app, text="View Transcripts", command=view_transcripts, takefocus=True)
view_button.pack(pady=5)

if __name__ == "__main__":
    app.mainloop()
