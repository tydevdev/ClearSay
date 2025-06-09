import customtkinter as ctk

# Configure appearance for dark mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

from model import run_model


def start_transcription():
    """Call the speech-to-text model and display its result."""
    result = run_model()
    text_box.configure(state="normal")
    text_box.delete("1.0", ctk.END)
    text_box.insert(ctk.END, result)
    text_box.configure(state="disabled")


# Create main application window
app = ctk.CTk()
app.title("ClearSay")
app.geometry("400x300")

# Transcribed text display
text_box = ctk.CTkTextbox(app, width=350, height=150, state="disabled")
text_box.pack(pady=20)

# Start Transcription button
start_button = ctk.CTkButton(app, text="Start Transcription", command=start_transcription)
start_button.pack(pady=10)

if __name__ == "__main__":
    app.mainloop()
