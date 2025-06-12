from recorder import Recorder
from storage import TranscriptStorage
from ui import ClearSayUI


def main() -> None:
    recorder = Recorder()
    transcripts = TranscriptStorage()
    ui = ClearSayUI(recorder, transcripts)
    ui.run()


if __name__ == "__main__":
    main()
