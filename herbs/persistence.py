"""Persistence helpers shared by projects, layers, and exported objects."""

import pickle


def load_legacy_pickle(file_path):
    """Load a legacy HERBS pickle with a consistent ``(data, error)`` result."""
    try:
        with open(file_path, "rb") as infile:
            return pickle.load(infile), None
    except OSError as exc:
        return None, "Unable to read file: {}".format(exc)
    except Exception as exc:
        return None, "Invalid or incomplete HERBS file: {}".format(exc)
