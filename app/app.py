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

# Directorys for recorded audio and saved transcripts
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

    # Save transcript alongside the recorded audio
    timestamp = os.path.splitext(os.path.basename(file_path))[0].replace(
        "recording_", ""
    )
    transcript_path = os.path.join(
        TRANSCRIPT_DIR, f"transcript_{timestamp}.txt"
    )
    try:
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcription.strip() + "\n")
        status_label.configure(text=f"Saved {os.path.basename(transcript_path)}")
    except OSError:
        status_label.configure(text="Failed to save transcript")

    start_button.configure(text="Start Recording", state="normal")
    recording = False


def copy_to_clipboard() -> None:
    """Copy the current transcript to the system clipboard."""
    text = text_box.get("1.0", "end").strip()
    if text:
        app.clipboard_clear()
        app.clipboard_append(text)


def clear_transcript() -> None:
    """Remove all text from the transcript display."""
    text_box.configure(state="normal")
    text_box.delete("1.0", "end")
    text_box.configure(state="disabled")


def view_transcripts() -> None:
    """Open a transcript file and display its contents."""
    path = ctk.filedialog.askopenfilename(
        initialdir=TRANSCRIPT_DIR,
        title="Open Transcript",
        filetypes=[("Text files", "*.txt")],
    )
    if path:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        top = ctk.CTkToplevel(app)
        top.title(os.path.basename(path))
        viewer = ctk.CTkTextbox(top, width=350, height=150)
        viewer.insert("1.0", content)
        viewer.configure(state="disabled")
        viewer.pack(padx=20, pady=20)
        ctk.CTkButton(top, text="Close", command=top.destroy).pack(pady=10)


# Create main application window
app = ctk.CTk()
app.title("ClearSay")
app.geometry("400x300")

# Transcribed text display
text_box = ctk.CTkTextbox(app, width=350, height=150, state="disabled")
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
view_button = ctk.CTkButton(app, text="View Transcripts", command=view_transcripts)
view_button.pack(pady=5)

# Status label for simple feedback
status_label = ctk.CTkLabel(app, text="")
status_label.pack(pady=5)

if __name__ == "__main__":
    app.mainloop()
