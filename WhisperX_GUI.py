import os
import shutil
# Suppress HuggingFace symlink warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import whisperx
import logging
from logging.handlers import RotatingFileHandler

import torch
import gc

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Rotating log handler to prevent unlimited log growth
handler = RotatingFileHandler("whisper_gui.log", maxBytes=1_048_576, backupCount=3, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

class WhisperTranscriptionApp:
	"""Main application class for the WhisperX Transcription GUI.
	
	This class handles the UI setup, model loading, audio transcription,
	and user interactions for transcribing audio files using OpenAI's Whisper model.
	"""
	def copy_transcription(self):
		"""Copy the transcription text to the clipboard.
		
		Retrieves the text from the text area and copies it to the system clipboard.
		Provides visual feedback by temporarily changing the button text.
		"""
		text = self.text_area.get("0.0", "end").strip()
		if text:
			self.root.clipboard_clear()
			self.root.clipboard_append(text)
			self.copy_btn.configure(text="Copied!")
			self.root.after(1200, lambda: self.copy_btn.configure(text="Copy"))
	def __init__(self, root):
		"""Initialize the WhisperTranscriptionApp with the main window.
		
		Sets up window properties, initializes variables, builds the UI,
		and starts model loading.
		
		Args:
			root: The root CustomTkinter window.
		"""
		self.root = root
		self.root.title("WhisperX Transcription")
		# Larger default window so UI elements are not clipped on startup
		self.root.geometry("1100x820")
		# Prevent the window from being resized smaller than the original layout
		self.root.minsize(900, 650)
		self.root.configure(bg="#181824")
        
		self.model = None
		self.device = ctk.StringVar(value="auto")
		self.alignment_enabled = ctk.BooleanVar(value=False)
		self.audio_file = None
		self.transcription = ""
        
		self.setup_ui()
		# Reload model if device changes
		self.device.trace_add('write', self.reload_model)
		self.model_loading = False
		self.load_model()
		# Check for HF token after UI setup
		self.root.after(100, self.check_hf_token)
        
	def setup_ui(self):
		"""Set up the user interface components.
		
		Creates and configures all UI elements including labels, buttons,
		progress bar, and text area.
		"""
		# Title
		title = ctk.CTkLabel(
			self.root,
			text="WhisperX Transcription",
			font=("Segoe UI", 28, "bold"),
			text_color="#f8fafc"
		)
		title.pack(pady=(30, 10))

		# Device selection
		device_frame = ctk.CTkFrame(self.root, fg_color="#181824")
		device_frame.pack(pady=(0, 10))
		ctk.CTkLabel(device_frame, text="Device:", font=("Segoe UI", 12), text_color="#f8fafc").pack(side="left", padx=(0, 5))
		available_devices = ["auto", "cpu"]
		if torch.cuda.is_available():
			available_devices.append("cuda")
		self.device_menu = ctk.CTkOptionMenu(device_frame, variable=self.device, values=available_devices, fg_color="#23263a", text_color="#f8fafc")
		self.device_menu.pack(side="left", padx=(0, 20))
		
		# Clear Cache Button
		self.clear_cache_btn = ctk.CTkButton(
			device_frame,
			text="Clear Cache",
			command=self.clear_cache,
			fg_color="#ef4444",
			hover_color="#dc2626",
			text_color="white",
			font=("Segoe UI", 11, "bold"),
			width=100,
			height=24
		)
		self.clear_cache_btn.pack(side="left")
        
		# File selection frame
		file_frame = ctk.CTkFrame(self.root, fg_color="#181824")
		file_frame.pack(pady=10, padx=40, fill="x")

		self.file_label = ctk.CTkLabel(
			file_frame,
			text="No file selected",
			font=("Segoe UI", 12),
			text_color="#f8fafc"
		)
		self.file_label.pack(side="left", padx=10)

		select_btn = ctk.CTkButton(
			file_frame,
			text="Select Audio File",
			command=self.select_file,
			fg_color="#6366f1",
			hover_color="#7c3aed",
			text_color="white",
			font=("Segoe UI", 13, "bold"),
			width=140,
			height=40
		)
		select_btn.pack(side="right")
		
		# Alignment checkbox
		self.align_chk = ctk.CTkCheckBox(
			self.root, 
			text="Enable Word-Level Alignment (slower)", 
			variable=self.alignment_enabled,
			font=("Segoe UI", 12),
			text_color="#f8fafc"
		)
		self.align_chk.pack(pady=(5, 0))
        
		# Transcribe button
		self.transcribe_btn = ctk.CTkButton(
			self.root,
			text="Transcribe",
			command=self.transcribe,
			fg_color="#8b5cf6",
			hover_color="#a78bfa",
			text_color="white",
			font=("Segoe UI", 16, "bold"),
			width=200,
			height=50,
			state="disabled"
		)
		self.transcribe_btn.pack(pady=25)
        
		# Status label
		self.status_label = ctk.CTkLabel(
			self.root,
			text="Loading WhisperX model...",
			font=("Segoe UI", 12, "italic"),
			text_color="#fbbf24"
		)
		self.status_label.pack(pady=(0, 10))

		# Progress bar (use .set() to update progress)
		self.progress_bar = ctk.CTkProgressBar(
			self.root,
			width=520,
			height=18,
			progress_color="#22d3ee",
			fg_color="#23263a"
		)
		self.progress_bar.pack(pady=(0, 18))
        
		# Transcription text area
		text_frame = ctk.CTkFrame(self.root, fg_color="#181824")
		text_frame.pack(pady=10, padx=40, fill="both", expand=True)

		ctk.CTkLabel(
			text_frame,
			text="Transcription:",
			font=("Segoe UI", 15, "bold"),
			text_color="#f8fafc"
		).pack(anchor="w", pady=(0, 5))

		# Transcription text area with lighter background and brighter text
		self.text_area = ctk.CTkTextbox(
			text_frame,
			font=("Segoe UI", 12),
			fg_color="#23263a",
			text_color="#f8fafc",
			width=600,
			height=200
		)
		self.text_area.pack(fill="both", expand=True, pady=5, side="left")

		# Copy button at top-right of transcription area
		self.copy_btn = ctk.CTkButton(
			text_frame,
			text="Copy",
			command=self.copy_transcription,
			fg_color="#06b6d4",
			hover_color="#22d3ee",
			text_color="white",
			font=("Segoe UI", 11, "bold"),
			width=80,
			height=32,
			state="normal"
		)
		self.copy_btn.pack(anchor="ne", padx=0, pady=(0, 5), side="top")
        
		# Export button
		self.export_btn = ctk.CTkButton(
			self.root,
			text="Export Transcription",
			command=self.export_transcription,
			fg_color="#3b82f6",
			hover_color="#38bdf8",
			text_color="white",
			font=("Segoe UI", 13, "bold"),
			width=200,
			height=40,
			state="disabled"
		)
		self.export_btn.pack(pady=12)
        
	def load_model(self):
		"""Load the WhisperX model in a background thread.
		
		Determines the device (CPU/CUDA), loads the model asynchronously,
		and updates the UI with status and errors.
		"""
		def load():
			try:
				device = self.device.get()
				orig_device = device
				if device == "auto":
					device = "cuda" if torch.cuda.is_available() else "cpu"
				elif device == "cuda" and not torch.cuda.is_available():
					device = "cpu"
					self.root.after(0, lambda: messagebox.showinfo("Device fallback", "CUDA is not available. Falling back to CPU."))
				# Determine compute type
				compute_type = "float16" if device == "cuda" else "int8"
				
				self.model = whisperx.load_model("large-v2", device=device, compute_type=compute_type)
				self.root.after(0, lambda: self.status_label.configure(text=f"Ready to transcribe ({device}, {compute_type})", text_color="#10b981"))
				self.root.after(0, lambda: self.transcribe_btn.configure(state="normal"))
				# Stop animated progress bar and set to complete
				self.root.after(0, lambda: self.progress_bar.stop())
				self.root.after(0, lambda: self.progress_bar.configure(mode="determinate"))
				self.root.after(0, lambda: self.progress_bar.set(1.0))
				logging.info("Model loaded on device: %s, compute_type: %s", device, compute_type)
				# If fallback occurred, update dropdown
				if orig_device != device:
					self.root.after(0, lambda: self.device.set(device))
			except Exception as e:
				logging.exception("Failed to load model: %s", e)
				self.root.after(0, lambda err=str(e): self.status_label.configure(text=f"Error loading model: {err}", text_color="#ef4444"))
				self.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Failed to load Whisper model:\n{err}"))
				self.root.after(0, lambda: self.transcribe_btn.configure(state="disabled"))
				# Stop progress bar on error
				self.root.after(0, lambda: self.progress_bar.stop())
				self.root.after(0, lambda: self.progress_bar.configure(mode="determinate"))
				self.root.after(0, lambda: self.progress_bar.set(0.0))
			finally:
				# Ensure flag is cleared even if an unexpected error occurs
				self.model_loading = False

		self.model_loading = True
		self.status_label.configure(text="Loading WhisperX model...", text_color="#f59e0b")
		self.transcribe_btn.configure(state="disabled")
		# Start animated progress bar
		self.progress_bar.configure(mode="indeterminate")
		self.progress_bar.start()
		thread = threading.Thread(target=load, daemon=True)
		thread.start()

	def reload_model(self, *_):
		"""Reload the Whisper model when device selection changes.
		
		Resets the model and triggers a new load with the updated device.
		"""
		self.status_label.configure(text="Reloading model...", text_color="#666666")
		self.model = None
		self.load_model()
		
	def check_hf_token(self):
		"""Check if HF_TOKEN is set when alignment is enabled.
		
		Displays a warning dialog with instructions if the token is missing.
		"""
		if self.alignment_enabled.get() and not os.environ.get("HF_TOKEN"):
			message = (
				"Word-level alignment requires a Hugging Face token to download alignment models.\n\n"
				"To set up your token:\n"
				"1. Create a free account at https://huggingface.co\n"
				"2. Go to Settings → Access Tokens and create a token\n"
				"3. Set the HF_TOKEN environment variable:\n\n"
				"   PowerShell (persistent):\n"
				"   [System.Environment]::SetEnvironmentVariable('HF_TOKEN', 'your_token', 'User')\n\n"
				"   PowerShell (session only):\n"
				"   $env:HF_TOKEN = \"your_token\"\n\n"
				"   CMD (session only):\n"
				"   set HF_TOKEN=your_token\n\n"
				"4. Restart this application\n\n"
				"See the README for more details."
			)
			messagebox.showwarning("Hugging Face Token Required", message)
	
	def format_timestamp(self, seconds):
		"""Format timestamp in seconds to MM:SS.mmm format.
		
		Args:
			seconds: Time in seconds (float)
			
		Returns:
			Formatted string in MM:SS.mmm format
		"""
		minutes = int(seconds // 60)
		secs = seconds % 60
		return f"{minutes:02d}:{secs:06.3f}"
        
	def select_file(self):
		"""Open a file dialog to select an audio file.
		
		Updates the UI with the selected file name and enables transcription.
		"""
		filetypes = (
			("Audio files", "*.mp3 *.wav *.m4a *.ogg *.flac *.webm *.mp4"),
			("All files", "*.*")
		)
        
		filename = filedialog.askopenfilename(
			title="Select an audio file",
			filetypes=filetypes
		)
        
		if filename:
			self.audio_file = filename
			self.file_label.configure(text=os.path.basename(filename))
			self.transcribe_btn.configure(state="normal")
			self.text_area.delete("0.0", "end")
			self.export_btn.configure(state="disabled")
            
	def transcribe(self):
		"""Transcribe the selected audio file.
		
		Transcribes the entire audio file directly using Whisper's internal processing.
		Updates the UI with status and results.
		"""
		if not self.audio_file or self.model_loading:
			return
		if not self.model:
			self.status_label.configure(text="Model not loaded yet. Please wait...")
			return

		self.transcribe_btn.configure(state="disabled")
		self.status_label.configure(text="Transcribing... This may take a while for long files", text_color="#f59e0b")
		self.text_area.delete("0.0", "end")
		self.progress_bar.configure(mode="indeterminate")
		self.progress_bar.start()

		def run_transcription():
			try:
				# Transcribe using WhisperX
				# 1. Load audio
				audio = whisperx.load_audio(self.audio_file)
				
				# 2. Transcribe with batching (try default batch size first)
				try:
					result = self.model.transcribe(audio, batch_size=4)
				except RuntimeError as e:
					if "out of memory" in str(e).lower():
						logging.warning("OOM detected. Retrying with batch_size=1 and gc.collect()")
						self.root.after(0, lambda: self.status_label.configure(text="OOM detected. Retrying with lower settings...", text_color="#f59e0b"))
						
						# Clear memory
						gc.collect()
						torch.cuda.empty_cache()
						
						# Fallback: batch_size=1
						result = self.model.transcribe(audio, batch_size=1)
					else:
						raise e

				# 3. Align (if enabled)
				if self.alignment_enabled.get():
					self.root.after(0, lambda: self.status_label.configure(text="Aligning...", text_color="#f59e0b"))
					
					# Clear memory before loading alignment model
					gc.collect()
					torch.cuda.empty_cache()
					
					device = self.device.get()
					if device == "auto":
						device = "cuda" if torch.cuda.is_available() else "cpu"
					elif device == "cuda" and not torch.cuda.is_available():
						device = "cpu"
						
					try:
						model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
						result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
					except OSError as e:
						error_str = str(e).lower()
						if "not a zip file" in error_str or "corrupted" in error_str:
							raise OSError("Alignment model appears corrupted. Please use the 'Clear Cache' button and try again.") from e
						elif "401" in error_str or "unauthorized" in error_str or "authentication" in error_str or "token" in error_str:
							raise OSError(
								"Authentication failed. Hugging Face token is required for alignment.\n\n"
								"To fix this:\n"
								"1. Get a token from https://huggingface.co/settings/tokens\n"
								"2. Set HF_TOKEN environment variable (see README)\n"
								"3. Restart the application\n\n"
								"PowerShell: [System.Environment]::SetEnvironmentVariable('HF_TOKEN', 'your_token', 'User')"
							) from e
						raise e
					
					# Clear memory after alignment
					del model_a
					gc.collect()
					torch.cuda.empty_cache()

				# 4. Combine segments
				segments = result.get("segments", [])
				
				# Format output with timestamps if alignment was used
				if self.alignment_enabled.get() and segments:
					# Check if segments have start/end times (they should after alignment)
					if "start" in segments[0] and "end" in segments[0]:
						formatted_segments = []
						for seg in segments:
							start_time = self.format_timestamp(seg["start"])
							end_time = self.format_timestamp(seg["end"])
							formatted_segments.append(f"[{start_time} - {end_time}] {seg['text'].strip()}")
						self.transcription = "\n".join(formatted_segments)
					else:
						# Fallback to plain text if no timestamps
						self.transcription = " ".join([seg["text"].strip() for seg in segments])
				else:
					# Plain text output when alignment is disabled
					self.transcription = " ".join([seg["text"].strip() for seg in segments])
				
				self.root.after(0, self.update_transcription_ui)
			except Exception as e:
				logging.exception("Transcription error: %s", e)
				self.root.after(0, lambda err=str(e): self.show_error(err))
			finally:
				# Always clean up after transcription
				gc.collect()
				if torch.cuda.is_available():
					torch.cuda.empty_cache()

		thread = threading.Thread(target=run_transcription, daemon=True)
		thread.start()
        
	def update_transcription_ui(self):
		"""Update the UI after transcription completes.
		
		Inserts the transcription text, updates status, and enables export.
		"""
		self.text_area.insert("0.0", self.transcription)
		self.status_label.configure(text="Transcription complete!", text_color="#10b981")
		self.transcribe_btn.configure(state="normal")
		self.export_btn.configure(state="normal")
		self.progress_bar.stop()
		self.progress_bar.configure(mode="determinate")
		self.progress_bar.set(1.0)
        
	def show_error(self, error_msg):
		"""Display an error message to the user.
		
		Logs the error and shows a dialog with the error details.
		
		Args:
			error_msg: The error message to display.
		"""
		logging.error("Transcription failed: %s", error_msg)
		self.status_label.configure(text="Transcription failed", text_color="#ef4444")
		self.progress_bar.stop()
		self.progress_bar.configure(mode="determinate")
		self.progress_bar.set(0.0)
		self.transcribe_btn.configure(state="normal")
		messagebox.showerror("Error", f"Transcription failed:\n{error_msg}")
        
	def export_transcription(self):
		"""Export the transcription to a text file.
		
		Opens a save dialog and writes the transcription to the selected file.
		"""
		if not self.transcription:
			return
            
		filename = filedialog.asksaveasfilename(
			defaultextension=".txt",
			filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
			initialfile=f"transcription_{os.path.splitext(os.path.basename(self.audio_file))[0]}.txt"
		)
        
		if filename:
			try:
				with open(filename, "w", encoding="utf-8") as f:
					f.write(self.transcription)
				messagebox.showinfo("Success", f"Transcription saved to:\n{filename}")
			except Exception as e:
				logging.exception("Failed to save transcription: %s", e)
				messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

	def clear_cache(self):
		"""Clear the Hugging Face model cache.
		
		Deletes the Hugging Face cache directory to resolve corruption issues.
		"""
		if not messagebox.askyesno("Clear Cache", "This will delete all cached Hugging Face models (including WhisperX models).\nThey will be re-downloaded next time you run a transcription.\n\nAre you sure?"):
			return
			
		try:
			# Default HF cache path on Windows
			cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
			if os.path.exists(cache_dir):
				shutil.rmtree(cache_dir)
				messagebox.showinfo("Success", "Cache cleared successfully.\nPlease restart the application.")
			else:
				messagebox.showinfo("Info", "Cache directory not found or already empty.")
		except Exception as e:
			logging.exception("Failed to clear cache: %s", e)
			messagebox.showerror("Error", f"Failed to clear cache:\n{e}")

def main():
	root = ctk.CTk()
	app = WhisperTranscriptionApp(root)
	root.mainloop()

if __name__ == "__main__":
	main()
