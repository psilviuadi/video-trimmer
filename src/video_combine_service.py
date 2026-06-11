import os
import moviepy

VideoFileClip = getattr(moviepy, 'VideoFileClip', None)
concatenate_videoclips = getattr(moviepy, 'concatenate_videoclips', None)


def _fade_clip(clip, fade_duration=1.0):
    """Apply a fade in and fade out effect to a clip."""
    try:
        if hasattr(moviepy.video.fx, 'FadeIn') and hasattr(moviepy.video.fx, 'FadeOut'):
            clip = moviepy.video.fx.FadeIn(fade_duration).apply(clip)
            clip = moviepy.video.fx.FadeOut(fade_duration).apply(clip)
            return clip
    except Exception:
        pass

    try:
        from moviepy.video.fx.all import fadein, fadeout
        clip = fadein(clip, fade_duration)
        clip = fadeout(clip, fade_duration)
    except Exception:
        pass
    return clip


def _find_combine_output_name(directory):
    """Return an available output filename in the current folder."""
    folder_name = os.path.basename(directory)
    parent_name = os.path.basename(os.path.dirname(directory))
    if parent_name:
        base_name = f"{parent_name} - {folder_name}"
    else:
        base_name = folder_name

    candidate = f"{base_name}.mp4"
    return candidate


def _safe_close_clip(clip):
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


def combine_numbered_clips(directory, output_path=None, fade_duration=1.0, logger=None):
    """Combine numbered MP4 clips in a folder into a single video."""
    clips = []
    index = 1

    while True:
        file_name = f"{index}.mp4"
        clip_path = os.path.join(directory, file_name)
        if not os.path.exists(clip_path):
            break

        clip = VideoFileClip(clip_path)
        clip = _fade_clip(clip, fade_duration=fade_duration)
        clips.append(clip)
        index += 1

    if not clips:
        raise RuntimeError("No numbered mp4 files found in the current folder.")

    combined = concatenate_videoclips(clips)
    if output_path:
        output_path = os.path.abspath(output_path)
    else:
        output_path = os.path.join(directory, _find_combine_output_name(directory))
    combined.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=logger)

    try:
        _safe_close_clip(combined)
    except Exception:
        pass

    for clip in clips:
        try:
            _safe_close_clip(clip)
        except Exception:
            pass

    return output_path
