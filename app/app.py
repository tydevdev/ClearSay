from recorder import Recorder
from transcripts import TranscriptManager
from ui import ClearSayUI


def main() -> None:
    recorder = Recorder()
    transcripts = TranscriptManager()
    ui = ClearSayUI(recorder, transcripts)
    ui.run()


if __name__ == "__main__":
    main()
