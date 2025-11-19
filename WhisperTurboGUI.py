import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import whisper
import os
import logging
from logging.handlers import RotatingFileHandler

# Rotating log handler to prevent unlimited log growth
handler = RotatingFileHandler("whisper_gui.log", maxBytes=1_048_576, backupCount=3, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

class WhisperTranscriptionApp:
	def copy_transcription(self):
		text = self.text_area.get("1.0", "end").strip()
		if text:
			self.root.clipboard_clear()
			self.root.clipboard_append(text)
			self.copy_btn.configure(text="Copied!")
			self.root.after(1200, lambda: self.copy_btn.configure(text="Copy"))
	def __init__(self, root):
		self.root = root
		self.root.title("Whisper Turbo Transcription")
		# Larger default window so UI elements are not clipped on startup
		self.root.geometry("1100x820")
		# Prevent the window from being resized smaller than the original layout
		self.root.minsize(900, 650)
		self.root.configure(bg="#181824")
        
		self.model = None
		self.device = ctk.StringVar(value="auto")
		self.audio_file = None
		self.transcription = ""
        
		self.setup_ui()
		# Reload model if device changes
		self.device.trace_add('write', self.reload_model)
		self.model_loading = False
		self.load_model()
        
	def setup_ui(self):
		# Title
		title = ctk.CTkLabel(
			self.root,
			text="Whisper Turbo Transcription",
			font=("Segoe UI", 28, "bold"),
			text_color="#f8fafc"
		)
		title.pack(pady=(30, 10))

		# Device selection
		import torch
		device_frame = ctk.CTkFrame(self.root, fg_color="#181824")
		device_frame.pack(pady=(0, 10))
		ctk.CTkLabel(device_frame, text="Device:", font=("Segoe UI", 12), text_color="#f8fafc").pack(side="left", padx=(0, 5))
		available_devices = ["auto", "cpu"]
		if torch.cuda.is_available():
			available_devices.append("cuda")
		self.device_menu = ctk.CTkOptionMenu(device_frame, variable=self.device, values=available_devices, fg_color="#23263a", text_color="#f8fafc")
		self.device_menu.pack(side="left")
        
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

		def on_enter(e):
			pass
		def on_leave(e):
			pass

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
        
		# Transcribe button
		def on_transcribe_enter(e):
			pass
		def on_transcribe_leave(e):
			pass
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
			text="Loading Whisper Turbo model...",
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
		def on_copy_enter(e):
			pass
		def on_copy_leave(e):
			pass
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
		def on_export_enter(e):
			pass
		def on_export_leave(e):
			pass
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
		"""Load Whisper Turbo model in background, show loading indicator"""
		def load():
			try:
				import torch
				device = self.device.get()
				orig_device = device
				if device == "auto":
					device = "cuda" if torch.cuda.is_available() else "cpu"
				elif device == "cuda" and not torch.cuda.is_available():
					device = "cpu"
					self.root.after(0, lambda: messagebox.showinfo("Device fallback", "CUDA is not available. Falling back to CPU."))
				self.model = whisper.load_model("turbo", device=device)
				self.root.after(0, lambda: self.status_label.configure(text=f"Ready to transcribe ({device})", text_color="#10b981"))
				self.root.after(0, lambda: self.transcribe_btn.configure(state="normal"))
				logging.info("Model loaded on device: %s", device)
				# If fallback occurred, update dropdown
				if orig_device != device:
					self.root.after(0, lambda: self.device.set(device))
			except Exception as e:
				logging.exception("Failed to load model: %s", e)
				self.root.after(0, lambda err=str(e): self.status_label.configure(text=f"Error loading model: {err}", text_color="#ef4444"))
				self.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Failed to load Whisper model:\n{err}"))
				self.root.after(0, lambda: self.transcribe_btn.configure(state="disabled"))
			finally:
				# Ensure flag is cleared even if an unexpected error occurs
				self.model_loading = False

		self.model_loading = True
		self.status_label.configure(text="Loading Whisper Turbo model...", text_color="#666666")
		self.transcribe_btn.configure(state="disabled")
		thread = threading.Thread(target=load, daemon=True)
		thread.start()

	def reload_model(self, *_):
		self.status_label.configure(text="Reloading model...", text_color="#666666")
		self.model = None
		self.load_model()
        
	def select_file(self):
		"""Open file dialog to select audio file"""
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
			self.text_area.delete("1.0", "end")
			self.export_btn.configure(state="disabled")
            
	def transcribe(self):
		"""Transcribe the selected audio file with progress"""
		if not self.audio_file or self.model_loading:
			return
		if not self.model:
			self.status_label.configure(text="Model not loaded yet. Please wait...")
			return

		self.transcribe_btn.configure(state="disabled")
		self.status_label.configure(text="Transcribing... This may take a moment", text_color="#f59e0b")
		self.text_area.delete("1.0", "end")
		self.progress_bar.set(0.0)

		def run_transcription():
			try:
				import numpy as np
				import math
				import whisper.audio

				# Load audio using whisper's loader (ffmpeg backend)
				audio = whisper.audio.load_audio(self.audio_file)
				sr = whisper.audio.SAMPLE_RATE
				total_samples = len(audio)
				chunk_duration = 30  # seconds
				samples_per_chunk = int(sr * chunk_duration)
				num_chunks = math.ceil(total_samples / samples_per_chunk)
				segments = []

				import tempfile
				import soundfile as sf
				for i in range(num_chunks):
					start = i * samples_per_chunk
					end = min((i + 1) * samples_per_chunk, total_samples)
					chunk_audio = audio[start:end]
					# Save chunk to temp file (as wav). Ensure removal in finally.
					temp_path = None
					try:
						with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
							sf.write(tmp.name, chunk_audio, sr)
							temp_path = tmp.name
							result = self.model.transcribe(temp_path)
							segments.append(result.get("text", ""))
					finally:
						if temp_path:
							try:
								os.remove(temp_path)
							except Exception:
								logging.exception("Failed to remove temp file: %s", temp_path)
					percent = ((i + 1) / num_chunks) * 100
					self.root.after(0, lambda p=percent: self.progress_bar.set(p/100.0))
					self.root.after(0, lambda p=percent: self.status_label.configure(text=f"Transcribing... {p:.0f}%", text_color="#f59e0b"))
				self.transcription = " ".join(segments)
				self.root.after(0, self.update_transcription_ui)
			except Exception as e:
				logging.exception("Transcription error: %s", e)
				self.root.after(0, lambda err=str(e): self.show_error(err))

		thread = threading.Thread(target=run_transcription, daemon=True)
		thread.start()
        
	def update_transcription_ui(self):
		"""Update UI after transcription completes"""
		self.text_area.insert("1.0", self.transcription)
		self.status_label.configure(text="Transcription complete!", text_color="#10b981")
		self.transcribe_btn.configure(state="normal")
		self.export_btn.configure(state="normal")
		self.progress_bar.set(1.0)
        
	def show_error(self, error_msg):
		"""Show error message"""
		logging.error("Transcription failed: %s", error_msg)
		self.status_label.configure(text="Transcription failed", text_color="#ef4444")
		self.transcribe_btn.configure(state="normal")
		messagebox.showerror("Error", f"Transcription failed:\n{error_msg}")
        
	def export_transcription(self):
		"""Export transcription to a text file"""
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

def main():
	ctk.set_appearance_mode("dark")
	ctk.set_default_color_theme("blue")
	root = ctk.CTk()
	app = WhisperTranscriptionApp(root)
	root.mainloop()

if __name__ == "__main__":
	main()
