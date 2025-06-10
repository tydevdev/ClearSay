import customtkinter as ctk
import os
import queue
from datetime import datetime
import wave

from model import run_model
import numpy as np
import sounddevice as sd

# Use a light theme by default with blue accents
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Global UI colors
TEXT_COLOR = "#000000"
BUTTON_FG = "#d0e7ff"
BUTTON_HOVER = "#b0d4ff"

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
        start_button.configure(
            text="Stop Recording",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        recording = True
    else:
        start_button.configure(text="Processing...", state="disabled")
        start_button.update_idletasks()
        if stream is not None:
            stream.stop()
            stream.close()
        frames = []
        while not audio_queue.empty():
            frames.append(audio_queue.get())

        if frames:
            start_button.configure(text="Processing...", state="disabled")
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

    start_button.configure(
        text="Start Recording",
        state="normal",
        font=ctk.CTkFont(size=16, weight="bold"),
    )
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
    refresh_transcripts_list(search_var.get())


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

# search variable for transcripts filtering
search_var = ctk.StringVar()


def apply_theme_colors() -> None:
    """Set background colors for the light theme."""
    gradient = ("#FFFFFF", "#EAF6FF")
    app.configure(fg_color=gradient)
    main_frame.configure(fg_color=gradient)
    transcripts_sidebar.configure(fg_color=gradient)
    transcripts_list.configure(fg_color=gradient)


def toggle_transcripts_sidebar() -> None:
    """Show or hide the transcript sidebar."""
    global sidebar_visible
    if sidebar_visible:
        transcripts_sidebar.grid_remove()
        view_button.configure(text="View Transcripts")
        sidebar_visible = False
    else:
        refresh_transcripts_list(search_var.get())
        transcripts_sidebar.grid(row=1, column=0, sticky="ns", padx=5, pady=5)
        view_button.configure(text="Hide Transcripts")
        sidebar_visible = True




def refresh_transcripts_list(filter_text: str = "") -> None:
    """Populate the sidebar with saved transcripts."""
    for widget in transcripts_list.winfo_children():
        widget.destroy()
    files = sorted(
        [f for f in os.listdir(TRANSCRIPT_DIR) if f.endswith(".txt")]
    )
    if filter_text:
        files = [f for f in files if filter_text.lower() in f.lower()]
    if files:
        for name in files:
            ctk.CTkButton(
                transcripts_list,
                text=name,
                width=230,
                anchor="w",
                fg_color="transparent",
                text_color=TEXT_COLOR,
                command=lambda n=name: display_transcript(n),
            ).pack(fill="x", padx=5, pady=2)
    else:
        ctk.CTkLabel(
            transcripts_list,
            text="No transcripts",
            text_color=TEXT_COLOR,
        ).pack(pady=5)


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
app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(1, weight=1)

# App name header
header_label = ctk.CTkLabel(
    app,
    text="ClearSay",
    font=ctk.CTkFont(size=24, weight="bold"),
    text_color=TEXT_COLOR,
    fg_color=("#b0d4ff", "#d0e7ff"),
    corner_radius=8,
)
header_label.grid(row=0, column=0, columnspan=2, pady=(10, 5))

# Sidebar for transcript list
transcripts_sidebar = ctk.CTkScrollableFrame(app, width=250)
ctk.CTkLabel(
    transcripts_sidebar,
    text="Saved Transcripts",
    text_color=TEXT_COLOR,
).pack(pady=(10, 0))
search_entry = ctk.CTkEntry(
    transcripts_sidebar,
    width=210,
    textvariable=search_var,
    placeholder_text="Search...",
)
search_entry.pack(pady=(0, 5))
search_entry.bind(
    "<KeyRelease>", lambda e: refresh_transcripts_list(search_var.get())
)
transcripts_list = ctk.CTkFrame(transcripts_sidebar)
transcripts_list.pack(fill="both", expand=True, padx=5, pady=5)
transcripts_sidebar.grid(row=1, column=0, sticky="ns", padx=5, pady=5)
transcripts_sidebar.grid_remove()

# Main content frame
main_frame = ctk.CTkFrame(app)
main_frame.grid(row=1, column=1, sticky="nsew")
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_rowconfigure(4, weight=1)

# Instructions for first-time users
instruction_label = ctk.CTkLabel(
    main_frame,
    text="Press 'Start Recording', speak, then wait for the transcription.",
    text_color=TEXT_COLOR,
)
instruction_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

# Start/stop recording section
recording_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
recording_frame.grid(row=2, column=0, pady=(10, 0))
start_button = ctk.CTkButton(
    recording_frame,
    text="Start Recording",
    command=toggle_recording,
    font=ctk.CTkFont(size=16, weight="bold"),
    width=180,
    fg_color=BUTTON_FG,
    hover_color=BUTTON_HOVER,
    text_color=TEXT_COLOR,
)
start_button.pack()

try:
    ctk.CTkToolTip(start_button, message="Start or stop recording (Space)")
except Exception:
    pass

# Transcribed text display
text_box = ctk.CTkTextbox(
    main_frame,
    width=550,
    height=400,
    state="disabled",
    border_width=1,
    corner_radius=8,
)
text_box.grid(row=4, column=0, padx=20, pady=20, sticky="nsew")

# Buttons for other actions
button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
button_frame.grid(row=5, column=0, pady=10)

copy_button = ctk.CTkButton(
    button_frame,
    text="Copy Transcript",
    command=copy_to_clipboard,
    fg_color=BUTTON_FG,
    hover_color=BUTTON_HOVER,
    text_color=TEXT_COLOR,
)
copy_button.grid(row=0, column=0, padx=5)
try:
    ctk.CTkToolTip(copy_button, message="Copy transcript to clipboard (Ctrl+C)")
except Exception:
    pass

view_button = ctk.CTkButton(
    button_frame,
    text="View Transcripts",
    command=toggle_transcripts_sidebar,
    fg_color=BUTTON_FG,
    hover_color=BUTTON_HOVER,
    text_color=TEXT_COLOR,
)
view_button.grid(row=0, column=1, padx=5)
try:
    ctk.CTkToolTip(view_button, message="Toggle transcript list (Ctrl+V)")
except Exception:
    pass

new_button = ctk.CTkButton(
    button_frame,
    text="New Transcription",
    command=new_transcription,
    fg_color=BUTTON_FG,
    hover_color=BUTTON_HOVER,
    text_color=TEXT_COLOR,
)
new_button.grid(row=0, column=2, padx=5)
try:
    ctk.CTkToolTip(new_button, message="New transcription (Ctrl+N)")
except Exception:
    pass

# Status label for simple feedback
status_label = ctk.CTkLabel(main_frame, text="", text_color=TEXT_COLOR)
status_label.grid(row=6, column=0, pady=(0, 10))

# Scaling controls
scaling_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
scaling_frame.grid(row=7, column=0, pady=(0, 10))
ctk.CTkLabel(scaling_frame, text="Scale:", text_color=TEXT_COLOR).pack(
    side="left", padx=(0, 5)
)
scale_slider = ctk.CTkSlider(
    scaling_frame,
    from_=80,
    to=140,
    number_of_steps=6,
    command=lambda v: ctk.set_widget_scaling(float(v) / 100),
)
scale_slider.set(100)
scale_slider.pack(side="left")

# Apply custom background colors once widgets are created
apply_theme_colors()

# Keyboard shortcuts for accessibility
app.bind("<space>", lambda _: toggle_recording())
app.bind("<Control-c>", lambda _: copy_to_clipboard())
app.bind("<Control-n>", lambda _: new_transcription())
app.bind("<Control-v>", lambda _: toggle_transcripts_sidebar())

if __name__ == "__main__":
    app.mainloop()
