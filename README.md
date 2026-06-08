# Python Video Trimmer

A simple desktop app for trimming a single video clip and combining numbered MP4 clips in a folder.

## What this project contains

- `run.py` — application entrypoint and logging setup
- `src/app_ui.py` — main tkinter UI controller
- `src/video_trim_service.py` — parameterized trim logic
- `src/video_combine_service.py` — parameterized combine logic
- `src/env_utils.py` — environment loader used by `run.py`

## Features

- Browse and preview video files
- Set exact trim start/end times
- Save trimmed output with custom filename
- Combine `1.mp4`, `2.mp4`, ... into a single MP4 file

## Requirements

- Python 3.8 or higher
- `pip`

Dependencies are listed in `requirements.txt`.

## Setup

1. Install Python from [python.org](https://python.org).

2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate the virtual environment:

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If you get an execution policy error, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

macOS / Linux:

```bash
source .venv/bin/activate
```

4. Create an environment file.

```bash
copy .env.example .env
```

Open `.env` and customize any configuration values if needed.

5. Install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Run the app

Start the app from the repository root:

```bash
python run.py
```

## Project structure

```text
src/
  app_ui.py
  env_utils.py
  video_trim_service.py
  video_combine_service.py
requirements.txt
run.py
README.md
```

## Troubleshooting

- If `moviepy` imports fail, confirm the virtual environment is activated and `requirements.txt` is installed.
- On Windows, if PowerShell policies block activation, use the `Set-ExecutionPolicy` command above.
- If the app cannot read a video file, verify the file format is supported and the path is correct.
