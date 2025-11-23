import os
# Suppress HuggingFace symlink warning
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# Enable faster downloads with hf_transfer
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

import whisperx
import torch
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def check_and_setup_hf_token():
    """
    Check if HF_TOKEN is set, and if not, guide the user through setting it up.
    Returns True if token is set (or user chooses to skip), False if user wants to exit.
    """
    print("=" * 60)
    print("Hugging Face Token Setup")
    print("=" * 60)
    
    # Check if token is already set
    current_token = os.environ.get("HF_TOKEN")
    if current_token:
        print("✅ HF_TOKEN is already set in your environment.")
        print(f"   Token preview: {current_token[:10]}...{current_token[-4:] if len(current_token) > 14 else ''}")
        print()
        return True
    
    print("⚠️  HF_TOKEN is not set.")
    print()
    print("The Hugging Face token is required to download alignment models.")
    print("Without it, you can still download the Whisper model, but word-level")
    print("alignment will not be available.")
    print()
    print("To get a token:")
    print("  1. Go to https://huggingface.co/settings/tokens")
    print("  2. Create a new token with 'read' permissions")
    print("  3. Copy the token value")
    print()
    print("-" * 60)
    print("What would you like to do?")
    print("  [1] Set HF_TOKEN now (recommended - persistent)")
    print("  [2] Skip token setup (download Whisper model only)")
    print("  [3] Exit and set token manually")
    print("-" * 60)
    
    while True:
        choice = input("Enter your choice (1/2/3): ").strip()
        
        if choice == "1":
            # Set token
            print()
            token = input("Paste your Hugging Face token here: ").strip()
            
            if not token:
                print("❌ No token provided. Please try again.")
                continue
            
            # Basic validation
            if len(token) < 20:
                print("⚠️  Warning: Token seems too short. Are you sure it's correct?")
                confirm = input("Continue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            
            # Set the token persistently for the user
            try:
                # Set for current session
                os.environ["HF_TOKEN"] = token
                
                # Set persistently using Windows environment variable API
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, 'HF_TOKEN', 0, winreg.REG_SZ, token)
                winreg.CloseKey(key)
                
                print()
                print("✅ HF_TOKEN has been set successfully!")
                print("   The token is now set persistently for your user account.")
                print("   Note: You may need to restart applications to use the token.")
                print()
                return True
            except Exception as e:
                print(f"❌ Failed to set environment variable: {e}")
                print("   The token is set for this session only.")
                print()
                return True
        
        elif choice == "2":
            print()
            print("⚠️  Skipping token setup.")
            print("   Only the Whisper model will be downloaded.")
            print("   Alignment models require a valid HF_TOKEN.")
            print()
            return True
        
        elif choice == "3":
            print()
            print("Exiting. You can set the token manually using:")
            print("  PowerShell: [System.Environment]::SetEnvironmentVariable('HF_TOKEN', 'your_token', 'User')")
            print()
            return False
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

def download_models():
    """
    Downloads the necessary models for WhisperX to the Hugging Face cache.
    """
    print("=" * 60)
    print("WhisperX Model Downloader")
    print("=" * 60)
    print("This script will download the models required for WhisperX.")
    print("Models will be stored in your Hugging Face cache directory.")
    print("Default location: C:\\Users\\<YourUser>\\.cache\\huggingface\\hub")
    print()
    
    # Check and setup HF token
    if not check_and_setup_hf_token():
        input("Press Enter to exit...")
        return
    
    print("-" * 60)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    
    print(f"Using device: {device}")
    print(f"Compute type: {compute_type}")
    print("-" * 60)

    # 1. Download Whisper Model
    print("\n[1/2] Downloading Whisper Model (large-v2)...")
    print("This may take several minutes depending on your connection...")
    try:
        # This triggers the download
        model = whisperx.load_model("large-v2", device=device, compute_type=compute_type)
        print("✅ Whisper model downloaded successfully.")
        del model  # Free memory
    except Exception as e:
        print(f"❌ Failed to download Whisper model: {e}")
        print("\n" + "=" * 60)
        print("Download process failed.")
        print("=" * 60)
        input("Press Enter to exit...")
        return

    # 2. Download Alignment Models (only if HF_TOKEN is set)
    has_token = bool(os.environ.get("HF_TOKEN"))
    
    if has_token:
        # Ask which languages to download
        print("\n[2/2] Downloading Alignment Models...")
        print("Which languages would you like to download alignment models for?")
        print("  Common options: en (English), nl (Dutch), fr (French), de (German), es (Spanish)")
        print("  Enter language codes separated by spaces (e.g., 'en nl fr')")
        print("  Or press Enter for default: en nl")
        
        lang_input = input("\nLanguage codes: ").strip()
        languages = lang_input.split() if lang_input else ["en", "nl"]
        
        print(f"\nDownloading alignment models for: {', '.join(languages)}...")
        
        for lang in languages:
            print(f"  - Downloading alignment model for '{lang}'...")
            try:
                model_a, metadata = whisperx.load_align_model(language_code=lang, device=device)
                print(f"    ✅ '{lang}' alignment model downloaded.")
                del model_a, metadata  # Free memory
            except Exception as e:
                error_msg = str(e).lower()
                if "401" in error_msg or "unauthorized" in error_msg or "authentication" in error_msg:
                    print(f"    ❌ Authentication failed for '{lang}'.")
                    print(f"       Your HF_TOKEN may be invalid or expired.")
                    print(f"       Please check your token at https://huggingface.co/settings/tokens")
                else:
                    print(f"    ❌ Failed to download alignment model for '{lang}': {e}")
    else:
        print("\n[2/2] Skipping Alignment Models (no HF_TOKEN set)")
        print("To download alignment models later, set HF_TOKEN and run this script again.")

    # 3. Download NLTK Data (required for alignment)
    print("\n[3/3] Downloading NLTK Data (required for word-level alignment)...")
    try:
        import nltk
        print("  - Downloading punkt tokenizer...")
        nltk.download('punkt', quiet=True)
        print("    ✅ punkt tokenizer downloaded.")
        
        print("  - Downloading punkt_tab tokenizer...")
        nltk.download('punkt_tab', quiet=True)
        print("    ✅ punkt_tab tokenizer downloaded.")
    except Exception as e:
        print(f"    ⚠️  Failed to download NLTK data: {e}")
        print("    You may need to download it manually later with:")
        print("    python -c \"import nltk; nltk.download('punkt'); nltk.download('punkt_tab')\"")

    print("\n" + "=" * 60)
    print("Download process completed!")
    print("You can now run the WhisperX GUI.")
    print("=" * 60)
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        download_models()
    except KeyboardInterrupt:
        print("\n\n⚠️  Download cancelled by user.")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        logging.exception("Unexpected error during download")
        input("Press Enter to exit...")
