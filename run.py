# run.py
from src.video_trimmer import VideoTrimmer
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoTrimmer(root)
    
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()