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

# Directory where recordings are stored
RECORDING_DIR = "recorded_audio"
os.makedirs(RECORDING_DIR, exist_ok=True)

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

            # Transcribe the saved recording and display the result
            transcription = run_model(file_path)
            text_box.configure(state="normal")
            text_box.delete("1.0", "end")
            text_box.insert("end", transcription)
            text_box.configure(state="disabled")

        start_button.configure(text="Start Recording", state="normal")
        recording = False


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

if __name__ == "__main__":
    app.mainloop()
