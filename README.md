# Whisper Turbo Transcription GUI

A modern desktop app for fast audio transcription using Whisper Turbo with a dark-themed GUI built on CustomTkinter.

## Features
- Transcribe audio files (mp3, wav, m4a, ogg, flac, webm, mp4, etc.)
- Modern, dark-themed GUI with a progress bar and status colors
- GPU/CPU device selection (auto-detects CUDA)
- Copy and export transcription
- Chunked processing for large files to reduce memory usage
- Error handling and user feedback

## Requirements
- Python 3.8+ (3.10/3.11 recommended)
- System `ffmpeg` (must be installed and available in PATH) — required by the audio loader
- Python packages (see `requirements.txt`)

The included `requirements.txt` lists the typical Python packages used by this app.

## Installation
1. Clone the repository:
   ```powershell
   git clone https://github.com/MeneerJanssens/WhisperTurboGUI.git
   cd WhisperTurboGUI
   ```
2. Create and activate a virtual environment (recommended):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # PowerShell
   # or use `.venv\Scripts\activate.bat` for cmd
   ```
3. Install Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Ensure `ffmpeg` is installed and available in your PATH. On Windows you can install a build from https://ffmpeg.org/ or via package managers like `choco`/`scoop`.

## Usage
Run the app:
```powershell
python WhisperTurboGUI.py
```

Basic workflow:
- Select the device (`auto`, `cpu`, or `cuda`) from the dropdown.
- Click `Select Audio File` and choose an audio file.
- Click `Transcribe` when the model has loaded.
- Use `Copy` to copy the transcription to clipboard or `Export Transcription` to save to a `.txt` file.

## Notes & Troubleshooting
- If the model fails to load, check that `torch` is installed and (optionally) that CUDA drivers are available for GPU usage.
- If you see audio loading errors, confirm `ffmpeg` is correctly installed and accessible from a terminal.
- The GUI uses `customtkinter` for theming — adjust the colors in `WhisperTurboGUI.py` if you prefer a different palette.

## FAQ

- **Q: Which `torch` wheel should I install for CPU vs GPU?**
  - **GPU (CUDA)**: The pinned `requirements.txt` currently references `torch==2.7.1+cu118`. This requires an NVIDIA GPU and matching CUDA 11.8 drivers/toolkit on the target machine. Install the corresponding CUDA drivers from NVIDIA and ensure the runtime is present.
  - **CPU-only**: If you don't have a compatible GPU or want a simpler install, install a CPU-only wheel. Example (Windows):
    ```powershell
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    ```
  - If `pip` fails to find a suitable wheel for your Python version, visit https://pytorch.org/get-started/locally/ and follow the recommended install command for your platform.

- **Q: How do I install `ffmpeg` on Windows?**
  - Option 1 (scoop):
    ```powershell
    scoop install ffmpeg
    ```
  - Option 2 (chocolatey):
    ```powershell
    choco install ffmpeg
    ```
  - Option 3: Download a static build from https://ffmpeg.org/download.html, extract, and add the `bin` folder to your `PATH`.

- **Q: My `pip install -r requirements.txt` fails on `torch` due to CUDA tags. What should I do?**
  - Use the CPU-only wheel (see above), or choose the correct CUDA-enabled wheel matching your GPU/driver. Alternatively, create a clean venv and install packages one at a time to diagnose the failing package.

## Creating a Windows executable (optional)
1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
2. Build the executable:
   ```powershell
   pyinstaller --onefile --noconsole WhisperTurboGUI.py
   ```
3. The `.exe` will be in the `dist` folder. Be careful not to commit large binaries to GitHub (GitHub limits files >100MB).

## License
MIT

## Credits
- Whisper Turbo / OpenAI Whisper
- PyTorch
- CustomTkinter