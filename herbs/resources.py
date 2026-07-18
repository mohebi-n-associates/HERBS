from pathlib import Path


PACKAGE_DIRECTORY = Path(__file__).resolve().parent


def resource_path(relative_path):
    """Return an absolute path to a resource shipped inside the HERBS package."""
    path = Path(relative_path)
    if path.is_absolute():
        return str(path)
    return str(PACKAGE_DIRECTORY / path)
