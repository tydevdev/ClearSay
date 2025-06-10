import customtkinter as ctk
import os
import queue
from datetime import datetime
import wave

from model import run_model
import numpy as np
import sounddevice as sd

# Configure appearance for dark mode

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Directories for recorded audio and saved transcripts
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
    text_box.insert("end", "\n" + transcription)
    text_box.configure(state="disabled")
    status_label.configure(text="")

    start_button.configure(text="Start Recording", state="normal")
    recording = False


def copy_to_clipboard() -> None:
    """Copy the current transcript to the system clipboard."""
    text = text_box.get("1.0", "end").strip()
    if text:
        app.clipboard_clear()
        app.clipboard_append(text)


def clear_transcript() -> None:
    """Save current text and clear the transcript display."""
    text = text_box.get("1.0", "end").strip()
    if text:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        transcript_path = os.path.join(
            TRANSCRIPT_DIR, f"transcript_{timestamp}.txt"
        )
        try:
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            status_label.configure(text=f"Saved {os.path.basename(transcript_path)}")
        except OSError:
            status_label.configure(text="Failed to save transcript")
    text_box.configure(state="normal")
    text_box.delete("1.0", "end")
    text_box.configure(state="disabled")
    refresh_transcripts_list()


def view_transcripts() -> None:
    """Display the transcript viewer inside the app window."""
    refresh_transcripts_list()
    transcripts_frame.pack(fill="both", expand=True, pady=10)


def refresh_transcripts_list() -> None:
    """Refresh the dropdown with saved transcripts."""
    files = sorted(
        [f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".txt")]
    )
    if files:
        transcript_menu.configure(values=files)
        transcript_menu.set(files[0])
        display_transcript(files[0])
    else:
        transcript_menu.configure(values=["No transcripts"])
        transcript_menu.set("No transcripts")
        transcript_viewer.configure(state="normal")
        transcript_viewer.delete("1.0", "end")
        transcript_viewer.insert("1.0", "")
        transcript_viewer.configure(state="disabled")


def display_transcript(name: str) -> None:
    """Show the contents of ``name`` in the transcript viewer."""
    path = os.path.join(TRANSCRIPT_DIR, name)
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    transcript_viewer.configure(state="normal")
    transcript_viewer.delete("1.0", "end")
    transcript_viewer.insert("1.0", content)
    transcript_viewer.configure(state="disabled")


# Create main application window
app = ctk.CTk()
app.title("ClearSay")
app.geometry("600x800")
app.minsize(600, 800)

# Transcribed text display
text_box = ctk.CTkTextbox(app, width=550, height=400, state="disabled")
text_box.pack(pady=20)

# Recording control button
start_button = ctk.CTkButton(app, text="Start Recording", command=toggle_recording)
start_button.pack(pady=10)

# Copy to clipboard button
copy_button = ctk.CTkButton(app, text="Copy Transcript", command=copy_to_clipboard)
copy_button.pack(pady=5)

# Clear transcript button
clear_button = ctk.CTkButton(app, text="Clear Transcript", command=clear_transcript)
clear_button.pack(pady=5)

# View saved transcripts button
view_button = ctk.CTkButton(
    app, text="View Transcripts", command=view_transcripts
)
view_button.pack(pady=5)

# Frame for in-app transcript viewer
transcripts_frame = ctk.CTkFrame(app)
transcripts_frame.pack_forget()

ctk.CTkLabel(transcripts_frame, text="Saved Transcripts").pack(pady=5)
transcript_menu = ctk.CTkOptionMenu(
    transcripts_frame, values=[], command=display_transcript
)
transcript_menu.pack(pady=5)

transcript_viewer = ctk.CTkTextbox(transcripts_frame, width=550, height=200)
transcript_viewer.configure(state="disabled")
transcript_viewer.pack(padx=20, pady=5, fill="both", expand=True)

ctk.CTkButton(
    transcripts_frame, text="Hide", command=lambda: transcripts_frame.pack_forget()
).pack(pady=5)

# Status label for simple feedback
status_label = ctk.CTkLabel(app, text="")
status_label.pack(pady=5)

if __name__ == "__main__":
    app.mainloop()
