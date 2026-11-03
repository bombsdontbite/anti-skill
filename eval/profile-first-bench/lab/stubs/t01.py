from stubkit import Replay

STUBS = {
    # spelling.py is never imported: correct() replays the recorded corrections.
    "spelling_import": Replay("spelling.correct", fake_module="spelling"),
    "confusion_cube": Replay("confusion_cube"),
    "correct_queries": Replay("correct_queries"),
}
