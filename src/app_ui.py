import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
import threading
from PIL import Image, ImageTk
import cv2
import tempfile
import pygame
from proglog import ProgressBarLogger

from .video_trim_service import trim_video, _safe_close_clip
from .video_combine_service import combine_numbered_clips
from moviepy.video.io.VideoFileClip import VideoFileClip


class VideoTrimmer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Trimmer")
        self.root.geometry("1000x800")

        self.video_path = None
        self.video_duration = 0
        self.clip = None
        self.cap = None
        self.current_frame = None
        self.is_playing = False
        self.current_time = 0

        self.temp_audio_path = None
        self.audio_ready = False
        self._progress_state = {}

        self.create_widgets()

    def _make_progress_logger(self, min_time_interval=0.2):
        outer = self

        class UIProgressLogger(ProgressBarLogger):
            def __init__(self):
                super().__init__(min_time_interval=min_time_interval)

            def bars_callback(self, bar, attr, value, old_value=None):
                try:
                    outer.root.after(0, outer._on_progress, bar, attr, value, old_value)
                except Exception:
                    pass

            def log(self, message):
                return

        return UIProgressLogger()

    def _on_progress(self, bar, attr, value, old_value):
        state = self._progress_state.setdefault(bar, {})

        if attr in ("frame_index", "index"):
            state['index'] = value
        if attr in ("total", "frames", "nframes"):
            state['total'] = value

        total = state.get('total')
        index = state.get('index')

        if total and (index is not None):
            try:
                percent = int((index / total) * 100)
            except Exception:
                percent = 0
            try:
                self.trim_progress['value'] = percent
                self.progress_label.config(text=f"Progress: {percent}%")
            except Exception:
                pass
        else:
            if total and (index is None):
                try:
                    self.trim_progress['value'] = 0
                    self.progress_label.config(text=f"Progress: 0%")
                except Exception:
                    pass

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)

        file_frame = ttk.LabelFrame(main_frame, text="Video Selection", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        file_frame.columnconfigure(0, weight=1)

        ttk.Label(file_frame, text="Select Video File:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_label = ttk.Label(file_frame, text="No file selected", foreground="gray")
        self.file_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(file_frame, text="Select Video", command=self.browse_file).grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        self.next_button = ttk.Button(file_frame, text="Next Video", command=self.next_video, state=tk.DISABLED)
        self.next_button.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)

        trim_frame = ttk.LabelFrame(main_frame, text="Video Trimming", padding="10")
        trim_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        trim_frame.columnconfigure(1, weight=1)
        trim_frame.columnconfigure(2, weight=0)

        ttk.Label(trim_frame, text="Start Time:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.start_entry = ttk.Entry(trim_frame, width=20)
        self.start_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        self.start_entry.insert(0, "0.00")
        self.set_start_button = ttk.Button(trim_frame, text="Set to Current", command=self.set_start_to_current, state=tk.DISABLED)
        self.set_start_button.grid(row=0, column=2, padx=10)

        ttk.Label(trim_frame, text="End Time:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.end_entry = ttk.Entry(trim_frame, width=20)
        self.end_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        self.end_entry.insert(0, "0.00")
        self.set_end_button = ttk.Button(trim_frame, text="Set to Current", command=self.set_end_to_current, state=tk.DISABLED)
        self.set_end_button.grid(row=1, column=2, padx=10)

        ttk.Label(trim_frame, text="Output:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.output_entry = ttk.Entry(trim_frame, width=20)
        self.output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        self.end_entry.insert(0, "0.00")
        self.trim_button = ttk.Button(trim_frame, text="Trim Video", command=self.trim_video, state=tk.DISABLED)
        self.trim_button.grid(row=2, column=2, padx=10)

        status_frame = ttk.LabelFrame(main_frame, text="Status / Combine", padding="10")
        status_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_frame.columnconfigure(0, weight=1)

        self.combine_button = ttk.Button(status_frame, text="Combine Videos", command=self.combine_videos, state=tk.DISABLED)
        self.combine_button.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))

        self.trim_progress = ttk.Progressbar(status_frame, length=220, mode='determinate')
        self.trim_progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        self.trim_progress['value'] = 0

        self.progress_label = ttk.Label(status_frame, text="", foreground="green")
        self.progress_label.grid(row=2, column=0, sticky=tk.W)

        self.video_frame = ttk.LabelFrame(main_frame, text="Video Preview", padding="10")
        self.video_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        self.video_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.video_frame, width=800, height=450, bg="black")
        self.canvas.grid(row=0, column=0, pady=5)

        controls_frame = ttk.Frame(self.video_frame)
        controls_frame.grid(row=1, column=0, pady=5)
        self.play_button = ttk.Button(controls_frame, text="▶ Play", command=self.toggle_play, state=tk.DISABLED)
        self.play_button.grid(row=0, column=2, padx=5)
        self.jump_back_button = ttk.Button(controls_frame, text="<< 5s", command=lambda: self.jump(-5), state=tk.DISABLED)
        self.jump_back_button.grid(row=0, column=1, padx=5)
        self.jump_forward_button = ttk.Button(controls_frame, text="5s >>", command=lambda: self.jump(5), state=tk.DISABLED)
        self.jump_forward_button.grid(row=0, column=3, padx=5)
        self.jump_to_start_button = ttk.Button(controls_frame, text="Start of Cut", command=self.jump_to_start_cut, state=tk.DISABLED)
        self.jump_to_start_button.grid(row=0, column=0, padx=5)
        self.jump_to_end_button = ttk.Button(controls_frame, text="End of Cut", command=self.jump_to_end_cut, state=tk.DISABLED)
        self.jump_to_end_button.grid(row=0, column=4, padx=5)
        self.time_label = ttk.Label(controls_frame, text="00:00.00 / 00:00.00")
        self.time_label.grid(row=0, column=5, padx=10)

        self.timeline = ttk.Scale(self.video_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_timeline_change)
        self.timeline.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        self.timeline.state(['disabled'])

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
                ("All Files", "*.*")
            ]
        )

        if file_path:
            self.load_video(file_path)

    def find_next_video_path(self, current_path):
        if not current_path:
            return None

        directory = os.path.dirname(current_path)
        supported_extensions = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}

        try:
            files = [
                name for name in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, name))
                and os.path.splitext(name)[1].lower() in supported_extensions
            ]
        except Exception:
            return None

        files = sorted(files, key=lambda name: name.lower())
        current_name = os.path.basename(current_path)

        for index, name in enumerate(files):
            if name.lower() == current_name.lower():
                if index + 1 < len(files):
                    return os.path.join(directory, files[index + 1])
                break

        return None

    def update_next_button_state(self):
        if self.video_path and self.find_next_video_path(self.video_path):
            self.next_button.config(state=tk.NORMAL)
        else:
            self.next_button.config(state=tk.DISABLED)

    def next_video(self):
        if not self.video_path:
            return

        next_path = self.find_next_video_path(self.video_path)
        if next_path:
            self.load_video(next_path)

    def find_next_numeric_output_name(self, directory, extension):
        for index in range(1, 51):
            candidate = f"{index}{extension}"
            if not os.path.exists(os.path.join(directory, candidate)):
                return candidate
        return f"output{extension}"

    def load_video(self, file_path):
        try:
            self.progress_label.config(text="Loading video...")
            self.root.update()

            if self.cap:
                self.cap.release()
                self.cap = None
            if self.clip:
                try:
                    _safe_close_clip(self.clip)
                finally:
                    self.clip = None
            try:
                pygame.mixer.stop()
            except Exception:
                pass
            try:
                pygame.mixer.quit()
            except Exception:
                pass
            if self.temp_audio_path:
                try:
                    os.remove(self.temp_audio_path)
                except Exception:
                    pass
                self.temp_audio_path = None
                self.audio_ready = False

            self.cap = cv2.VideoCapture(file_path)
            self.clip = VideoFileClip(file_path)
            self.video_path = file_path
            self.video_duration = self.clip.duration
            self.current_time = 0

            filename = os.path.basename(file_path)
            self.file_label.config(text=filename, foreground="black")
            self.display_frame_at_time(0)
            self.update_time_label()

            self.start_entry.delete(0, tk.END)
            self.start_entry.insert(0, "0.00")
            self.end_entry.delete(0, tk.END)
            self.end_entry.insert(0, f"{self.video_duration:.2f}")

            extension = os.path.splitext(filename)[1]
            suggested_name = self.find_next_numeric_output_name(os.path.dirname(file_path), extension)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, suggested_name)

            self.play_button.config(state=tk.NORMAL)
            self.trim_button.config(state=tk.NORMAL)
            self.combine_button.config(state=tk.NORMAL)
            self.set_start_button.config(state=tk.NORMAL)
            self.set_end_button.config(state=tk.NORMAL)
            self.jump_back_button.config(state=tk.NORMAL)
            self.jump_forward_button.config(state=tk.NORMAL)
            self.jump_to_start_button.config(state=tk.NORMAL)
            self.jump_to_end_button.config(state=tk.NORMAL)
            self.timeline.state(['!disabled'])
            self.timeline.config(to=self.video_duration)
            self.update_next_button_state()

            if self.clip.audio is not None:
                self.progress_label.config(text="Extracting audio (background)...")
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                tmp.close()
                self.temp_audio_path = tmp.name
                threading.Thread(target=self._extract_audio, args=(self.clip, self.temp_audio_path), daemon=True).start()
            else:
                self.audio_ready = False
                self.temp_audio_path = None

            self.progress_label.config(text="Video loaded successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video:\n{str(e)}")
            self.progress_label.config(text="")

    def _extract_audio(self, clip, path):
        try:
            try:
                logger = self._make_progress_logger()
                clip.audio.write_audiofile(path, fps=44100, nbytes=2, write_logfile=False, logger=logger)
            except TypeError:
                clip.audio.write_audiofile(path, fps=44100, nbytes=2, write_logfile=False)
            self.temp_audio_path = path
            try:
                pygame.mixer.init(frequency=44100)
            except Exception:
                pass

            def _load():
                try:
                    pygame.mixer.music.load(self.temp_audio_path)
                    self.audio_ready = True
                    self.progress_label.config(text="Audio ready for preview.")
                except Exception as e:
                    self.audio_ready = False
                    self.progress_label.config(text=f"Audio load failed: {e}")

            self.root.after(0, _load)
        except Exception as e:
            import moviepy.audio.io.ffmpeg_audiowriter as ffaw
            try:
                ffaw.ffmpeg_audiowrite(clip, path, 44100, 2, 2000, codec='pcm_s16le', write_logfile=False, logger=self._make_progress_logger())
                self.temp_audio_path = path
                try:
                    pygame.mixer.init(frequency=44100)
                except Exception:
                    pass

                def _load2():
                    try:
                        pygame.mixer.music.load(self.temp_audio_path)
                        self.audio_ready = True
                        self.progress_label.config(text="Audio ready for preview.")
                    except Exception as e2:
                        self.audio_ready = False
                        self.progress_label.config(text=f"Audio load failed: {e2}")

                self.root.after(0, _load2)
                return
            except Exception as e2:
                self.audio_ready = False
                msg = f"{e} | fallback error: {e2}"
                self.root.after(0, lambda m=msg: self.progress_label.config(text=f"Audio extraction failed: {m}"))

    def display_frame_at_time(self, time_sec):
        try:
            self.cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
            ret, frame = self.cap.read()

            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width = frame.shape[:2]
                canvas_width = 640
                canvas_height = 360
                scale = min(canvas_width / width, canvas_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
                img = Image.fromarray(frame)
                self.current_frame = ImageTk.PhotoImage(image=img)
                self.canvas.delete("all")
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                self.canvas.create_image(x, y, anchor=tk.NW, image=self.current_frame)
        except Exception as e:
            print(f"Error displaying frame: {e}")

    def toggle_play(self):
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="▶ Play")
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        else:
            self.is_playing = True
            self.play_button.config(text="⏸ Pause")
            if self.audio_ready and self.temp_audio_path:
                try:
                    self.play_audio_from(self.current_time)
                except Exception:
                    pass
            self.play_video()

    def play_audio_from(self, start_time):
        if not self.audio_ready or not self.temp_audio_path:
            return
        try:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            try:
                pygame.mixer.music.play(loops=0, start=start_time)
            except TypeError:
                pygame.mixer.music.play(loops=0)
                try:
                    pygame.mixer.music.set_pos(start_time)
                except Exception:
                    pass
        except Exception as e:
            print(f"Audio playback error: {e}")

    def play_video(self):
        if not self.is_playing or not self.cap:
            return

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        try:
            frame_delay = int(1000 / fps) if fps and fps > 0 else 33
        except Exception:
            frame_delay = 33

        ret, frame = self.cap.read()

        if ret:
            self.current_time = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = frame.shape[:2]
            canvas_width = 640
            canvas_height = 360
            scale = min(canvas_width / width, canvas_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
            img = Image.fromarray(frame)
            self.current_frame = ImageTk.PhotoImage(image=img)
            self.canvas.delete("all")
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.current_frame)
            self.timeline.set(self.current_time)
            self.update_time_label()
            self.root.after(frame_delay, self.play_video)
        else:
            self.is_playing = False
            self.play_button.config(text="▶ Play")
            self.current_time = 0
            self.cap.set(cv2.CAP_PROP_POS_MSEC, 0)
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def on_timeline_change(self, value):
        if not self.is_playing:
            time_sec = float(value)
            self.current_time = time_sec
            self.display_frame_at_time(time_sec)
            self.update_time_label()
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def update_time_label(self):
        current_min = int(self.current_time // 60)
        current_sec = self.current_time % 60
        total_min = int(self.video_duration // 60)
        total_sec = self.video_duration % 60
        self.time_label.config(text=f"{current_min:02d}:{current_sec:05.2f} / {total_min:02d}:{total_sec:05.2f}")

    def set_start_to_current(self):
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, f"{self.current_time:.2f}")

    def set_end_to_current(self):
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, f"{self.current_time:.2f}")

    def jump(self, seconds):
        if not self.clip or not self.cap:
            return
        new_time = self.current_time + seconds
        new_time = max(0.0, min(self.video_duration, new_time))
        self.current_time = new_time
        self.cap.set(cv2.CAP_PROP_POS_MSEC, new_time * 1000)
        self.display_frame_at_time(new_time)
        self.timeline.set(new_time)
        self.update_time_label()
        if self.is_playing and self.audio_ready and self.temp_audio_path:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            try:
                self.play_audio_from(new_time)
            except Exception:
                pass

    def jump_to_start_cut(self):
        try:
            start_time = float(self.start_entry.get())
            self.current_time = start_time
            self.cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
            self.display_frame_at_time(start_time)
            self.timeline.set(start_time)
            self.update_time_label()
            if self.is_playing and self.audio_ready and self.temp_audio_path:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                try:
                    self.play_audio_from(start_time)
                except Exception:
                    pass
        except ValueError:
            pass

    def jump_to_end_cut(self):
        try:
            end_time = float(self.end_entry.get())
            self.current_time = end_time
            self.cap.set(cv2.CAP_PROP_POS_MSEC, end_time * 1000)
            self.display_frame_at_time(end_time)
            self.timeline.set(end_time)
            self.update_time_label()
            if self.is_playing and self.audio_ready and self.temp_audio_path:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                try:
                    self.play_audio_from(end_time)
                except Exception:
                    pass
        except ValueError:
            pass

    def trim_video(self):
        if not self.clip:
            messagebox.showwarning("Warning", "Please select a video first!")
            return

        try:
            start_time = float(self.start_entry.get())
            end_time = float(self.end_entry.get())
            output_name = self.output_entry.get()

            if start_time < 0 or end_time > self.video_duration:
                messagebox.showerror("Error", "Trim times are out of video duration range!")
                return
            if start_time >= end_time:
                messagebox.showerror("Error", "Start time must be less than end time!")
                return
            if not output_name:
                messagebox.showerror("Error", "Please enter an output filename!")
                return

            output_dir = os.path.dirname(self.video_path)
            output_path = os.path.join(output_dir, output_name)

            self.trim_button.config(state=tk.DISABLED)
            self.progress_label.config(text="Trimming video... This may take a while.")

            thread = threading.Thread(target=self.process_trim, args=(start_time, end_time, output_path), daemon=True)
            thread.start()

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for start and end times!")
            self.trim_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.trim_button.config(state=tk.NORMAL)

    def process_trim(self, start_time, end_time, output_path):
        try:
            logger = self._make_progress_logger()
            trim_video(self.video_path, start_time, end_time, output_path, logger=logger)
            self.root.after(0, self.trim_complete, output_path)
        except Exception as e:
            self.root.after(0, self.trim_error, str(e))

    def trim_complete(self, output_path):
        self.progress_label.config(text=f"Video trimmed successfully!")
        messagebox.showinfo("Success", f"Video saved to:\n{output_path}")
        self.trim_button.config(state=tk.NORMAL)

    def trim_error(self, error_msg):
        self.progress_label.config(text="Trimming failed!")
        messagebox.showerror("Error", f"Failed to trim video:\n{error_msg}")
        self.trim_button.config(state=tk.NORMAL)
        self.combine_button.config(state=tk.NORMAL)

    def combine_videos(self):
        if not self.video_path:
            messagebox.showwarning("Warning", "Please select a video first!")
            return

        self.combine_button.config(state=tk.DISABLED)
        self.progress_label.config(text="Combining videos in current folder...")
        threading.Thread(target=self.process_combine, daemon=True).start()

    def process_combine(self):
        try:
            directory = os.path.dirname(self.video_path)
            output_path = combine_numbered_clips(directory, fade_duration=1.0, logger=self._make_progress_logger())
            self.root.after(0, self.combine_complete, output_path)
        except Exception as e:
            self.root.after(0, self.combine_error, str(e))

    def combine_complete(self, output_path):
        self.progress_label.config(text="Videos combined successfully!")
        messagebox.showinfo("Success", f"Combined video saved to:\n{output_path}")
        self.combine_button.config(state=tk.NORMAL)

    def combine_error(self, error_msg):
        self.progress_label.config(text="Combine failed!")
        messagebox.showerror("Error", f"Failed to combine videos:\n{error_msg}")
        self.combine_button.config(state=tk.NORMAL)

    def cleanup(self):
        self.is_playing = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.clip:
            try:
                _safe_close_clip(self.clip)
            finally:
                self.clip = None
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
