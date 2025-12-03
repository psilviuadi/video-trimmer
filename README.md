# Python Video Trimmer

Select a video you want to trim. View the video to select start and end trims. Select an output name and start trimming.

## Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Python Environment Setup

1. Install Python from [python.org](https://python.org)

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:

Windows:
```bash
.venv\Scripts\Activate.ps1
```

If you get an execution policy error, run this once
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Linux/Mac:
```bash
source .venv/bin/activate
```

4. Install requirements:
```bash
pip install -r requirements.txt
```

## Daily Usage

1. Activate the virtual environment (if not already activated):

Windows:
```bash
.venv\Scripts\Activate.ps1
```

If you get an execution policy error, run this once
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Linux/Mac:
```bash
source .venv/bin/activate
```

2. Start the script with:

```
python run.py
```
