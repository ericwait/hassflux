import json
import os
from pathlib import Path
from typing import Dict

def load_friendly_names(file_path: Path) -> Dict[str, str]:
    """Loads friendly names from a JSON file."""
    if file_path.exists():
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def get_start_id(progress_file: Path) -> int:
    """Reads the last processed state_id from the progress file."""
    if progress_file.exists():
        with open(progress_file, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                pass
    return 0

def save_progress(progress_file: Path, state_id: int) -> None:
    """Saves the current state_id to the progress file."""
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_file, "w") as f:
        f.write(str(state_id))
