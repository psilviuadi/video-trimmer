import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
from moviepy.editor import VideoFileClip
import threading
from PIL import Image, ImageTk
import cv2

class VideoTrimmer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Trimmer")
        self.root.geometry("900x700")
        
        # Variables to store video info
        self.video_path = None
        self.video_duration = 0
        self.clip = None
        self.cap = None
        self.current_frame = None
        self.is_playing = False
        self.current_time = 0
        
        # Create UI components
        self.create_widgets()
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # File selection section
        ttk.Label(main_frame, text="Select Video File:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.file_label = ttk.Label(main_frame, text="No file selected", foreground="gray")
        self.file_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Button(main_frame, text="Browse Video", command=self.browse_file).grid(row=2, column=0, sticky=tk.W, pady=10)
        
        # Video player section
        self.video_frame = ttk.LabelFrame(main_frame, text="Video Preview", padding="10")
        self.video_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        self.video_frame.columnconfigure(0, weight=1)
        
        # Canvas for video display
        self.canvas = tk.Canvas(self.video_frame, width=640, height=360, bg="black")
        self.canvas.grid(row=0, column=0, pady=5)
        
        # Video controls
        controls_frame = ttk.Frame(self.video_frame)
        controls_frame.grid(row=1, column=0, pady=5)
        
        self.play_button = ttk.Button(controls_frame, text="▶ Play", command=self.toggle_play, state=tk.DISABLED)
        self.play_button.grid(row=0, column=0, padx=5)
        
        self.time_label = ttk.Label(controls_frame, text="00:00.00 / 00:00.00")
        self.time_label.grid(row=0, column=1, padx=10)
        
        # Timeline slider
        self.timeline = ttk.Scale(self.video_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_timeline_change)
        self.timeline.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        self.timeline.state(['disabled'])
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        
        # Trim controls section
        ttk.Label(main_frame, text="Trim Settings:", font=("Arial", 12, "bold")).grid(row=5, column=0, sticky=tk.W, pady=5)
        
        trim_frame = ttk.Frame(main_frame)
        trim_frame.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Start time
        ttk.Label(trim_frame, text="Start Time (seconds):").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.start_entry = ttk.Entry(trim_frame, width=15)
        self.start_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.start_entry.insert(0, "0.00")
        
        self.set_start_button = ttk.Button(trim_frame, text="Set to Current", command=self.set_start_to_current, state=tk.DISABLED)
        self.set_start_button.grid(row=0, column=2, padx=10)
        
        # End time
        ttk.Label(trim_frame, text="End Time (seconds):").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.end_entry = ttk.Entry(trim_frame, width=15)
        self.end_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.end_entry.insert(0, "0.00")
        
        self.set_end_button = ttk.Button(trim_frame, text="Set to Current", command=self.set_end_to_current, state=tk.DISABLED)
        self.set_end_button.grid(row=1, column=2, padx=10)
        
        # Output filename
        ttk.Label(trim_frame, text="Output Filename:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.output_entry = ttk.Entry(trim_frame, width=30)
        self.output_entry.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Trim button
        self.trim_button = ttk.Button(main_frame, text="Trim Video", command=self.trim_video, state=tk.DISABLED)
        self.trim_button.grid(row=7, column=0, pady=20)
        
        # Progress label
        self.progress_label = ttk.Label(main_frame, text="", foreground="green")
        self.progress_label.grid(row=8, column=0, columnspan=2, pady=5)
    
    def browse_file(self):
        """Open file dialog to select a video file"""
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self.load_video(file_path)
    
    def load_video(self, file_path):
        """Load the selected video and update UI"""
        try:
            self.progress_label.config(text="Loading video...")
            self.root.update()
            
            # Clean up previous video
            if self.cap:
                self.cap.release()
            if self.clip:
                self.clip.close()
            
            # Load video with OpenCV for playback
            self.cap = cv2.VideoCapture(file_path)
            
            # Load video clip for trimming
            self.clip = VideoFileClip(file_path)
            self.video_path = file_path
            self.video_duration = self.clip.duration
            self.current_time = 0
            
            # Get video properties
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Update UI
            filename = os.path.basename(file_path)
            self.file_label.config(text=filename, foreground="black")
            
            # Display first frame
            self.display_frame_at_time(0)
            
            # Update time label
            self.update_time_label()
            
            # Set default trim values
            self.start_entry.delete(0, tk.END)
            self.start_entry.insert(0, "0.00")
            
            self.end_entry.delete(0, tk.END)
            self.end_entry.insert(0, f"{self.video_duration:.2f}")
            
            # Suggest output filename
            name_without_ext = os.path.splitext(filename)[0]
            extension = os.path.splitext(filename)[1]
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, f"{name_without_ext}_trimmed{extension}")
            
            # Enable controls
            self.play_button.config(state=tk.NORMAL)
            self.trim_button.config(state=tk.NORMAL)
            self.set_start_button.config(state=tk.NORMAL)
            self.set_end_button.config(state=tk.NORMAL)
            self.timeline.state(['!disabled'])
            self.timeline.config(to=self.video_duration)
            
            self.progress_label.config(text="Video loaded successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video:\n{str(e)}")
            self.progress_label.config(text="")
    
    def display_frame_at_time(self, time_sec):
        """Display a specific frame from the video"""
        try:
            # Set video to specific time
            self.cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
            ret, frame = self.cap.read()
            
            if ret:
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize frame to fit canvas
                height, width = frame.shape[:2]
                canvas_width = 640
                canvas_height = 360
                
                # Calculate scaling
                scale = min(canvas_width / width, canvas_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                frame = cv2.resize(frame, (new_width, new_height))
                
                # Convert to PhotoImage
                img = Image.fromarray(frame)
                self.current_frame = ImageTk.PhotoImage(image=img)
                
                # Display on canvas
                self.canvas.delete("all")
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                self.canvas.create_image(x, y, anchor=tk.NW, image=self.current_frame)
                
        except Exception as e:
            print(f"Error displaying frame: {e}")
    
    def toggle_play(self):
        """Toggle video playback"""
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="▶ Play")
        else:
            self.is_playing = True
            self.play_button.config(text="⏸ Pause")
            self.play_video()
    
    def play_video(self):
        """Play video frames"""
        if not self.is_playing or not self.cap:
            return
        
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_delay = int(1000 / fps)
        
        ret, frame = self.cap.read()
        
        if ret:
            self.current_time = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            
            # Display frame
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
            
            # Update timeline and time label
            self.timeline.set(self.current_time)
            self.update_time_label()
            
            # Schedule next frame
            self.root.after(frame_delay, self.play_video)
        else:
            # Video ended
            self.is_playing = False
            self.play_button.config(text="▶ Play")
            self.current_time = 0
            self.cap.set(cv2.CAP_PROP_POS_MSEC, 0)
    
    def on_timeline_change(self, value):
        """Handle timeline slider change"""
        if not self.is_playing:
            time_sec = float(value)
            self.current_time = time_sec
            self.display_frame_at_time(time_sec)
            self.update_time_label()
    
    def update_time_label(self):
        """Update the time display label"""
        current_min = int(self.current_time // 60)
        current_sec = self.current_time % 60
        
        total_min = int(self.video_duration // 60)
        total_sec = self.video_duration % 60
        
        self.time_label.config(text=f"{current_min:02d}:{current_sec:05.2f} / {total_min:02d}:{total_sec:05.2f}")
    
    def set_start_to_current(self):
        """Set start time to current playback position"""
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, f"{self.current_time:.2f}")
    
    def set_end_to_current(self):
        """Set end time to current playback position"""
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, f"{self.current_time:.2f}")
    
    def trim_video(self):
        """Trim the video based on start and end times"""
        if not self.clip:
            messagebox.showwarning("Warning", "Please select a video first!")
            return
        
        try:
            # Get trim times
            start_time = float(self.start_entry.get())
            end_time = float(self.end_entry.get())
            output_name = self.output_entry.get()
            
            # Validate inputs
            if start_time < 0 or end_time > self.video_duration:
                messagebox.showerror("Error", "Trim times are out of video duration range!")
                return
            
            if start_time >= end_time:
                messagebox.showerror("Error", "Start time must be less than end time!")
                return
            
            if not output_name:
                messagebox.showerror("Error", "Please enter an output filename!")
                return
            
            # Get output path (same directory as input)
            output_dir = os.path.dirname(self.video_path)
            output_path = os.path.join(output_dir, output_name)
            
            # Disable button during processing
            self.trim_button.config(state=tk.DISABLED)
            self.progress_label.config(text="Trimming video... This may take a while.")
            
            # Run trimming in a separate thread to keep UI responsive
            thread = threading.Thread(target=self.process_trim, args=(start_time, end_time, output_path))
            thread.start()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for start and end times!")
            self.trim_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.trim_button.config(state=tk.NORMAL)
    
    def process_trim(self, start_time, end_time, output_path):
        """Process the video trimming in a separate thread"""
        try:
            # Create trimmed clip
            trimmed_clip = self.clip.subclip(start_time, end_time)
            
            # Write to file
            trimmed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
            
            # Close clips
            trimmed_clip.close()
            
            # Update UI on main thread
            self.root.after(0, self.trim_complete, output_path)
            
        except Exception as e:
            self.root.after(0, self.trim_error, str(e))
    
    def trim_complete(self, output_path):
        """Called when trimming is complete"""
        self.progress_label.config(text=f"Video trimmed successfully!")
        messagebox.showinfo("Success", f"Video saved to:\n{output_path}")
        self.trim_button.config(state=tk.NORMAL)
    
    def trim_error(self, error_msg):
        """Called when trimming fails"""
        self.progress_label.config(text="Trimming failed!")
        messagebox.showerror("Error", f"Failed to trim video:\n{error_msg}")
        self.trim_button.config(state=tk.NORMAL)
    
    def cleanup(self):
        """Clean up resources when closing"""
        self.is_playing = False
        if self.cap:
            self.cap.release()
        if self.clip:
            self.clip.close()