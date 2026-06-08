import os
from pathlib import Path


def _parse_env_line(line: str):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    return key, value


def _load_env_file(path: Path):
    try:
        with path.open("r", encoding="utf-8") as fp:
            for raw_line in fp:
                parsed = _parse_env_line(raw_line)
                if not parsed:
                    continue
                key, value = parsed
                if key not in os.environ:
                    os.environ[key] = value
    except FileNotFoundError:
        pass


def load_env(dotenv_path: Path | str | None = None, example_path: Path | str | None = None):
    root = Path(__file__).resolve().parents[1]
    dotenv_file = Path(dotenv_path) if dotenv_path else root / ".env"
    example_file = Path(example_path) if example_path else root / ".env.example"

    if dotenv_file.exists():
        _load_env_file(dotenv_file)
    elif example_file.exists():
        _load_env_file(example_file)
