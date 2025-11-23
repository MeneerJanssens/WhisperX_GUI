# WhisperX Transcription GUI

A modern desktop app for fast audio transcription using WhisperX with a dark-themed GUI built on CustomTkinter.

## Features
- Transcribe audio files (mp3, wav, m4a, ogg, flac, webm, mp4, etc.)
- Modern, dark-themed GUI with **animated progress bar** and status colors
- **Segment Timestamps:** Displays `[MM:SS.mmm - MM:SS.mmm]` timestamps when alignment is enabled
- GPU/CPU device selection (auto-detects CUDA)
- Copy and export transcription
- Batched processing for fast transcription
- Word-level alignment for accurate timestamps
- Error handling and user feedback (including NLTK data auto-download)

## Requirements
- Python 3.8+ (3.10/3.11 recommended)
- System `ffmpeg` (must be installed and available in PATH) — required by the audio loader
- NVIDIA GPU with CUDA drivers (recommended for speed)
- Python packages (see `requirements.txt`)

**Note on PyTorch:**
The project is configured for **PyTorch 2.8.0** with **CUDA 12.9** support. Ensure your NVIDIA drivers are up to date (version 525+ recommended).

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
python WhisperX_GUI.py
```

Basic workflow:
- Select the device (`auto`, `cpu`, or `cuda`) from the dropdown.
- Click `Select Audio File` and choose an audio file.
- (Optional) Check "Enable Word-Level Alignment" for precise timestamps.
- Click `Transcribe`. The **orange** status text and **animated progress bar** will indicate activity.
- Once complete, view the transcription (with timestamps if aligned) in the text area.
- Use `Copy` to copy the transcription to clipboard or `Export Transcription` to save to a `.txt` file.

## Pre-downloading Models (Optional)

You can optionally pre-download the required models before using the GUI:

```powershell
python download_models.py
```

This interactive script will:
- Check if you have an HF_TOKEN set and guide you through setting it up if needed
- Download the Whisper model (large-v2)
- Download alignment models for your chosen languages (default: English and Dutch)
- Download NLTK tokenizer data automatically
- Set the HF_TOKEN persistently in your Windows environment

The script provides an interactive setup experience and is especially useful for:
- First-time setup
- Configuring your HF token without manual environment variable editing
- Pre-downloading models on a fast connection before working offline

## Hugging Face Token for Alignment

If you enable **word-level alignment**, WhisperX needs to download alignment models from Hugging Face, which requires authentication. You can either use the `download_models.py` script (recommended) or follow these manual steps:

### 1. Get a Hugging Face Token
- Create a free account at [https://huggingface.co](https://huggingface.co)
- Go to **Settings → Access Tokens** ([direct link](https://huggingface.co/settings/tokens))
- Click **New token** and create a token with **read** permissions
- Copy the token value

### 2. Set the HF_TOKEN Environment Variable

Choose one of the following methods based on your preference:

**PowerShell (Persistent - Recommended)**
```powershell
[System.Environment]::SetEnvironmentVariable('HF_TOKEN', 'your_token_here', 'User')
```
This sets the token permanently for your user account. You'll need to restart the application after setting it.

**PowerShell (Current Session Only)**
```powershell
$env:HF_TOKEN = "your_token_here"
```
This only works for the current PowerShell session. You'll need to set it again if you close the terminal.

**Command Prompt (Current Session Only)**
```cmd
set HF_TOKEN=your_token_here
```
This only works for the current CMD session.

### 3. Restart the Application
After setting the environment variable (especially for persistent methods), restart the WhisperX GUI application.

## Notes & Troubleshooting
- **Alignment errors**: If you encounter authentication errors when using alignment, ensure your `HF_TOKEN` is set correctly (see the section above). You can also try clearing the cache using the "Clear Cache" button and restarting the application.
- **Corrupted model cache**: If you see "not a zip file" or corruption errors, click the **Clear Cache** button in the app and try again. This will delete cached models and re-download them.
- **NLTK errors**: The `download_models.py` script automatically downloads required NLTK data. If you encounter NLTK-related errors, run the script or manually download with: `python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"`
- If the model fails to load, check that `torch` is installed and (optionally) that CUDA drivers are available for GPU usage.
- If you see audio loading errors, confirm `ffmpeg` is correctly installed and accessible from a terminal.
- The GUI uses `customtkinter` for theming — adjust the colors in `WhisperX_GUI.py` if you prefer a different palette.

## FAQ

- **Q: Which `torch` wheel should I install for CPU vs GPU?**
  - **GPU (CUDA)**: The pinned `requirements.txt` currently references `torch==2.8.0+cu129`. This requires an NVIDIA GPU and matching CUDA 12.9 drivers/toolkit on the target machine. Install the corresponding CUDA drivers from NVIDIA and ensure the runtime is present.
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

- **Q: What does the timestamp output look like?**
  - When alignment is enabled, each segment displays with timestamps: `[00:05.500 - 00:08.300] Your transcribed text here`
  - Without alignment, you get plain text output without timestamps.

## Creating a Windows executable (optional)
1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
2. Build the executable:
   ```powershell
   pyinstaller --onefile --noconsole WhisperX_GUI.py
   ```
3. The `.exe` will be in the `dist` folder. Be careful not to commit large binaries to GitHub (GitHub limits files >100MB).

## License
MIT

## Credits
- WhisperX
- PyTorch
- CustomTkinter