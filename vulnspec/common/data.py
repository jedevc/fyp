from pathlib import Path

DATA_DIRECTORY = Path(__file__).parent.parent / "data"


def data_path(*parts: str) -> Path:
    current = DATA_DIRECTORY
    for part in parts:
        current /= part
    return current
