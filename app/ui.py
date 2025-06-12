import os
import threading
import customtkinter as ctk

from constants import BUTTON_FG, BUTTON_HOVER, TEXT_COLOR, TRANSCRIPT_DIR
from model import run_model
from recorder import Recorder
from transcripts import TranscriptManager


class ClearSayUI:
    def __init__(self, recorder: Recorder, transcripts: TranscriptManager) -> None:
        """Initialize the UI with the recorder and transcript manager."""

        self.recorder = recorder
        self.transcripts = transcripts
        self.sidebar_visible = False
        self.current_timestamp: str | None = None

        # App root must exist before any Tk variables are created
        self.app: ctk.CTk | None = None
        self.search_var: ctk.StringVar | None = None
        self._build()

    def _build(self) -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.app = ctk.CTk()
        self.search_var = ctk.StringVar()
        self.app.title("ClearSay")
        self.app.geometry("1000x600")
        self.app.minsize(800, 600)
        self.app.protocol("WM_DELETE_WINDOW", self.on_close)
        self.app.grid_columnconfigure(1, weight=1)
        self.app.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_sidebar()
        self._build_main()
        self.apply_theme_colors()
        self._bind_shortcuts()

    def _build_header(self) -> None:
        self.header_label = ctk.CTkLabel(
            self.app,
            text="ClearSay",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=TEXT_COLOR,
            fg_color=("#b0d4ff", "#d0e7ff"),
            corner_radius=8,
        )
        self.header_label.grid(row=0, column=0, columnspan=2, pady=(10, 5))

    def _build_sidebar(self) -> None:
        self.transcripts_sidebar = ctk.CTkScrollableFrame(self.app, width=250)
        ctk.CTkLabel(
            self.transcripts_sidebar,
            text="Saved Transcripts",
            text_color=TEXT_COLOR,
        ).pack(pady=(10, 0))
        self.search_entry = ctk.CTkEntry(
            self.transcripts_sidebar,
            width=210,
            textvariable=self.search_var,
            placeholder_text="Search...",
        )
        self.search_entry.pack(pady=(0, 5))
        self.search_entry.bind(
            "<KeyRelease>", lambda _: self.refresh_transcripts_list(self.search_var.get())
        )
        self.transcripts_list = ctk.CTkFrame(self.transcripts_sidebar)
        self.transcripts_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.transcripts_sidebar.grid(row=1, column=0, sticky="ns", padx=5, pady=5)
        self.transcripts_sidebar.grid_remove()

    def _build_main(self) -> None:
        self.main_frame = ctk.CTkFrame(self.app)
        self.main_frame.grid(row=1, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            self.main_frame,
            text="Press 'Start Recording', speak, then wait for the transcription.",
            text_color=TEXT_COLOR,
        ).grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        recording_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        recording_frame.grid(row=2, column=0, pady=(10, 0))
        self.start_button = ctk.CTkButton(
            recording_frame,
            text="Start Recording",
            command=self.toggle_recording,
            font=ctk.CTkFont(size=16, weight="bold"),
            width=180,
            fg_color=BUTTON_FG,
            hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
        )
        self.start_button.pack()
        try:
            ctk.CTkToolTip(self.start_button, message="Start or stop recording (Space)")
        except Exception:
            pass

        self.text_box = ctk.CTkTextbox(
            self.main_frame,
            width=550,
            height=400,
            state="disabled",
            border_width=1,
            corner_radius=8,
        )
        self.text_box.grid(row=4, column=0, padx=20, pady=20, sticky="nsew")

        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.grid(row=5, column=0, pady=10)

        copy_button = ctk.CTkButton(
            button_frame,
            text="Copy Transcript",
            command=self.copy_to_clipboard,
            fg_color=BUTTON_FG,
            hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
        )
        copy_button.grid(row=0, column=0, padx=5)
        try:
            ctk.CTkToolTip(copy_button, message="Copy transcript to clipboard (Ctrl+C)")
        except Exception:
            pass

        self.view_button = ctk.CTkButton(
            button_frame,
            text="View Transcripts",
            command=self.toggle_transcripts_sidebar,
            fg_color=BUTTON_FG,
            hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
        )
        self.view_button.grid(row=0, column=1, padx=5)
        try:
            ctk.CTkToolTip(self.view_button, message="Toggle transcript list (Ctrl+V)")
        except Exception:
            pass

        new_button = ctk.CTkButton(
            button_frame,
            text="New Transcription",
            command=self.new_transcription,
            fg_color=BUTTON_FG,
            hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
        )
        new_button.grid(row=0, column=2, padx=5)
        try:
            ctk.CTkToolTip(new_button, message="New transcription (Ctrl+N)")
        except Exception:
            pass

        self.status_label = ctk.CTkLabel(self.main_frame, text="", text_color=TEXT_COLOR)
        self.status_label.grid(row=6, column=0, pady=(0, 10))

        scaling_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
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

    def _bind_shortcuts(self) -> None:
        self.app.bind("<space>", lambda _: self.toggle_recording())
        self.app.bind("<Control-c>", lambda _: self.copy_to_clipboard())
        self.app.bind("<Control-n>", lambda _: self.new_transcription())
        self.app.bind("<Control-v>", lambda _: self.toggle_transcripts_sidebar())

    # Public API
    def run(self) -> None:
        self.app.mainloop()

    # Methods mapped from original functions
    def toggle_recording(self) -> None:
        if not self.recorder.recording:
            try:
                self.recorder.start()
            except Exception as exc:  # Recording can fail if no mic is present
                self.status_label.configure(text=f"Recording error: {exc}")
                return
            self.start_button.configure(
                text="Stop Recording",
                font=ctk.CTkFont(size=16, weight="bold"),
            )
        else:
            self.start_button.configure(text="Processing...", state="disabled")
            self.status_label.configure(text="Transcribing...")
            self.start_button.update_idletasks()
            file_path = self.recorder.stop()
            if file_path:
                self.current_timestamp = self.recorder.last_timestamp
                threading.Thread(
                    target=self.process_transcription,
                    args=(file_path,),
                    daemon=True,
                ).start()
            else:
                self.start_button.configure(
                    text="Start Recording",
                    state="normal",
                    font=ctk.CTkFont(size=16, weight="bold"),
                )

    def process_transcription(self, file_path: str) -> None:
        """Run the model and update the UI when finished."""

        transcription = run_model(file_path)
        self.app.after(0, lambda: self._update_transcription_ui(transcription))

    def _update_transcription_ui(self, transcription: str) -> None:
        self.text_box.configure(state="normal")
        if self.text_box.get("1.0", "end").strip():
            self.text_box.insert("end", "\n\n" + transcription)
        else:
            self.text_box.insert("end", transcription)
        self.text_box.configure(state="disabled")
        self.status_label.configure(text="")
        self.save_current_transcript()
        self.refresh_transcripts_list(self.search_var.get())
        self.start_button.configure(
            text="Start Recording",
            state="normal",
            font=ctk.CTkFont(size=16, weight="bold"),
        )

    def copy_to_clipboard(self) -> None:
        text = self.text_box.get("1.0", "end").strip()
        if text:
            self.app.clipboard_clear()
            self.app.clipboard_append(text)

    def save_current_transcript(self) -> None:
        text = self.text_box.get("1.0", "end").strip()
        path = self.transcripts.save(text, self.current_timestamp)
        if path is None:
            self.status_label.configure(text="Failed to save transcript")
            return
        self.status_label.configure(text=f"Saved {os.path.basename(path)}")
        self.refresh_transcripts_list(self.search_var.get())

    def clear_transcript(self) -> None:
        self.save_current_transcript()
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.configure(state="disabled")
        self.transcripts.new()
        self.current_timestamp = None

    def new_transcription(self) -> None:
        self.clear_transcript()
        self.status_label.configure(text="")

    def on_close(self) -> None:
        self.save_current_transcript()
        self.app.destroy()

    def apply_theme_colors(self) -> None:
        gradient = ("#FFFFFF", "#EAF6FF")
        self.app.configure(fg_color=gradient)
        self.main_frame.configure(fg_color=gradient)
        self.transcripts_sidebar.configure(fg_color=gradient)
        self.transcripts_list.configure(fg_color=gradient)

    def toggle_transcripts_sidebar(self) -> None:
        if self.sidebar_visible:
            self.transcripts_sidebar.grid_remove()
            self.view_button.configure(text="View Transcripts")
            self.sidebar_visible = False
        else:
            self.refresh_transcripts_list(self.search_var.get())
            self.transcripts_sidebar.grid(row=1, column=0, sticky="ns", padx=5, pady=5)
            self.view_button.configure(text="Hide Transcripts")
            self.sidebar_visible = True

    def refresh_transcripts_list(self, filter_text: str = "") -> None:
        for widget in self.transcripts_list.winfo_children():
            widget.destroy()
        files = self.transcripts.list(filter_text)
        if files:
            for name in files:
                ctk.CTkButton(
                    self.transcripts_list,
                    text=name,
                    width=230,
                    anchor="w",
                    fg_color="transparent",
                    text_color=TEXT_COLOR,
                    command=lambda n=name: self.display_transcript(n),
                ).pack(fill="x", padx=5, pady=2)
        else:
            ctk.CTkLabel(
                self.transcripts_list,
                text="No transcripts",
                text_color=TEXT_COLOR,
            ).pack(pady=5)

    def display_transcript(self, name: str) -> None:
        content = self.transcripts.load(name)
        if content is None:
            return
        # allow subsequent saves to overwrite the opened transcript
        self.transcripts.current_path = os.path.join(TRANSCRIPT_DIR, name)
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", content)
        self.text_box.configure(state="disabled")
