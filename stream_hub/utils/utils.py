import yaml
from pathlib import Path

def load_yaml(path=None):
    if path is None:
        return {}

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)