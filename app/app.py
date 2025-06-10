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
current_transcript_path: str | None = None


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
    if text_box.get("1.0", "end").strip():
        text_box.insert("end", "\n" + transcription)
    else:
        text_box.insert("end", transcription)
    text_box.configure(state="disabled")
    status_label.configure(text="")
    save_current_transcript()

    start_button.configure(text="Start Recording", state="normal")
    recording = False


def copy_to_clipboard() -> None:
    """Copy the current transcript to the system clipboard."""
    text = text_box.get("1.0", "end").strip()
    if text:
        app.clipboard_clear()
        app.clipboard_append(text)


def save_current_transcript() -> None:
    """Write current transcript text to a file."""
    global current_transcript_path
    text = text_box.get("1.0", "end").strip()
    if not text:
        return
    if current_transcript_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_transcript_path = os.path.join(
            TRANSCRIPT_DIR, f"transcript_{timestamp}.txt"
        )
    try:
        with open(current_transcript_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    except OSError:
        status_label.configure(text="Failed to save transcript")
        return
    status_label.configure(text=f"Saved {os.path.basename(current_transcript_path)}")
    refresh_transcripts_list()


def clear_transcript() -> None:
    """Save current text and clear the transcript display."""
    save_current_transcript()
    text_box.configure(state="normal")
    text_box.delete("1.0", "end")
    text_box.configure(state="disabled")
    global current_transcript_path
    current_transcript_path = None


def new_transcription() -> None:
    """Save current transcript and start a new one."""
    clear_transcript()
    status_label.configure(text="")


def on_close() -> None:
    """Handle window close by saving current transcript."""
    save_current_transcript()
    app.destroy()


sidebar_visible = False


def toggle_transcripts_sidebar() -> None:
    """Show or hide the transcript sidebar."""
    global sidebar_visible
    if sidebar_visible:
        transcripts_sidebar.pack_forget()
        sidebar_visible = False
    else:
        refresh_transcripts_list()
        transcripts_sidebar.pack(side="left", fill="y", padx=5, pady=5)
        sidebar_visible = True


def refresh_transcripts_list() -> None:
    """Populate the sidebar with saved transcripts."""
    for widget in transcripts_list.winfo_children():
        widget.destroy()
    files = sorted(
        [f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".txt")]
    )
    if files:
        for name in files:
            ctk.CTkButton(
                transcripts_list,
                text=name,
                width=190,
                anchor="e",
                fg_color="transparent",
                command=lambda n=name: display_transcript(n),
            ).pack(fill="x", padx=5, pady=2)
    else:
        ctk.CTkLabel(transcripts_list, text="No transcripts").pack(pady=5)


def display_transcript(name: str) -> None:
    """Load ``name`` into the main transcript box."""
    path = os.path.join(TRANSCRIPT_DIR, name)
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    text_box.configure(state="normal")
    text_box.delete("1.0", "end")
    text_box.insert("1.0", content)
    text_box.configure(state="disabled")


# Create main application window
app = ctk.CTk()
app.title("ClearSay")
app.geometry("1000x600")
app.minsize(800, 600)
app.protocol("WM_DELETE_WINDOW", on_close)

# Sidebar for transcript list
transcripts_sidebar = ctk.CTkScrollableFrame(app, width=220)
ctk.CTkLabel(transcripts_sidebar, text="Saved Transcripts").pack(pady=(10, 0))
transcripts_list = ctk.CTkFrame(transcripts_sidebar)
transcripts_list.pack(fill="both", expand=True, padx=5, pady=5)
transcripts_sidebar.pack_forget()

# Main content frame
main_frame = ctk.CTkFrame(app)
main_frame.pack(side="right", fill="both", expand=True)

# Top controls
top_frame = ctk.CTkFrame(main_frame)
top_frame.pack(fill="x", pady=(10, 0))
new_button = ctk.CTkButton(top_frame, text="New Transcription", command=new_transcription)
new_button.pack(side="right", padx=5)

# Transcribed text display
text_box = ctk.CTkTextbox(main_frame, width=550, height=400, state="disabled")
text_box.pack(pady=20, padx=20)

# Buttons in a single row
button_frame = ctk.CTkFrame(main_frame)
button_frame.pack(pady=10)

start_button = ctk.CTkButton(button_frame, text="Start Recording", command=toggle_recording)
start_button.pack(side="left", padx=5)

copy_button = ctk.CTkButton(button_frame, text="Copy Transcript", command=copy_to_clipboard)
copy_button.pack(side="left", padx=5)

view_button = ctk.CTkButton(button_frame, text="View Transcripts", command=toggle_transcripts_sidebar)
view_button.pack(side="left", padx=5)

# Status label for simple feedback
status_label = ctk.CTkLabel(main_frame, text="")
status_label.pack(pady=5)

if __name__ == "__main__":
    app.mainloop()
