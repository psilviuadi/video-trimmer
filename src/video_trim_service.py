import moviepy

try:
    from moviepy.editor import VideoFileClip
except Exception:
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
    except Exception:
        VideoFileClip = getattr(moviepy, 'VideoFileClip', None)
        if VideoFileClip is None:
            raise


def _safe_close_clip(clip):
    """Attempt to close a MoviePy clip robustly across versions."""
    if not clip:
        return
    try:
        clip.close()
    except Exception:
        try:
            if hasattr(clip, "reader") and clip.reader is not None:
                try:
                    clip.reader.close()
                except Exception:
                    pass
            if hasattr(clip, "audio") and clip.audio is not None and hasattr(clip.audio, "reader"):
                try:
                    if hasattr(clip.audio.reader, "close_proc"):
                        clip.audio.reader.close_proc()
                    else:
                        clip.audio.reader.close()
                except Exception:
                    pass
        except Exception:
            pass


def _make_subclip(clip, start, end):
    """Return a subclip between start and end, compatible across MoviePy versions."""
    if hasattr(clip, "subclip"):
        return clip.subclip(start, end)
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start, end)
    try:
        return clip[start:end]
    except Exception:
        pass
    try:
        new_clip = clip.time_transform(lambda t: t + start, apply_to=[])
        if end is None:
            return new_clip
        new_clip.duration = end - start
        new_clip.end = new_clip.start + new_clip.duration
        return new_clip
    except Exception:
        raise RuntimeError("Unable to create subclip with installed MoviePy version")


def trim_video(input_path, start_time, end_time, output_path, codec="libx264", audio_codec="aac", logger=None):
    """Trim a video file between start_time and end_time and write it to output_path."""
    clip = None
    trimmed_clip = None
    try:
        clip = VideoFileClip(input_path)
        trimmed_clip = _make_subclip(clip, start_time, end_time)
        trimmed_clip.write_videofile(output_path, codec=codec, audio_codec=audio_codec, logger=logger)
        return output_path
    finally:
        try:
            if trimmed_clip is not None:
                _safe_close_clip(trimmed_clip)
        except Exception:
            pass
        try:
            if clip is not None:
                _safe_close_clip(clip)
        except Exception:
            pass
